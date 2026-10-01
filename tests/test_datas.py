"""Leitura das datas de matrícula nos cinco formatos publicados entre 2015 e 2024."""
from datetime import date

import duckdb
import pytest

from dw_sme.transformacao import datas as d

CASOS = [
    (("2019-02-04 00:00:00", 2019), date(2019, 2, 4)),      # 2015-2019 e 2022
    (("2019-12-20", 2019), date(2019, 12, 20)),
    (("1/10/2020 00:02:24", 2020), date(2020, 10, 1)),      # 2020: dia e mês sem zero à esquerda
    (("21/12/2020 13:47:49", 2020), date(2020, 12, 21)),
    (("01/02/2023 00:00", 2023), date(2023, 2, 1)),         # 2023-2024
    (("45656", 2024), date(2024, 12, 30)),                  # 2024: serial do Excel
    (("45323.5", 2024), date(2024, 2, 1)),
    (("2030-01-01 00:00:00", 2019), None),                  # fora da janela do ano letivo
    (("31/02/2019 00:00", 2019), None),                     # data impossível
    (("lixo", 2019), None),
    ((None, 2021), None),                                   # 2021 não publicou datas
]


@pytest.mark.parametrize("entrada, esperado", CASOS)
def test_data_publicada(entrada, esperado):
    assert d.data_publicada(*entrada) == esperado


def test_sql_igual_a_implementacao_python():
    con = duckdb.connect()
    con.execute("create table t(valor varchar, ano int)")
    con.executemany("insert into t values (?, ?)", [e for e, _ in CASOS])
    obtido = [r[0] for r in con.execute(f"select {d.sql_data('valor', 'ano')} from t").fetchall()]
    assert obtido == [esperado for _, esperado in CASOS]


def test_janela_aceita_ano_anterior_e_seguinte():
    # rematrícula em dezembro do ano anterior e encerramento em janeiro do seguinte são legítimos
    assert d.data_publicada("2018-12-10 00:00:00", 2019) == date(2018, 12, 10)
    assert d.data_publicada("2020-01-15 00:00:00", 2019) == date(2020, 1, 15)
    assert d.data_publicada("2017-12-31 00:00:00", 2019) is None


def test_calendario_da_dimensao():
    dias = d.calendario(2019, 2020)
    assert dias[0]["data"] == date(2019, 1, 1) and dias[-1]["data"] == date(2020, 12, 31)
    assert len(dias) == 365 + 366
    sabado = next(x for x in dias if x["data"] == date(2019, 2, 2))
    assert sabado["nome_dia_semana"] == "SABADO" and sabado["fim_de_semana"]
    assert sabado["trimestre"] == 1 and sabado["semestre"] == 1
