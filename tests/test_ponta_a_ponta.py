"""Pipeline inteiro, do download às consultas, contra um portal falso em memória.

O portal serve um pacote .zip com o microdado sintético de 2019 (no formato
de 2015-2018: separador '|', latin-1, atividade complementar no mesmo
arquivo), uma nota técnica e um arquivo de atividades complementares, além
das planilhas de fila de exemplo. Um diretório falso do IBGE serve os temas
Básico e Demografia do Censo 2022 sintético. Nada depende de internet.
"""
import io
import json
import zipfile

import pytest

from dw_sme import pipeline
from dw_sme.config import Configuracao
from dw_sme.qualidade.verificacoes import FALHA

from conftest import FIXTURES, gravar_ibge, microdado_2019, zip_em_memoria
from test_extracao import ServidorFalso, pacote

BASE = "https://portal.exemplo/api/3/action"
IBGE = "https://ibge.exemplo/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/"


def rotas_ibge(tmp_path) -> dict[str, bytes]:
    """Listagem de diretório no estilo do servidor do IBGE, com subpastas e um XLSX que não deve ser escolhido."""
    origem = tmp_path / "ibge_origem"
    gravar_ibge(origem)
    csv = IBGE + "Agregados_por_Setor_csv/"
    demografia = (origem / "Agregados_por_setores_demografia_BR.csv").read_bytes()
    return {
        IBGE: b'<a href="../">Parent</a> <a href="?C=N;O=D">Name</a> <a href="Agregados_por_Setor_csv/">csv</a> '
              b'<a href="Agregados_por_Setor_xlsx/">xlsx</a> <a href="Documentacao/">doc</a>',
        csv: b'<a href="Agregados_por_setores_basico_BR.zip">b</a> '
             b'<a href="Agregados_por_setores_demografia_BR.zip">d</a> <a href="Leia-me.txt">l</a>',
        IBGE + "Agregados_por_Setor_xlsx/": b'<a href="Agregados_por_setores_demografia_BR.xlsx">x</a>',
        IBGE + "Documentacao/": b'<a href="dicionario.pdf">p</a>',
        csv + "Agregados_por_setores_basico_BR.zip": (origem / "Agregados_por_setores_basico_BR.zip").read_bytes(),
        csv + "Agregados_por_setores_demografia_BR.zip": zip_em_memoria(
            {"Agregados_por_setores_demografia_BR.csv": demografia}),
    }


def _zip_microdado() -> bytes:
    csv = microdado_2019().to_csv(sep="|", index=False, encoding="latin-1")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("Microdados_EOL_Matriculas_Ano_2019.csv", csv.encode("latin-1"))
        z.writestr("Microdados_EOL_Matricula_Atividades_Complementares.csv", b"AN_LETIVO|X\n2019|1\n")
        z.writestr("NOTA TECNICA.txt", b"nota")
    return buffer.getvalue()


@pytest.fixture
def portal(tmp_path):
    url_zip = "https://portal.exemplo/download/microdados-2019.zip"
    recursos_micro = [
        {"id": "m1", "name": "Microdados de Matrículas - 2019", "format": "ZIP", "url": url_zip, "size": 1},
        {"id": "m0", "name": "Microdados de Matrículas - 2000-2005", "format": "ZIP",
         "url": "https://portal.exemplo/download/antigo.zip", "size": 1},
    ]
    rotas = {url_zip: _zip_microdado()}
    recursos_fila = []
    for i, f in enumerate(sorted((FIXTURES / "fila").glob("*.csv"))):
        url = f"https://portal.exemplo/download/{f.name}"
        nome = "Demanda por Vagas - 2006 a 2017" if f.name == "evolucaodemanda.csv" else f"Demanda - {f.stem}"
        recursos_fila.append({"id": f"f{i}", "name": nome, "format": "CSV", "url": url, "size": 1})
        rotas[url] = f.read_bytes()
    rotas.update(rotas_ibge(tmp_path))
    rotas[f"{BASE}/package_show?id=microdados-matriculas"] = pacote(recursos_micro)
    rotas[f"{BASE}/package_show?id=demanda-e-matriculas"] = pacote(recursos_fila)
    return ServidorFalso(rotas)


def test_pipeline_completo_sem_internet(tmp_path, portal):
    cfg = Configuracao(dir_dados=tmp_path / "data", ckan_base=BASE, ibge_base=IBGE, sete_zip=None,
                       log=lambda *_: None)
    resultado = pipeline.executar_tudo(cfg, abrir=portal)

    # baixar: só o pacote do recorte; o de 2000-2005 fica de fora; do IBGE, os dois temas em CSV
    assert resultado["baixar"] == {"microdados": 1, "demanda": 7, "dicionarios": 0, "ibge": 2}
    assert sorted(p.name for p in cfg.dir_raw_ibge.glob("*.zip")) == [
        "Agregados_por_setores_basico_BR.zip", "Agregados_por_setores_demografia_BR.zip"]
    assert not (cfg.dir_raw_microdados / "antigo.zip").exists()

    # preparar: só o arquivo de escolarização vira Parquet
    brutos = sorted(p.name for p in cfg.dir_bruto.rglob("*.parquet"))
    assert brutos == ["Microdados_EOL_Matriculas_Ano_2019.parquet"]
    meta = json.loads((cfg.dir_bruto / "_preparacao.json").read_text(encoding="utf-8"))
    assert meta[0]["separador"] == "|" and meta[0]["linhas"] == 4 and meta[0]["rejeitadas"] == 0

    # carregar: a atividade complementar (TURMA_ESCOL = N) não entra; a população do Censo entra
    assert resultado["carregar"]["fato_matricula"] == 3
    assert resultado["carregar"]["fato_turma"] == 2
    assert resultado["carregar"]["fato_populacao"] == 6 * 11

    # verificar e consultar
    assert FALHA not in resultado["verificar"].values()
    assert set(resultado["consultar"]) == {f"C{i}" for i in range(1, 9)}
    assert (cfg.dir_relatorios / "qualidade.md").exists()


def test_preparar_de_novo_nao_reconverte(tmp_path, portal):
    cfg = Configuracao(dir_dados=tmp_path / "data", ckan_base=BASE, sete_zip=None, log=lambda *_: None)
    pipeline.baixar(cfg, abrir=portal)
    primeira = pipeline.preparar(cfg)
    segunda = pipeline.preparar(cfg)
    assert [r["situacao"] for r in primeira] == ["convertido"]
    assert [r["situacao"] for r in segunda] == ["existente"]


def test_planilhas_de_fila_com_periodo_repetido_falham(tmp_path):
    from dw_sme.preparacao import preparar_fila
    destino = tmp_path / "data" / "raw" / "demanda"
    destino.mkdir(parents=True)
    original = FIXTURES / "fila" / "publicacao-demanda-e-matricula-abr-2024.csv"
    for nome in ("publicacao-demanda-e-matricula-abr-2024.csv", "copia-demanda-abril-2024.csv"):
        (destino / nome).write_bytes(original.read_bytes())
    with pytest.raises(ValueError, match="mais de uma planilha"):
        preparar_fila(Configuracao(dir_dados=tmp_path / "data", log=lambda *_: None))
