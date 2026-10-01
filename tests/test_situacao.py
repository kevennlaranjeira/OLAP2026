"""Resumo do desfecho da matrícula a partir dos 12 indicadores SIT_AL_*."""
import duckdb
import pytest

from dw_sme.transformacao import situacao as s


def flags(*ligados):
    return {k: (k in ligados) for k in s.INDICADORES}


@pytest.mark.parametrize("ligados, esperado", [
    (("aprovado",), "APROVADO"),
    (("reprovado",), "REPROVADO"),
    (("abandono",), "ABANDONO"),
    (("transferido",), "TRANSFERIDO"),
    (("remanejado",), "TRANSFERIDO"),
    (("concluido",), "CONCLUIDO"),
    (("ativo",), "EM CURSO"),
    (("falecido",), "FALECIDO"),
    (("aprovado", "reprovado"), "REPROVADO"),   # 8.491 casos reais: prioridade explícita
    (("aprovado", "transferido"), "TRANSFERIDO"),
    (("abandono", "ativo"), "ABANDONO"),
    ((), "SEM DESFECHO"),
])
def test_prioridade(ligados, esperado):
    assert s.desfecho(flags(*ligados)) == esperado


def test_nulos_contam_como_desligados():
    f = {k: None for k in s.INDICADORES}
    f["abandono"] = True
    assert s.desfecho(f) == "ABANDONO"


def test_categorias_unicas_e_sem_desfecho_por_ultimo():
    assert s.DESFECHOS[-1] == "SEM DESFECHO"
    assert len(set(s.DESFECHOS)) == len(s.DESFECHOS)


def test_colunas_de_origem_mapeadas_para_os_12_indicadores():
    assert len(s.INDICADORES) == 12
    assert set(s.COLUNA_ORIGEM) == set(s.INDICADORES)
    assert all(c.startswith("SIT_AL_") for c in s.COLUNA_ORIGEM.values())


def test_sql_reproduz_python():
    con = duckdb.connect()
    con.execute("create table t(" + ", ".join(f"{k} boolean" for k in s.INDICADORES) + ")")
    combinacoes = [(), ("aprovado",), ("aprovado", "reprovado"), ("abandono", "ativo"),
                   ("transferido", "concluido"), ("falecido", "abandono"), ("remanejado",),
                   ("ativo",), ("concluido",), ("reclassificado",)]
    linhas = [tuple(k in c for k in s.INDICADORES) for c in combinacoes]
    con.executemany(f"insert into t values ({','.join('?' * len(s.INDICADORES))})", linhas)
    obtido = [r[0] for r in con.execute(f"select {s.sql_desfecho()} from t").fetchall()]
    assert obtido == [s.desfecho(flags(*c)) for c in combinacoes]
