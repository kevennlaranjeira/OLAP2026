"""Linha de comando e orquestração do pipeline, de ponta a ponta sobre dados sintéticos."""
import json

import pytest

from dw_sme import cli, pipeline
from dw_sme.config import Configuracao, intervalo_de_anos


@pytest.mark.parametrize("texto, esperado", [("2015-2024", range(2015, 2025)), ("2019", range(2019, 2020))])
def test_intervalo_de_anos(texto, esperado):
    assert intervalo_de_anos(texto) == esperado


def test_intervalo_invertido_falha():
    with pytest.raises(ValueError):
        intervalo_de_anos("2024-2015")


def test_argumentos():
    args = cli.construir_parser().parse_args(["carregar", "--dados", "x", "--anos", "2019-2021", "--manter-staging"])
    cfg = cli.configuracao(args)
    assert cfg.anos == range(2019, 2022) and cfg.manter_staging
    assert cfg.banco.as_posix().endswith("x/dw/dw_sme.duckdb")


def test_etapa_invalida_e_recusada():
    with pytest.raises(SystemExit):
        cli.construir_parser().parse_args(["apagar"])


def test_carregar_verificar_consultar_pela_linha_de_comando(dados_sinteticos, capsys):
    base = ["--dados", str(dados_sinteticos)]
    assert cli.main(["carregar", *base]) == 0
    assert cli.main(["verificar", *base]) == 0
    assert cli.main(["consultar", *base]) == 0
    relatorios = dados_sinteticos / "relatorios"
    assert (relatorios / "qualidade.md").exists()
    assert json.loads((relatorios / "carga.json").read_text(encoding="utf-8"))["fato_matricula"] == 7
    assert len(list((relatorios / "consultas").glob("*.csv"))) == 6
    saida = capsys.readouterr().out
    assert "Q01 OK" in saida and "C5:" in saida


def test_baixar_usa_o_portal_e_o_recorte(tmp_path):
    from test_extracao import RECURSOS, ServidorFalso, pacote
    base = "https://dados.exemplo/api/3/action"
    rotas = {f"{base}/package_show?id=microdados-matriculas": pacote([r for r in RECURSOS if r["id"].startswith("m")]),
             f"{base}/package_show?id=demanda-e-matriculas": pacote([r for r in RECURSOS if r["id"].startswith("r")])}
    for r in RECURSOS:
        rotas[r["url"]] = f"conteudo de {r['id']}".encode()
    cfg = Configuracao(dir_dados=tmp_path / "data", ckan_base=base, log=lambda *_: None)
    resumo = pipeline.baixar(cfg, abrir=ServidorFalso(rotas))
    assert resumo == {"microdados": 2, "demanda": 2, "dicionarios": 1}
    assert (cfg.dir_raw_microdados / "m1518.zip").read_bytes() == b"conteudo de m1"
    assert (cfg.dir_raw_fila / "manifesto.json").exists()
