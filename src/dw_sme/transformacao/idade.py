"""Idade do aluno em 31 de março do ano letivo e as faixas da dimensão Idade.

A idade publicada tem quatro defeitos conhecidos: vem com vírgula decimal em
2020 ('5,00'), falta em centenas de milhares de linhas de 2021 e 2022, usa o
ano de nascimento 1900 como valor padrão (idades de 115 a 124) e, em 2022, o
mês de nascimento traz valores acima de 12. A regra abaixo usa a idade
publicada quando ela é plausível e, se não for, calcula a partir do
nascimento. Quando o mês é inválido, a idade é estimada só pelo ano e a linha
fica marcada.

A regra existe duas vezes: em Python, que é a referência testada caso a caso,
e em SQL, que é a que roda sobre o microdado inteiro. Um teste garante que as
duas dão o mesmo resultado.
"""
from __future__ import annotations

from .normalizacao import inteiro_br

IDADE_MAXIMA = 99
ANO_NASCIMENTO_MINIMO = 1901  # 1900 é o valor padrão do sistema de origem

FAIXAS_ESCOLARES = (
    (0, 3, "0 A 3 ANOS"), (4, 5, "4 E 5 ANOS"), (6, 10, "6 A 10 ANOS"),
    (11, 14, "11 A 14 ANOS"), (15, 17, "15 A 17 ANOS"), (18, 29, "18 A 29 ANOS"),
    (30, 999, "30 ANOS OU MAIS"),
)
# Mesmo corte do tema Demografia dos Agregados por Setores do Censo 2022 (V01031 a V01041).
FAIXAS_IBGE = (
    (0, 4, "0 A 4 ANOS"), (5, 9, "5 A 9 ANOS"), (10, 14, "10 A 14 ANOS"),
    (15, 19, "15 A 19 ANOS"), (20, 24, "20 A 24 ANOS"), (25, 29, "25 A 29 ANOS"),
    (30, 39, "30 A 39 ANOS"), (40, 49, "40 A 49 ANOS"), (50, 59, "50 A 59 ANOS"),
    (60, 69, "60 A 69 ANOS"), (70, 999, "70 ANOS OU MAIS"),
)
GRUPOS_ETARIOS = ((0, 11, "CRIANCA"), (12, 17, "ADOLESCENTE"), (18, 59, "ADULTO"), (60, 999, "IDOSO"))


def idade_referencia(ano_letivo: int, idade_publicada: str | None,
                     ano_nascimento: str | None, mes_nascimento: str | None) -> tuple[int | None, bool]:
    """Retorna (idade, estimada). Idade None significa 'não informada'."""
    publicada = inteiro_br(idade_publicada)
    if publicada is not None and 0 <= publicada <= IDADE_MAXIMA:
        return publicada, False
    ano = inteiro_br(ano_nascimento)
    if ano is None or ano < ANO_NASCIMENTO_MINIMO or ano > ano_letivo:
        return None, False
    mes = inteiro_br(mes_nascimento)
    if mes is not None and 1 <= mes <= 12:
        idade, estimada = ano_letivo - ano - (1 if mes > 3 else 0), False
    else:
        idade, estimada = ano_letivo - ano - 1, True
    if not 0 <= idade <= IDADE_MAXIMA:
        return None, False
    return idade, estimada


def sql_inteiro_br(coluna: str) -> str:
    """Equivalente SQL de `normalizacao.inteiro_br`, só com operações de texto (sem regex)."""
    limpo = f"replace(trim({coluna}), '.', '')"
    return (
        f"(CASE WHEN {coluna} IS NULL OR strpos(upper({coluna}), 'E') > 0 THEN NULL "
        f"WHEN replace(split_part({limpo}, ',', 2), '0', '') <> '' THEN NULL "
        f"ELSE TRY_CAST(split_part({limpo}, ',', 1) AS INTEGER) END)"
    )


def _calculada(ano: str, an: str, mes: str) -> str:
    return (f"({ano} - {an} - (CASE WHEN {mes} BETWEEN 1 AND 12 "
            f"THEN (CASE WHEN {mes} > 3 THEN 1 ELSE 0 END) ELSE 1 END))")


def sql_idade_inteiros(ano: str, pub: str, an: str, mes: str) -> str:
    """Regra da idade sobre colunas já convertidas para inteiro (conversão feita uma vez por linha)."""
    calc = _calculada(ano, an, mes)
    return (
        f"(CASE WHEN {pub} BETWEEN 0 AND {IDADE_MAXIMA} THEN {pub} "
        f"WHEN {an} IS NULL OR {an} < {ANO_NASCIMENTO_MINIMO} OR {an} > {ano} THEN NULL "
        f"WHEN {calc} BETWEEN 0 AND {IDADE_MAXIMA} THEN {calc} END)"
    )


def sql_idade_estimada_inteiros(ano: str, pub: str, an: str, mes: str) -> str:
    calc = _calculada(ano, an, mes)
    return (
        f"(CASE WHEN {pub} BETWEEN 0 AND {IDADE_MAXIMA} THEN false "
        f"WHEN {an} IS NULL OR {an} < {ANO_NASCIMENTO_MINIMO} OR {an} > {ano} THEN false "
        f"WHEN NOT ({calc} BETWEEN 0 AND {IDADE_MAXIMA}) THEN false "
        f"WHEN {mes} BETWEEN 1 AND 12 THEN false ELSE true END)"
    )


def sql_idade(ano: str, idade: str, ano_nasc: str, mes_nasc: str) -> str:
    return sql_idade_inteiros(ano, sql_inteiro_br(idade), sql_inteiro_br(ano_nasc), sql_inteiro_br(mes_nasc))


def sql_idade_estimada(ano: str, idade: str, ano_nasc: str, mes_nasc: str) -> str:
    return sql_idade_estimada_inteiros(ano, sql_inteiro_br(idade), sql_inteiro_br(ano_nasc),
                                       sql_inteiro_br(mes_nasc))


def _faixa(idade: int | None, faixas, nulo: str) -> str:
    if idade is None:
        return nulo
    for inicio, fim, rotulo in faixas:
        if inicio <= idade <= fim:
            return rotulo
    return nulo


def faixa_escolar(idade: int | None) -> str:
    return _faixa(idade, FAIXAS_ESCOLARES, "NAO INFORMADA")


def faixa_ibge(idade: int | None) -> str:
    return _faixa(idade, FAIXAS_IBGE, "NAO INFORMADA")


def grupo_etario(idade: int | None) -> str:
    return _faixa(idade, GRUPOS_ETARIOS, "NAO INFORMADO")
