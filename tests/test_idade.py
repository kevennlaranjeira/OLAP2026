"""Idade em 31 de março e faixas. Casos dos defeitos encontrados: vírgula
decimal em 2020, nulos em 2021-22, mês de nascimento maior que 12 em 2022 e
ano de nascimento 1900 usado como valor padrão."""
import duckdb
import pytest

from dw_sme.transformacao import idade as i

CASOS = [
    # (ano letivo, idade publicada, ano nasc., mês nasc.) -> (idade, estimada)
    ((2019, "11", "2008", "5"), (11, False)),       # publicada válida prevalece
    ((2020, "5,00", None, None), (5, False)),       # vírgula decimal de 2020
    ((2022, None, "2019", "2"), (3, False)),        # nasceu em fevereiro: já fez aniversário
    ((2022, None, "2019", "7"), (2, False)),        # nasceu em julho: ainda não fez
    ((2022, None, "2019", "18"), (2, True)),        # mês impossível: estimada pelo ano
    ((2015, "115", "1900", "1"), (None, False)),    # 1900 = valor padrão
    ((2024, "-1", "2025", "1"), (None, False)),     # nascimento depois do ano letivo
    ((2021, None, None, None), (None, False)),
    ((2023, "0", "2022", "12"), (0, False)),
    ((2016, "abc", "2010", "3"), (6, False)),       # publicada ilegível: calcula
    ((2018, "99", "1919", "1"), (99, False)),
    ((2018, "100", "1918", "1"), (None, False)),    # acima de 99 é tratado como inválido
]


@pytest.mark.parametrize("entrada, esperado", CASOS)
def test_idade_referencia(entrada, esperado):
    assert i.idade_referencia(*entrada) == esperado


def test_sql_igual_a_implementacao_python():
    """A regra roda em SQL sobre 15 milhões de linhas; a versão Python é a referência."""
    con = duckdb.connect()
    con.execute("create table t(ano int, idade varchar, ano_nasc varchar, mes_nasc varchar)")
    con.executemany("insert into t values (?,?,?,?)", [c for c, _ in CASOS])
    sql = (
        f"select {i.sql_idade('ano', 'idade', 'ano_nasc', 'mes_nasc')}, "
        f"{i.sql_idade_estimada('ano', 'idade', 'ano_nasc', 'mes_nasc')} from t"
    )
    obtido = [(a, bool(b)) for a, b in con.execute(sql).fetchall()]
    assert obtido == [esperado for _, esperado in CASOS]


@pytest.mark.parametrize("idade, escolar, ibge, grupo", [
    (0, "0 A 3 ANOS", "0 A 4 ANOS", "CRIANCA"),
    (3, "0 A 3 ANOS", "0 A 4 ANOS", "CRIANCA"),
    (4, "4 E 5 ANOS", "0 A 4 ANOS", "CRIANCA"),
    (5, "4 E 5 ANOS", "5 A 9 ANOS", "CRIANCA"),
    (10, "6 A 10 ANOS", "10 A 14 ANOS", "CRIANCA"),
    (14, "11 A 14 ANOS", "10 A 14 ANOS", "ADOLESCENTE"),
    (17, "15 A 17 ANOS", "15 A 19 ANOS", "ADOLESCENTE"),
    (25, "18 A 29 ANOS", "25 A 29 ANOS", "ADULTO"),
    (45, "30 ANOS OU MAIS", "40 A 49 ANOS", "ADULTO"),
    (72, "30 ANOS OU MAIS", "70 ANOS OU MAIS", "IDOSO"),
    (None, "NAO INFORMADA", "NAO INFORMADA", "NAO INFORMADO"),
])
def test_faixas(idade, escolar, ibge, grupo):
    assert i.faixa_escolar(idade) == escolar
    assert i.faixa_ibge(idade) == ibge
    assert i.grupo_etario(idade) == grupo


def test_faixa_escolar_e_ibge_sao_hierarquias_paralelas():
    # 4 anos cai em '4 e 5' (escolar) mas em '0 a 4' (IBGE)
    assert i.faixa_escolar(4) != i.faixa_escolar(3)
    assert i.faixa_ibge(4) == i.faixa_ibge(3)


def test_faixas_ibge_iguais_as_do_censo_2022():
    # Corte do tema Demografia dos Agregados por Setores (V01031 a V01041)
    assert i.FAIXAS_IBGE[0] == (0, 4, "0 A 4 ANOS")
    assert i.FAIXAS_IBGE[-1] == (70, 999, "70 ANOS OU MAIS")
    assert len(i.FAIXAS_IBGE) == 11
