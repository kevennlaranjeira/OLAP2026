"""Pipeline inteiro, do download às consultas, contra um portal falso em memória.

O portal serve um pacote .zip com o microdado sintético de 2019 (no formato
de 2015-2018: separador '|', latin-1, atividade complementar no mesmo
arquivo), uma nota técnica e um arquivo de atividades complementares, além
das planilhas de fila de exemplo. Nada depende de internet.
"""
import io
import json
import zipfile
from pathlib import Path

import pytest

from conftest import FIXTURES, microdado_2019
from dw_sme import pipeline
from dw_sme.config import Configuracao
from dw_sme.qualidade.verificacoes import FALHA
from test_extracao import ServidorFalso, pacote

BASE = "https://portal.exemplo/api/3/action"


def _zip_microdado() -> bytes:
    csv = microdado_2019().to_csv(sep="|", index=False, encoding="latin-1")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("Microdados_EOL_Matriculas_Ano_2019.csv", csv.encode("latin-1"))
        z.writestr("Microdados_EOL_Matricula_Atividades_Complementares.csv", b"AN_LETIVO|X\n2019|1\n")
        z.writestr("NOTA TECNICA.txt", b"nota")
    return buffer.getvalue()


@pytest.fixture
def portal():
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
    rotas[f"{BASE}/package_show?id=microdados-matriculas"] = pacote(recursos_micro)
    rotas[f"{BASE}/package_show?id=demanda-e-matriculas"] = pacote(recursos_fila)
    return ServidorFalso(rotas)


def test_pipeline_completo_sem_internet(tmp_path, portal):
    cfg = Configuracao(dir_dados=tmp_path / "data", ckan_base=BASE, sete_zip=None, log=lambda *_: None)
    resultado = pipeline.executar_tudo(cfg, abrir=portal)

    # baixar: só o pacote do recorte; o de 2000-2005 fica de fora
    assert resultado["baixar"] == {"microdados": 1, "demanda": 7, "dicionarios": 0}
    assert not (cfg.dir_raw_microdados / "antigo.zip").exists()

    # preparar: só o arquivo de escolarização vira Parquet
    brutos = sorted(p.name for p in cfg.dir_bruto.rglob("*.parquet"))
    assert brutos == ["Microdados_EOL_Matriculas_Ano_2019.parquet"]
    meta = json.loads((cfg.dir_bruto / "_preparacao.json").read_text(encoding="utf-8"))
    assert meta[0]["separador"] == "|" and meta[0]["linhas"] == 4 and meta[0]["rejeitadas"] == 0

    # carregar: a atividade complementar (TURMA_ESCOL = N) não entra
    assert resultado["carregar"]["fato_matricula"] == 3

    # verificar e consultar
    assert FALHA not in resultado["verificar"].values()
    assert set(resultado["consultar"]) == {"C1", "C2", "C3", "C4", "C5", "C6"}
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
