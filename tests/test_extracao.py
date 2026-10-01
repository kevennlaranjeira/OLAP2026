"""Extração: cliente CKAN, manifesto de downloads, seleção pelo recorte e pacotes."""
import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from dw_sme.extracao import arquivos, ckan, fontes

BASE = "https://dados.exemplo/api/3/action"


class RespostaFalsa:
    def __init__(self, corpo: bytes):
        self._corpo, self._pos = corpo, 0

    def read(self, n: int = -1):
        fim = len(self._corpo) if n is None or n < 0 else self._pos + n
        pedaco, self._pos = self._corpo[self._pos:fim], min(fim, len(self._corpo))
        return pedaco

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class ServidorFalso:
    """Substitui urllib.request.urlopen; registra cada requisição feita."""

    def __init__(self, rotas: dict[str, bytes], falhas: int = 0):
        self.rotas, self.falhas, self.pedidos = rotas, falhas, []

    def __call__(self, req, timeout=None):
        self.pedidos.append(req)
        if self.falhas:
            self.falhas -= 1
            raise OSError("conexão recusada")
        return RespostaFalsa(self.rotas[req.full_url])


def pacote(recursos):
    return json.dumps({"success": True, "result": {"name": "x", "resources": recursos}}).encode()


RECURSOS = [
    {"id": "r1", "name": "Demanda e Matrículas - Jun/2026", "format": "CSV", "url": "https://d/x/jun-2026.csv", "size": 10},
    {"id": "r2", "name": "Demanda e Matrículas - Dez/2024", "format": "CSV", "url": "https://d/x/dez-2024.csv", "size": 10},
    {"id": "r3", "name": "Demanda e Matrículas - Dez/2024", "format": "XLS", "url": "https://d/x/dez-2024.xls", "size": 10},
    {"id": "r4", "name": "Demanda por Vagas - 2006 a 2017", "format": "CSV", "url": "https://d/x/evolucao.csv", "size": 10},
    {"id": "r5", "name": "Dicionário - Demanda e Matrículas", "format": "CSV", "url": "https://d/x/dic.csv", "size": 10},
    {"id": "m1", "name": "Microdados de Matrículas - 2015-2018", "format": "ZIP", "url": "https://d/x/m1518.zip", "size": 10},
    {"id": "m2", "name": "Microdados de Matrículas - 2019-2021", "format": "ZIP", "url": "https://d/x/m1921.rar", "size": 10},
    {"id": "m3", "name": "Microdados de Matrícula - 2025", "format": ".zip", "url": "https://d/x/m2025.zip", "size": 10},
    {"id": "m4", "name": "Microdados de Matrículas - 2000-2005", "format": "ZIP", "url": "https://d/x/m0005.zip", "size": 10},
    {"id": "m5", "name": "Leia-me", "format": "PDF", "url": "https://d/x/leia.pdf", "size": 10},
]


# ------------------------------------------------------------------ CKAN

def test_lista_recursos_com_user_agent():
    srv = ServidorFalso({f"{BASE}/package_show?id=demanda": pacote(RECURSOS)})
    cliente = ckan.ClienteCKAN(BASE, user_agent="dw-sme/teste", abrir=srv)
    recursos = cliente.recursos("demanda")
    assert [r.id for r in recursos] == [r["id"] for r in RECURSOS]
    assert recursos[5].formato == "ZIP" and recursos[7].formato == "ZIP"   # '.zip' normalizado
    assert srv.pedidos[0].get_header("User-agent") == "dw-sme/teste"


def test_tenta_de_novo_quando_a_rede_falha():
    srv = ServidorFalso({f"{BASE}/package_show?id=demanda": pacote(RECURSOS)}, falhas=2)
    cliente = ckan.ClienteCKAN(BASE, user_agent="x", abrir=srv, tentativas=3, pausa=0)
    assert len(cliente.recursos("demanda")) == len(RECURSOS)


def test_desiste_depois_das_tentativas():
    srv = ServidorFalso({}, falhas=5)
    cliente = ckan.ClienteCKAN(BASE, user_agent="x", abrir=srv, tentativas=2, pausa=0)
    with pytest.raises(OSError):
        cliente.recursos("demanda")


def test_resposta_sem_sucesso_e_erro():
    srv = ServidorFalso({f"{BASE}/package_show?id=x": json.dumps({"success": False}).encode()})
    with pytest.raises(RuntimeError):
        ckan.ClienteCKAN(BASE, user_agent="x", abrir=srv).recursos("x")


# ------------------------------------------------------------------ download e manifesto

def test_download_registra_hash_e_nao_baixa_de_novo(tmp_path):
    conteudo = b"AGUA RASA;1;2\n"
    srv = ServidorFalso({"https://d/x/jun-2026.csv": conteudo})
    rec = ckan.Recurso(id="r1", nome="Demanda - Jun/2026", formato="CSV", url="https://d/x/jun-2026.csv", tamanho=None)
    manifesto = ckan.Manifesto(tmp_path / "manifesto.json")
    caminho = ckan.baixar(rec, tmp_path / "raw", manifesto, user_agent="x", abrir=srv)
    assert caminho.read_bytes() == conteudo
    entrada = json.loads((tmp_path / "manifesto.json").read_text(encoding="utf-8"))["jun-2026.csv"]
    assert entrada["sha256"] == hashlib.sha256(conteudo).hexdigest()
    assert entrada["bytes"] == len(conteudo) and entrada["recurso_id"] == "r1"
    # segunda chamada usa o cache
    ckan.baixar(rec, tmp_path / "raw", ckan.Manifesto(tmp_path / "manifesto.json"), user_agent="x", abrir=srv)
    assert len(srv.pedidos) == 1


def test_arquivo_alterado_em_disco_e_baixado_de_novo(tmp_path):
    srv = ServidorFalso({"https://d/x/a.csv": b"original"})
    rec = ckan.Recurso(id="r", nome="a", formato="CSV", url="https://d/x/a.csv", tamanho=None)
    manifesto = ckan.Manifesto(tmp_path / "m.json")
    caminho = ckan.baixar(rec, tmp_path, manifesto, user_agent="x", abrir=srv)
    caminho.write_bytes(b"corrompido")
    ckan.baixar(rec, tmp_path, manifesto, user_agent="x", abrir=srv)
    assert caminho.read_bytes() == b"original" and len(srv.pedidos) == 2


def test_verificar_aponta_arquivo_divergente(tmp_path):
    srv = ServidorFalso({"https://d/x/a.csv": b"original"})
    rec = ckan.Recurso(id="r", nome="a", formato="CSV", url="https://d/x/a.csv", tamanho=None)
    manifesto = ckan.Manifesto(tmp_path / "m.json")
    caminho = ckan.baixar(rec, tmp_path, manifesto, user_agent="x", abrir=srv)
    assert manifesto.verificar(tmp_path) == []
    caminho.write_bytes(b"x")
    assert manifesto.verificar(tmp_path) == ["a.csv"]


# ------------------------------------------------------------------ seleção pelo recorte

@pytest.mark.parametrize("nome, anos", [
    ("Microdados de Matrículas - 2015-2018", {2015, 2016, 2017, 2018}),
    ("Microdados de Matrícula - 2025", {2025}),
    ("Demanda e Matrículas - Jun/2026", {2026}),
    ("Demanda por Vagas - 2006 a 2017", set(range(2006, 2018))),
    ("Leia-me", set()),
])
def test_anos_do_recurso(nome, anos):
    assert fontes.anos_do_nome(nome) == anos


def test_selecao_da_fila_pelo_recorte():
    recursos = [ckan.Recurso.de_ckan(r) for r in RECURSOS]
    sel = fontes.selecionar_fila(recursos, range(2015, 2025))
    assert [r.id for r in sel] == ["r2", "r4"]   # só CSV, dentro do recorte; série histórica incluída


def test_selecao_dos_microdados_pelo_recorte():
    recursos = [ckan.Recurso.de_ckan(r) for r in RECURSOS]
    sel = fontes.selecionar_microdados(recursos, range(2015, 2025))
    assert [r.id for r in sel] == ["m1", "m2"]


# ------------------------------------------------------------------ pacotes

def _zip_com(tmp_path, membros: dict[str, bytes]) -> Path:
    caminho = tmp_path / "pacote.zip"
    with zipfile.ZipFile(caminho, "w") as z:
        for nome, conteudo in membros.items():
            z.writestr(nome, conteudo)
    return caminho


def test_lista_e_extrai_zip_sem_7zip(tmp_path):
    pacote_zip = _zip_com(tmp_path, {"pasta/Microdados_2024.csv": b"A;B\n1;2\n", "NOTA.txt": b"x"})
    membros = arquivos.listar(pacote_zip, sete_zip=None)
    assert sorted(membros) == ["NOTA.txt", "pasta/Microdados_2024.csv"]
    destino = arquivos.extrair(pacote_zip, "pasta/Microdados_2024.csv", tmp_path / "ext", sete_zip=None)
    assert destino.name == "Microdados_2024.csv" and destino.read_bytes() == b"A;B\n1;2\n"


def test_rar_sem_7zip_falha_com_mensagem_clara(tmp_path):
    falso = tmp_path / "x.rar"
    falso.write_bytes(b"Rar!")
    with pytest.raises(RuntimeError, match="7-Zip"):
        arquivos.listar(falso, sete_zip=None)


@pytest.mark.skipif(arquivos.localizar_7zip() is None, reason="7-Zip não instalado")
def test_extrai_zip_com_7zip(tmp_path):
    pacote_zip = _zip_com(tmp_path, {"Microdados_2024.csv": b"A;B\n1;2\n"})
    sete = arquivos.localizar_7zip()
    assert arquivos.listar(pacote_zip, sete_zip=sete) == ["Microdados_2024.csv"]
    destino = arquivos.extrair(pacote_zip, "Microdados_2024.csv", tmp_path / "ext", sete_zip=sete)
    assert destino.read_bytes() == b"A;B\n1;2\n"


@pytest.mark.parametrize("conteudo, esperado", [
    ("ÁGUA;1\n".encode("utf-8"), "utf-8"),
    ("ÁGUA;1\n".encode("latin-1"), "latin-1"),
    (b"\xef\xbb\xbfAN_LETIVO;X\n", "utf-8"),
])
def test_detectar_encoding(tmp_path, conteudo, esperado):
    f = tmp_path / "a.csv"
    f.write_bytes(conteudo)
    assert arquivos.detectar_encoding(f) == esperado


@pytest.mark.parametrize("cabecalho, sep", [
    ("AN_LETIVO|CD_UNIDADE|NOME", "|"), ("AN_LETIVO;CD;NOME", ";"), ("A,B,C", ","),
])
def test_detectar_separador(tmp_path, cabecalho, sep):
    f = tmp_path / "a.csv"
    f.write_text(cabecalho + "\n1\n", encoding="utf-8")
    assert arquivos.detectar_separador(f) == sep


@pytest.mark.parametrize("membro, esperado", [
    ("Microdados_EOL_Matriculas_Ano_2015.csv", 2015),
    ("microdados-de-matricula-2024/Microdados_Matricula_EOL_Escolarizacao_Outros_2024.csv", 2024),
    ("Microdados_EOL_Matriculas_Ano_2021.txt", 2021),
    ("Microdados_EOL_Matriculas_Ano_2022_Atividades_Complementares.csv", None),
    ("Microdados_EOL_Matricula_Atividades_Complementares.csv", None),
    ("NOTA TÉCNICA.txt", None),
])
def test_membro_de_escolarizacao(membro, esperado):
    assert fontes.ano_do_membro_escolarizacao(membro) == esperado
