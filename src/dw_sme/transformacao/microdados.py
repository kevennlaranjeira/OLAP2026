"""Harmonização do microdado de matrícula entre os anos.

Os arquivos de 2015 a 2024 trazem a mesma informação com nomes de coluna
diferentes ('idade_aluno_31_03', 'IDADE_ALUNO_3103', 'IDADE_ALUNO_MAR';
'DEF_AUTISMO' e 'DEF__AUTISMO'; 'QTD_DIAS_MATR' e 'QTD_DIAS_MAT') e com
colunas que existem só em parte da série. Este módulo gera, para cada arquivo,
um SELECT que leva as colunas encontradas para um vocabulário canônico único.

A seleção olha as colunas que o arquivo realmente tem; não existe tabela fixa
de "qual ano tem qual coluna". Coluna ausente vira nulo tipado.

Nenhum valor é transformado aqui: o staging guarda o texto como publicado.
A normalização acontece depois, por tabelas de correspondência construídas
sobre os valores distintos (ver normalizacao.py).
"""
from __future__ import annotations

from ..texto_sql import literal
from .normalizacao import texto
from .situacao import COLUNA_ORIGEM as _SITUACAO_ORIGEM

_DEF_ORIGEM = {
    "autismo": "AUTISMO",
    "surdez_leve": "SURDEZ_LEVE",
    "surdez_severa": "SURDEZ_SEV",
    "surdez_unilateral": "SURDEZ_UNILATERAL",
    "intelectual": "INTELECT",
    "multipla": "MULTIPLA",
    "cegueira": "CEGUEIRA",
    "baixa_visao": "BAIXA_VISAO",
    "surdocegueira": "SURDO_CEG",
    "transtorno_desintegrativo": "TRANST_DES_INF",
    "sindrome_asperger": "SINDR_ASPER",
    "sindrome_rett": "SINDR_RETT",
    "fisica_sem_cadeira": "FIS_N_CADEIR",
    "fisica_cadeirante": "FIS_CADEIR",
    "visao_monocular": "VISAO_MONOCULAR",
    "paralisia_cerebral": "PARALISIA_CEREBRAL",
    "sindrome_down": "SINDROME_DOWN",
}
DEFICIENCIAS = tuple(_DEF_ORIGEM)

# Coluna canônica -> nomes possíveis na origem, em ordem de preferência.
_ALIASES: dict[str, tuple[str, ...]] = {
    "ano_publicado": ("AN_LETIVO",),
    "cd_escola_origem": ("CD_UNIDADE_EDUCACAO",),
    "cd_inep_escola_origem": ("CD_INEP_ESCOLA",),
    "nome_escola": ("NOME_ESCOLA",),
    "tipo_escola": ("TIPO_ESCOLA",),
    "distrito": ("NOME_DISTRITO",),
    "dre": ("DRE",),
    "setor_sme": ("CD_SETOR",),
    "situacao_escola": ("SITUACAO_ESCOLA",),
    "cd_turma_origem": ("CD_TURMA",),
    "nome_turma": ("NOME_TURMA",),
    "cd_turno": ("CD_TURNO",),
    "desc_turno": ("DESC_TURNO",),
    "hora_inicio": ("HORA_IN_TURMA", "HORA_INICIO"),
    "hora_fim": ("HORA_FIM_TURMA",),
    "modalidade": ("MODALIDADE",),
    "segmento": ("MODALIDADE_SEGMENTO",),
    "serie": ("DESC_SERIE",),
    "turma_escol": ("TURMA_ESCOL",),
    "idade_publicada": ("IDADE_ALUNO_MAR", "IDADE_ALUNO_3103", "IDADE_ALUNO_31_03"),
    "ano_nascimento": ("ANO_NASC_ALUNO",),
    "mes_nascimento": ("MES_NASC_ALUNO",),
    "sexo": ("CD_SEXO",),
    "raca_cor": ("DESC_RACA_COR",),
    "nee_altas_habilidades": ("NEE_ALT_HAB",),
    "cd_matricula_origem": ("CD_MAT",),
    "dt_inicio": ("DT_IN_MAT",),
    "dt_fim": ("DT_FIM_MAT",),
    "qtd_dias": ("QTD_DIAS_MAT", "QTD_DIAS_MATR"),
    "situacao_matricula": ("SITUACAO_MAT",),
    **{f"sit_{k}": (col,) for k, col in _SITUACAO_ORIGEM.items()},
    **{f"def_{k}": (f"DEF_{suf}", f"DEF__{suf}") for k, suf in _DEF_ORIGEM.items()},
    "def_nao_possui": ("DEF_N_POSSUI", "DEF__N_POSSUI"),
}
COLUNAS_CANONICAS = tuple(_ALIASES)

_NULO = "CAST(NULL AS VARCHAR)"


def _chave(nome: str) -> str:
    return nome.replace("﻿", "").strip().upper()


def _citar(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def expressoes(colunas_disponiveis: list[str]) -> dict[str, str]:
    """Expressão SQL de cada coluna canônica para um arquivo com estas colunas."""
    por_chave: dict[str, str] = {}
    for c in colunas_disponiveis:
        por_chave.setdefault(_chave(c), c)
    saida = {}
    for canonica, candidatos in _ALIASES.items():
        achada = next((por_chave[a] for a in candidatos if a in por_chave), None)
        saida[canonica] = _citar(achada) if achada else _NULO
    return saida


def arquivo_eh_escolarizacao(nome_arquivo: str) -> bool:
    """Arquivos de atividades complementares nunca entram no fato de matrícula."""
    t = texto(nome_arquivo) or ""
    return not ("ATIVIDADE" in t or "COMPLEMENTAR" in t)


def sql_filtro_escolarizacao(expr_turma_escol: str, nome_arquivo: str) -> str:
    """TURMA_ESCOL decide quando contém S ou N; caso contrário decide o arquivo.

    Em 2023 a coluna traz o nome da turma ('4A') em vez do indicador, e os
    arquivos já vêm separados por escolarização.
    """
    padrao = "true" if arquivo_eh_escolarizacao(nome_arquivo) else "false"
    if expr_turma_escol == _NULO:
        return padrao
    flag = f"upper(trim({expr_turma_escol}))"
    return f"(CASE WHEN {flag} IN ('S', 'N') THEN {flag} = 'S' ELSE {padrao} END)"


def sql_staging(fonte: str, ano: int, nome_arquivo: str, colunas_disponiveis: list[str]) -> str:
    """SELECT que leva um arquivo bruto ao staging canônico, já filtrado."""
    expr = expressoes(colunas_disponiveis)
    campos = ",\n  ".join(f"{e} AS {c}" for c, e in expr.items())
    return (
        f"SELECT CAST({int(ano)} AS INTEGER) AS ano_letivo, {literal(nome_arquivo)} AS arquivo,\n  {campos}\n"
        f"FROM {fonte}\n"
        f"WHERE {sql_filtro_escolarizacao(expr['turma_escol'], nome_arquivo)}"
    )
