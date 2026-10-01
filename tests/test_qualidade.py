"""Verificações de qualidade sobre o DW sintético e sobre tabelas montadas para quebrar."""
import duckdb
import pytest

from dw_sme.carga import carregar
from dw_sme.config import Configuracao
from dw_sme.qualidade import verificacoes as q


@pytest.fixture
def dw(dados_sinteticos, tmp_path):
    cfg = Configuracao(dir_dados=dados_sinteticos, banco=tmp_path / "dw_q.duckdb", log=lambda *_: None)
    resumo = carregar.carregar_tudo(cfg)
    con = duckdb.connect(str(cfg.banco), read_only=True)
    yield con, resumo
    con.close()


def test_nenhuma_falha_no_dw_sintetico(dw):
    con, resumo = dw
    resultado = q.verificar(con, resumo["fila_metadados"])
    assert [v.codigo for v in resultado] == [f"Q{i:02d}" for i in range(1, 11)]
    assert all(v.status in (q.OK, q.ALERTA) for v in resultado)
    por_codigo = {v.codigo: v for v in resultado}
    assert por_codigo["Q01"].status == q.OK
    assert por_codigo["Q02"].status == q.OK
    assert por_codigo["Q03"].status == q.OK


def test_observacoes_dos_anos_viram_alerta(dw):
    con, _ = dw
    v = q.observacoes_ano(con)
    assert v.status == q.ALERTA and "2 de 3" in v.resumo     # 2021 e 2023 têm ressalvas


def test_integridade_detecta_chave_orfa():
    con = duckdb.connect()
    con.execute("create schema dw")
    con.execute("create table dw.dim_x(chave_x int)")
    con.execute("create table dw.fato_y(chave_x int)")
    con.execute("insert into dw.dim_x values (1)")
    con.execute("insert into dw.fato_y values (1), (2), (2)")
    v = q.integridade(con, {"fato_y": [("chave_x", "dim_x", "chave_x")]})
    assert v.status == q.FALHA and "2 linhas órfãs" in v.resumo


def test_divergencias_da_planilha_viram_alerta():
    meta = [{"periodo": "2023-06-01", "arquivo": "a.csv", "divergencias_total": ["x", "y"], "inconsistencias": ["z"]},
            {"periodo": "2023-08-01", "arquivo": "b.csv", "divergencias_total": [], "inconsistencias": []}]
    assert q.totais_publicados(meta).status == q.ALERTA
    assert q.total_e_partes(meta).status == q.ALERTA
    assert q.totais_publicados([meta[1]]).status == q.OK


def test_relatorio_markdown(dw):
    con, resumo = dw
    texto = q.relatorio_markdown(q.verificar(con, resumo["fila_metadados"]), resumo)
    assert texto.startswith("# Relatório de qualidade")
    assert "## Q01 · Integridade referencial · OK" in texto
    assert "| fato_matricula |" in texto or "| fato |" in texto


@pytest.mark.parametrize("valor, esperado", [
    (1234567, "1.234.567"), (0.1234, "0.1234"), (None, ""), ("a|b", "a/b"), (True, "True"),
])
def test_formatacao_das_celulas(valor, esperado):
    assert q._formatar(valor) == esperado
