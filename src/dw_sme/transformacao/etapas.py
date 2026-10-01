"""Classificação das séries dos microdados nas etapas de ensino.

A etapa é a ponte entre as duas bases. A planilha de fila publica matrícula e
demanda por etapa (creche, pré-escola, fundamental I...), enquanto o
microdado traz a série de cada turma. Este módulo define o catálogo de etapas
conformado entre os dois fatos e a regra que leva cada série até ele.

Ciclo e etapa são hierarquias paralelas: o ciclo interdisciplinar (4o a 6o
ano) atravessa a fronteira entre anos iniciais e anos finais.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .normalizacao import texto


@dataclass(frozen=True)
class Etapa:
    codigo: str
    nome: str
    nivel: str
    ordem: int


ETAPAS: tuple[Etapa, ...] = (
    Etapa("CRECHE", "CRECHE", "EDUCACAO INFANTIL", 1),
    Etapa("PRE", "PRE-ESCOLA", "EDUCACAO INFANTIL", 2),
    Etapa("FUND_I", "ENSINO FUNDAMENTAL - ANOS INICIAIS", "ENSINO FUNDAMENTAL", 3),
    Etapa("FUND_II", "ENSINO FUNDAMENTAL - ANOS FINAIS", "ENSINO FUNDAMENTAL", 4),
    Etapa("MEDIO", "ENSINO MEDIO", "ENSINO MEDIO", 5),
    Etapa("EJA_I", "EJA - ANOS INICIAIS", "EDUCACAO DE JOVENS E ADULTOS", 6),
    Etapa("EJA_II", "EJA - ANOS FINAIS", "EDUCACAO DE JOVENS E ADULTOS", 7),
    Etapa("MOVA", "MOVA - ALFABETIZACAO DE JOVENS E ADULTOS", "EDUCACAO DE JOVENS E ADULTOS", 8),
    Etapa("PROJOVEM", "PROJOVEM", "EDUCACAO DE JOVENS E ADULTOS", 9),
    Etapa("ED_PROF", "EDUCACAO PROFISSIONAL", "EDUCACAO PROFISSIONAL", 10),
)
POR_CODIGO = {e.codigo: e for e in ETAPAS}

# Rótulos de coluna da planilha de fila (já normalizados por `texto`) -> etapa.
ETAPA_DA_COLUNA_FILA = {
    "CRECHE": "CRECHE",
    "PRE ESCOLA": "PRE",
    "ENS. FUND.I": "FUND_I",
    "ENS. FUND.II": "FUND_II",
    "EJA I": "EJA_I",
    "EJA II": "EJA_II",
    "ENS. MEDIO": "MEDIO",
    "ED. PROF.": "ED_PROF",
}

# Modalidades cujas turmas não são de escolarização (todas com TURMA_ESCOL = 'N').
NAO_ESCOLARIZACAO = frozenset({"ATCOMP", "REC", "SAAI", "OIE", "OSL", "CONVEE", "EDFIS", "EJAQUA"})

_POR_MODALIDADE = {"CRECHE": "CRECHE", "PRE": "PRE", "MEDIO": "MEDIO",
                   "EDPROF": "ED_PROF", "MOVA": "MOVA", "PROJ": "PROJOVEM"}
_POR_SEGMENTO = {"FUND1": "FUND_I", "FUN1A4": "FUND_I", "FUND2": "FUND_II", "FUN5A8": "FUND_II",
                 "EJA1A4": "EJA_I", "EJA5A8": "EJA_II", "MEDIO": "MEDIO", "PRE": "PRE",
                 "CRECHE": "CRECHE"}

_ANO = re.compile(r"(\d)\.ANO")
_CICLO = re.compile(r"^(?:EE)?C\.(I{1,3})\b")
_NOME_CICLO = {"I": "ALFABETIZACAO", "II": "INTERDISCIPLINAR", "III": "AUTORAL"}
_EJA_INICIAL = re.compile(r"\b(ALF|BASICA|MI|MII)\b")
_EJA_FINAL = re.compile(r"\b(COMPL|FINAL|MIII|MIV)\b")


@dataclass(frozen=True)
class Classificacao:
    modalidade: str
    segmento: str | None
    serie: str | None
    etapa: str
    ciclo: str | None
    ordem_serie: int | None
    educacao_especial: bool


def _ano_da_serie(serie: str | None) -> int | None:
    m = _ANO.search(serie or "")
    return int(m.group(1)) if m else None


def _ciclo(serie: str | None) -> str | None:
    m = _CICLO.match(serie or "")
    return _NOME_CICLO[m.group(1)] if m else None


def _etapa_pela_serie(serie: str | None) -> str | None:
    if not serie:
        return None
    ano = _ano_da_serie(serie)
    if ano:
        return "FUND_I" if ano <= 5 else "FUND_II"
    if "BILING" in serie:
        return "FUND_I"
    if "MED" in serie or "E.M" in serie or "NORMAL" in serie:
        return "MEDIO"
    if "INFANTIL" in serie or "PRE" in serie:
        return "PRE"
    if "BERCARIO" in serie or "MINI" in serie:
        return "CRECHE"
    if _EJA_FINAL.search(serie):
        return "EJA_II"
    if _EJA_INICIAL.search(serie):
        return "EJA_I"
    return None


def classificar(modalidade: str | None, segmento: str | None, serie: str | None) -> Classificacao | None:
    """Etapa de uma turma, ou None se ela não for de escolarização.

    A ordem de precedência é modalidade, depois segmento, depois o texto da
    série. O segmento resolve o fundamental e a EJA; a série cobre os anos em
    que o segmento falta e a educação especial, que usa um segmento genérico.
    """
    m, seg, s = texto(modalidade), texto(segmento), texto(serie)
    if m is None or m in NAO_ESCOLARIZACAO:
        return None
    if m in _POR_MODALIDADE:
        etapa = _POR_MODALIDADE[m]
    else:
        etapa = _POR_SEGMENTO.get(seg or "") or _etapa_pela_serie(s)
    if etapa is None:
        return None
    return Classificacao(
        modalidade=m, segmento=seg, serie=s, etapa=etapa,
        ciclo=_ciclo(s), ordem_serie=_ano_da_serie(s), educacao_especial=(m == "ESPEC"),
    )
