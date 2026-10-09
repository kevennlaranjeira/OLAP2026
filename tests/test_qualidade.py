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
    assert [v.codigo for v in resultado] == [f"Q{i:02d}" for i in range(1, 15)]
    assert all(v.status in (q.OK, q.ALERTA) for v in resultado)
    por_codigo = {v.codigo: v for v in resultado}
    assert por_codigo["Q01"].status == q.OK
    assert por_codigo["Q02"].status == q.OK
    assert por_codigo["Q03"].status == q.OK
    assert por_codigo["Q11"].status == q.OK
    assert por_codigo["Q13"].status == q.OK        # hierarquias valem como dependência funcional
    assert por_codigo["Q14"].status == q.ALERTA    # só o 'Distrito Sintético' do Censo de teste
    assert "27 chaves estrangeiras" in por_codigo["Q01"].resumo


def test_ocupacao_conserva_matriculas_e_turmas(dw):
    con, _ = dw
    v = q.ocupacao_turmas(con)
    assert v.status == q.OK
    det = v.detalhe.set_index("ano")
    assert (det["matriculas"] == det["matriculas_no_fato_turma"]).all()
    assert (det["turmas_distintas"] == det["linhas_fato_turma"]).all()


def test_populacao_com_setor_sem_distrito_e_valor_nao_publicado_vira_alerta(dw):
    con, _ = dw
    v = q.populacao(con)
    assert v.status == q.ALERTA
    r = v.detalhe.iloc[0]
    assert r.setores == 6 and r.setores_sem_distrito_da_sme == 1 and r.valores_nao_publicados == 1


def test_populacao_ausente_vira_alerta(tmp_path):
    from conftest import FIXTURES, _gravar, microdado_2019
    dados = tmp_path / "data"
    _gravar(microdado_2019(), dados / "interim" / "bruto" / "ano=2019" / "Microdados_EOL_Matriculas_Ano_2019.parquet")
    (dados / "raw" / "demanda").mkdir(parents=True)
    for f in (FIXTURES / "fila").glob("*.csv"):
        (dados / "raw" / "demanda" / f.name).write_bytes(f.read_bytes())
    cfg = Configuracao(dir_dados=dados, banco=tmp_path / "sem_ibge.duckdb", log=lambda *_: None)
    resumo = carregar.carregar_tudo(cfg)
    assert resumo["populacao"] == {"carregada": False, "motivo": "arquivos ausentes"}
    con = duckdb.connect(str(cfg.banco), read_only=True)
    try:
        v = q.populacao(con)
        assert v.status == q.ALERTA and "não carregada" in v.resumo
        assert con.execute("select count(*) from dw.dim_faixa_etaria").fetchone()[0] == 11
    finally:
        con.close()


def test_fato_de_turma_que_nao_conserva_e_falha():
    con = duckdb.connect()
    con.execute("create schema dw")
    con.execute("create table dw.dim_ano_letivo(chave_ano_letivo int, ano int)")
    con.execute("create table dw.fato_matricula(chave_ano_letivo int, id_turma varchar, qtd_matricula int)")
    con.execute("""create table dw.fato_turma(chave_ano_letivo int, qtd_matriculas int,
                   qtd_matriculas_ativas_junho int, qtd_turmas_ativas_junho int)""")
    con.execute("insert into dw.dim_ano_letivo values (1, 2019)")
    con.execute("insert into dw.fato_matricula values (1, 't1', 1), (1, 't1', 1), (1, 't2', 1)")
    con.execute("insert into dw.fato_turma values (1, 2, 2, 1)")
    v = q.ocupacao_turmas(con)
    assert v.status == q.FALHA


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


def test_ano_sem_ponto_de_milhar():
    assert q._formatar(2019, "ano") == "2019" and q._formatar(2019.0, "ano") == "2019"
    import pandas as pd
    texto = q.tabela_markdown(pd.DataFrame({"ano": [2019], "matriculas": [1234]}))
    assert "| 2019 | 1.234 |" in texto


# ------------------------------------------------------------------ banco vazio e relatório

def test_banco_sem_dados_nao_tem_o_que_reconciliar_nem_ocupar():
    con = duckdb.connect()
    carregar.criar_esquema(con)
    q07, q11 = q.reconciliacao(con), q.ocupacao_turmas(con)
    assert (q07.status, q11.status) == (q.OK, q.OK)
    assert "nada a reconciliar" in q07.resumo and "Nenhuma matrícula" in q11.resumo


def test_tabela_markdown_vazia_e_longa():
    import pandas as pd
    assert q.tabela_markdown(None) == "_sem linhas_\n"
    assert q.tabela_markdown(pd.DataFrame()) == "_sem linhas_\n"
    longa = q.tabela_markdown(pd.DataFrame({"ano": range(2000, 2070)}), limite=60)
    assert longa.count("\n| ") == 60 and "mais 10 linhas" in longa


def test_relatorio_sem_resumo_da_carga_nao_mostra_volumes():
    v = q.Verificacao("Q01", "Integridade referencial", q.OK, "tudo certo", None)
    texto = q.relatorio_markdown([v])
    assert "Volumes carregados" not in texto and "Integridade referencial · OK" in texto
