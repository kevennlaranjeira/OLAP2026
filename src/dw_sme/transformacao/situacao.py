"""Desfecho da matrícula a partir dos 12 indicadores SIT_AL_* do microdado.

Os indicadores não são mutuamente exclusivos: há matrículas marcadas como
aprovadas e reprovadas ao mesmo tempo (8.491 casos entre 2015 e 2024) e
matrículas transferidas que também constam como aprovadas. O resumo usado no
fato de desfecho precisa ser exclusivo, para que as contagens somem o total de
matrículas. A ordem de prioridade abaixo resolve os conflitos e está
documentada em docs/04-integracao-e-qualidade.md.
"""
from __future__ import annotations

from typing import Callable, Mapping

INDICADORES = (
    "aprovado", "reprovado", "abandono", "concluido", "transferido", "falecido",
    "nao_compareceu", "excluido", "cessado", "remanejado", "reclassificado", "ativo",
)
COLUNA_ORIGEM = {
    "aprovado": "SIT_AL_APROV", "reprovado": "SIT_AL_REPROV", "abandono": "SIT_AL_ABAND",
    "concluido": "SIT_AL_CONCL", "transferido": "SIT_AL_TRANSF", "falecido": "SIT_AL_FALEC",
    "nao_compareceu": "SIT_AL_NCOM", "excluido": "SIT_AL_EXCL", "cessado": "SIT_AL_CES",
    "remanejado": "SIT_AL_REMAN", "reclassificado": "SIT_AL_RECLAS", "ativo": "SIT_AL_ATIVO",
}

# (desfecho, indicadores que o disparam), em ordem de prioridade
_REGRAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("FALECIDO", ("falecido",)),
    ("TRANSFERIDO", ("transferido", "remanejado")),
    ("ABANDONO", ("abandono",)),
    ("REPROVADO", ("reprovado",)),
    ("APROVADO", ("aprovado",)),
    ("CONCLUIDO", ("concluido",)),
    ("OUTRA SAIDA", ("nao_compareceu", "excluido", "cessado", "reclassificado")),
    ("EM CURSO", ("ativo",)),
)
DESFECHOS = tuple(nome for nome, _ in _REGRAS) + ("SEM DESFECHO",)


def desfecho(indicadores: Mapping[str, bool | None]) -> str:
    for nome, gatilhos in _REGRAS:
        if any(indicadores.get(g) for g in gatilhos):
            return nome
    return "SEM DESFECHO"


def sql_desfecho(coluna: Callable[[str], str] = lambda k: k) -> str:
    """Equivalente SQL de `desfecho`. `coluna` traduz o indicador no nome da coluna booleana."""
    ramos = " ".join(
        f"WHEN {' OR '.join(f'coalesce({coluna(g)}, false)' for g in gatilhos)} THEN '{nome}'"
        for nome, gatilhos in _REGRAS
    )
    return f"(CASE {ramos} ELSE 'SEM DESFECHO' END)"
