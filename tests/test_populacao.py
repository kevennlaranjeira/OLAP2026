"""População do Censo 2022: leitura dos Agregados por Setores e download do diretório do IBGE."""
import pytest

from dw_sme.extracao import ibge
from dw_sme.transformacao import populacao as pop

from conftest import IBGE_DEMOGRAFIA, POPULACAO_0_4, gravar_ibge, zip_em_memoria
from test_extracao import ServidorFalso


@pytest.fixture
def pasta(tmp_path):
    gravar_ibge(tmp_path / "ibge")
    return tmp_path / "ibge"


def test_variaveis_seguem_as_faixas_da_dimensao_idade():
    assert pop.VARIAVEIS_FAIXA[0] == ("V01031", "0 A 4 ANOS", 0, 4)
    assert pop.VARIAVEIS_FAIXA[-1] == ("V01041", "70 ANOS OU MAIS", 70, None)
    assert len(pop.VARIAVEIS_FAIXA) == 11


@pytest.mark.parametrize("valor, esperado", [
    ("355030801000001", "355030801000001"),
    ("355030801000001P", "355030801000001"),     # sufixo de letra ignorado
    (" 3550308.01.00001 ", None),                 # 14 dígitos: inválido
    (None, None),
])
def test_codigo_do_setor(valor, esperado):
    assert pop.codigo_setor(valor) == esperado


@pytest.mark.parametrize("valor, esperado", [("12", 12), (" 0 ", 0), ("X", None), ("", None), ("1.5", None), (None, None)])
def test_contagem(valor, esperado):
    assert pop.contagem(valor) == esperado


def test_localiza_os_dois_temas(pasta):
    achados = pop.localizar(pasta)
    assert achados["basico"].name == "Agregados_por_setores_basico_BR.zip"
    assert achados["demografia"].name == "Agregados_por_setores_demografia_BR.csv"
    assert pop.localizar(pasta / "nao-existe") == {}


def test_le_so_o_municipio_e_liga_o_setor_ao_distrito(pasta):
    p = pop.ler(pasta)
    assert len(p.setores) == 6                                   # Adamantina fica fora
    distritos = dict(zip(p.setores["cd_setor"], p.setores["distrito"], strict=True))
    assert distritos["355030801000001"] == "AGUA RASA"           # acento e caixa normalizados
    assert distritos["355030801000003"] == "AGUA RASA"           # ausente do Básico: herda do distrito IBGE
    assert distritos["355030899000001"] == "DISTRITO SINTETICO"
    zero_a_quatro = p.pessoas[p.pessoas.faixa_ibge == "0 A 4 ANOS"].merge(p.setores, on="cd_setor")
    soma = zero_a_quatro.groupby("distrito")["qtd_pessoas"].sum().to_dict()
    assert {d: soma[d] for d in POPULACAO_0_4} == POPULACAO_0_4
    assert p.meta["valores_nao_numericos"] == 1
    assert p.meta["pessoas"] == sum(sum(v for v in vs if v != "X")
                                    for s, vs in IBGE_DEMOGRAFIA.items() if s.startswith("3550308"))


def test_sem_os_dois_temas_nao_le_nada(pasta):
    (pasta / "Agregados_por_setores_basico_BR.zip").unlink()
    assert pop.ler(pasta) is None


def test_coluna_ausente_interrompe_a_leitura(pasta):
    (pasta / "Agregados_por_setores_demografia_BR.csv").write_text("CD_SETOR;V01031\n355030801000001;3\n",
                                                                     encoding="utf-8")
    with pytest.raises(ValueError, match="colunas esperadas ausentes"):
        pop.ler(pasta)


def test_layout_com_valores_nao_numericos_interrompe_a_leitura(pasta):
    variaveis = ";".join(v for v, *_ in pop.VARIAVEIS_FAIXA)
    linhas = [f"CD_SETOR;{variaveis}"] + [f"35503080100000{i};" + ";".join(["1,5"] * 11) for i in range(1, 4)]
    (pasta / "Agregados_por_setores_demografia_BR.csv").write_text("\n".join(linhas), encoding="utf-8")
    with pytest.raises(ValueError, match="não é o documentado"):
        pop.ler(pasta)


def test_setor_repetido_interrompe_a_leitura(pasta):
    arquivo = pasta / "Agregados_por_setores_demografia_BR.csv"
    linhas = arquivo.read_text(encoding="utf-8").splitlines()
    arquivo.write_text("\n".join([*linhas, linhas[1]]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="setor censitário repetido"):
        pop.ler(pasta)


def test_zip_sem_csv_e_recusado(pasta):
    (pasta / "Agregados_por_setores_basico_BR.zip").write_bytes(zip_em_memoria({"leia-me.txt": b"x"}))
    with pytest.raises(ValueError, match="nenhum CSV"):
        pop.ler(pasta)


# ----------------------------------------------------------------------------- download

BASE = "https://ibge.exemplo/Agregados/"


def test_links_ficam_abaixo_da_base():
    html = '<a href="../">p</a><a href="?C=M">o</a><a href="sub/">s</a><a href="a.zip">a</a><a href="sub/">s</a>'
    assert ibge.links(html, BASE) == [BASE + "sub/", BASE + "a.zip"]


def test_escolhe_csv_e_a_versao_mais_recente():
    arquivos = [BASE + "xlsx/Agregados_por_setores_demografia_BR.xlsx",
                BASE + "csv/Agregados_por_setores_demografia_BR_20240101.zip",
                BASE + "csv/Agregados_por_setores_demografia_BR_20250417.zip",
                BASE + "csv/Agregados_por_setores_basico_BR.csv",
                BASE + "csv/Leia-me.txt"]
    assert ibge.escolher(arquivos) == {"basico": BASE + "csv/Agregados_por_setores_basico_BR.csv",
                                       "demografia": BASE + "csv/Agregados_por_setores_demografia_BR_20250417.zip"}


def test_arquivo_de_dados_ganha_de_dicionario_com_o_tema_no_nome():
    arquivos = [BASE + "doc/dicionario_demografia_basico.csv",
                BASE + "csv/Agregados_por_setores_demografia_BR.zip",
                BASE + "csv/Agregados_por_setores_basico_BR.zip"]
    assert ibge.escolher(arquivos) == {"basico": BASE + "csv/Agregados_por_setores_basico_BR.zip",
                                       "demografia": BASE + "csv/Agregados_por_setores_demografia_BR.zip"}


def test_baixa_os_dois_temas_com_manifesto(tmp_path):
    rotas = {BASE: b'<a href="csv/">c</a>',
             BASE + "csv/": b'<a href="Agregados_por_setores_basico_BR.zip">b</a>'
                            b'<a href="Agregados_por_setores_demografia_BR.zip">d</a>',
             BASE + "csv/Agregados_por_setores_basico_BR.zip": b"b",
             BASE + "csv/Agregados_por_setores_demografia_BR.zip": b"d"}
    srv = ServidorFalso(rotas)
    baixados = ibge.baixar(tmp_path, "teste", abrir=srv, base=BASE)
    assert {t: p.read_bytes() for t, p in baixados.items()} == {"basico": b"b", "demografia": b"d"}
    assert (tmp_path / "manifesto.json").exists()
    pedidos = len(srv.pedidos)
    ibge.baixar(tmp_path, "teste", abrir=srv, base=BASE)          # segunda vez: só a listagem
    assert len(srv.pedidos) - pedidos == 2


def test_subpasta_inacessivel_nao_interrompe_a_busca():
    rotas = {BASE: b'<a href="quebrada/">q</a><a href="csv/">c</a>',
             BASE + "csv/": b'<a href="Agregados_por_setores_basico_BR.zip">b</a>'
                            b'<a href="Agregados_por_setores_demografia_BR.zip">d</a>'}
    achados = ibge.localizar(BASE, "teste", abrir=ServidorFalso(rotas))
    assert set(achados) == {"basico", "demografia"}


def test_listagem_sem_os_temas_e_erro(tmp_path):
    srv = ServidorFalso({BASE: b'<a href="outro.zip">o</a>'})
    with pytest.raises(FileNotFoundError, match="demografia"):
        ibge.baixar(tmp_path, "teste", abrir=srv, base=BASE)


def test_erro_404_nao_e_repetido():
    srv = ServidorFalso({})
    with pytest.raises(OSError):
        ibge.localizar(BASE, "teste", abrir=srv)
    assert len(srv.pedidos) == 1


def test_falha_de_rede_e_repetida(monkeypatch):
    monkeypatch.setattr(ibge.time, "sleep", lambda _s: None)
    srv = ServidorFalso({BASE: b""}, falhas=2)
    assert ibge.localizar(BASE, "teste", abrir=srv) == {}
    assert len(srv.pedidos) == 3


class ServidorInstavel:
    """Responde 503 nas primeiras chamadas e depois serve as rotas."""

    def __init__(self, rotas, erros_5xx):
        self.rotas, self.erros, self.pedidos = rotas, erros_5xx, []

    def __call__(self, req, timeout=None):
        import urllib.error

        from test_extracao import RespostaFalsa
        self.pedidos.append(req.full_url)
        if self.erros:
            self.erros -= 1
            raise urllib.error.HTTPError(req.full_url, 503, "Service Unavailable", hdrs=None, fp=None)
        return RespostaFalsa(self.rotas[req.full_url])


def test_erro_5xx_do_servidor_e_repetido(monkeypatch):
    monkeypatch.setattr(ibge.time, "sleep", lambda _s: None)
    srv = ServidorInstavel({BASE: b'<a href="Agregados_por_setores_basico_BR.zip">b</a>'}, erros_5xx=2)
    assert set(ibge.localizar(BASE, "teste", abrir=srv)) == {"basico"}
    assert len(srv.pedidos) == 3


def test_erro_5xx_persistente_desiste(monkeypatch):
    monkeypatch.setattr(ibge.time, "sleep", lambda _s: None)
    srv = ServidorInstavel({}, erros_5xx=9)
    with pytest.raises(OSError):
        ibge.localizar(BASE, "teste", abrir=srv)
    assert len(srv.pedidos) == 3


def test_subpasta_vista_duas_vezes_e_lida_uma_vez_e_profundidade_limitada():
    rotas = {BASE: b'<a href="x/">x</a><a href="x/y/">y</a><a href="a/">a</a>',
             BASE + "x/": b'<a href="y/">y</a>',                        # x/y/ aparece de novo, no nível 2
             BASE + "x/y/": b'<a href="Agregados_por_setores_basico_BR.zip">b</a>',
             BASE + "a/": b'<a href="b/">b</a>',
             BASE + "a/b/": b'<a href="c/">c</a>',
             BASE + "a/b/c/": b'<a href="Agregados_por_setores_demografia_BR.zip">d</a>'}   # nível 3
    srv = ServidorFalso(rotas)
    achados = ibge.localizar(BASE, "teste", abrir=srv, profundidade=2)
    assert set(achados) == {"basico"}
    lidas = [p.full_url for p in srv.pedidos]
    assert lidas.count(BASE + "x/y/") == 1 and BASE + "a/b/c/" not in lidas
