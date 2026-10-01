"""Quais recursos de cada base entram no recorte temporal.

Os nomes dos recursos no portal carregam o período: "Microdados de
Matrículas - 2015-2018", "Microdados de Matrícula - 2025",
"Demanda e Matrículas - Jun/2026", "Demanda por Vagas - 2006 a 2017".
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import PurePosixPath

from ..transformacao.microdados import arquivo_eh_escolarizacao
from ..transformacao.normalizacao import texto
from .ckan import Recurso

CKAN_BASE = "https://dados.prefeitura.sp.gov.br/api/3/action"
PACOTE_MICRODADOS = "microdados-matriculas"
PACOTE_FILA = "demanda-e-matriculas"

_INTERVALO = re.compile(r"\b((?:19|20)\d{2})\s*(?:-|A)\s*((?:19|20)\d{2})\b")
_ANO = re.compile(r"\b((?:19|20)\d{2})\b")


def anos_do_nome(nome: str) -> set[int]:
    t = texto(nome) or ""
    m = _INTERVALO.search(t)
    if m:
        return set(range(int(m.group(1)), int(m.group(2)) + 1))
    return {int(a) for a in _ANO.findall(t)}


def _no_recorte(recurso: Recurso, anos: Iterable[int]) -> bool:
    return bool(anos_do_nome(recurso.nome) & set(anos))


def _eh_dicionario(recurso: Recurso) -> bool:
    return (texto(recurso.nome) or "").startswith("DICIONARIO")


def selecionar_fila(recursos: list[Recurso], anos: Iterable[int]) -> list[Recurso]:
    """Planilhas de fila (CSV) do recorte, incluindo a série histórica quando ela o intercepta."""
    anos = list(anos)
    return [r for r in recursos if r.formato == "CSV" and not _eh_dicionario(r) and _no_recorte(r, anos)]


def selecionar_microdados(recursos: list[Recurso], anos: Iterable[int]) -> list[Recurso]:
    anos = list(anos)
    return [r for r in recursos
            if r.formato in ("ZIP", "RAR") and "MICRODADOS" in (texto(r.nome) or "") and _no_recorte(r, anos)]


def selecionar_dicionarios(recursos: list[Recurso]) -> list[Recurso]:
    """Dicionários de dados em CSV, guardados como documentação da origem."""
    return [r for r in recursos if r.formato == "CSV" and _eh_dicionario(r)]


def ano_do_membro_escolarizacao(membro: str) -> int | None:
    """Ano de um arquivo de matrícula de escolarização dentro do pacote, ou None se não for um."""
    nome = PurePosixPath(membro.replace("\\", "/")).name
    if not nome.lower().endswith((".csv", ".txt")) or "NOTA" in (texto(nome) or ""):
        return None
    if not arquivo_eh_escolarizacao(nome):
        return None
    m = re.search(r"(20\d{2})", nome)
    return int(m.group(1)) if m else None
