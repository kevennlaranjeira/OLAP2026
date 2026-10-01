"""Datas de início e fim da matrícula e o calendário da dimensão Data.

O microdado publica as datas em cinco formatos ao longo da série:
'2019-02-04 00:00:00' (2015-2019 e 2022), '1/10/2020 00:02:24' (2020, sem
zero à esquerda), '01/02/2023 00:00' (2023-2024), nenhuma data (2021) e, em
2024, cerca de metade das linhas como número serial do Excel ('45656' =
30/12/2024, contado em dias a partir de 30/12/1899).

Datas fora da janela de um ano antes a um ano depois do ano letivo são
tratadas como inválidas.

Como em idade.py, a regra existe em Python (referência testada) e em SQL (a
que roda sobre o microdado); um teste garante que coincidem.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta

FORMATOS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y")
_SERIAL_EXCEL = re.compile(r"[0-9]{5}([.][0-9]+)?")
_BASE_EXCEL = date(1899, 12, 30)
_DIAS = ("SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO")
_MESES = ("JANEIRO", "FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO", "JULHO",
          "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO")


def _na_janela(d: date, ano_letivo: int) -> bool:
    return date(ano_letivo - 1, 1, 1) <= d <= date(ano_letivo + 1, 12, 31)


def data_publicada(valor: str | None, ano_letivo: int) -> date | None:
    if valor is None:
        return None
    s = str(valor).strip()
    d = None
    if _SERIAL_EXCEL.fullmatch(s):
        d = _BASE_EXCEL + timedelta(days=int(float(s)))
    else:
        for formato in FORMATOS:
            try:
                d = datetime.strptime(s, formato).date()
                break
            except ValueError:
                continue
    return d if d is not None and _na_janela(d, ano_letivo) else None


def sql_data(coluna: str, ano: str) -> str:
    """Equivalente SQL de `data_publicada`."""
    v = f"trim({coluna})"
    formatos = ", ".join(f"'{f}'" for f in FORMATOS)
    bruta = (f"(CASE WHEN regexp_full_match({v}, '[0-9]{{5}}([.][0-9]+)?') "
             f"THEN DATE '1899-12-30' + CAST(floor(CAST({v} AS DOUBLE)) AS INTEGER) "
             f"ELSE CAST(try_strptime({v}, [{formatos}]) AS DATE) END)")
    return (f"(CASE WHEN {bruta} BETWEEN make_date({ano} - 1, 1, 1) AND make_date({ano} + 1, 12, 31) "
            f"THEN {bruta} END)")


def calendario(ano_inicial: int, ano_final: int) -> list[dict]:
    """Um registro por dia, de 1o de janeiro do ano inicial a 31 de dezembro do ano final."""
    dias, d = [], date(ano_inicial, 1, 1)
    while d <= date(ano_final, 12, 31):
        dias.append({
            "data": d, "dia": d.day, "mes": d.month, "nome_mes": _MESES[d.month - 1],
            "trimestre": (d.month - 1) // 3 + 1, "semestre": (d.month - 1) // 6 + 1, "ano": d.year,
            "dia_semana": d.isoweekday(), "nome_dia_semana": _DIAS[d.weekday()],
            "fim_de_semana": d.weekday() >= 5,
        })
        d += timedelta(days=1)
    return dias
