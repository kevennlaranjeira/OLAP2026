"""Identidade das escolas entre anos e versões da dimensão Escola.

Problema: o código da escola (CD_UNIDADE_EDUCACAO) é íntegro de 2015 a 2021,
chega embaralhado mas ainda um para um em 2022, e é destruído em 2023 e 2024
(notação científica, com centenas de escolas colidindo no mesmo código).

Solução, em três passos:

1. avaliar_codigos: classifica o código de cada ano a partir do próprio dado,
   sem lista fixa de anos ruins.
2. identificar: nos anos de código confiável usa o código publicado; nos
   demais, recupera o código casando nome, tipo e distrito com o último ano
   confiável em que essa combinação aponta para uma única escola. Homônimos
   e escolas novas recebem chave sintética estável (hash do nome, tipo e
   distrito).
3. versionar: dimensão de mudança lenta tipo 2. Mudança de nome, tipo,
   distrito ou DRE abre nova versão; mudança só de grafia, não.

Tudo roda sobre as escolas distintas por ano (cerca de 45 mil linhas), não
sobre os 13 milhões de matrículas. A junção com o fato usa o mapa gerado aqui.
"""
from __future__ import annotations

import hashlib

import pandas as pd

from . import normalizacao as n

CONFIAVEL = "CONFIAVEL"
CONSISTENTE_NO_ANO = "CONSISTENTE_NO_ANO"
CORROMPIDO = "CORROMPIDO"

PUBLICADO = "PUBLICADO"
RECUPERADO = "RECUPERADO_POR_NOME"
SINTETICO = "SINTETICO"

_TAMANHO_MAXIMO_CODIGO_SME = 8
_ATRIBUTOS_VERSIONADOS = ("nome", "tipo", "distrito", "dre")


def codigo_normalizado(cd: str | None) -> str | None:
    if cd is None or (isinstance(cd, float) and pd.isna(cd)):
        return None
    s = str(cd).strip()
    if not s:
        return None
    return (s.lstrip("0") or "0") if s.isdigit() else s


def _str_ou_none(v) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    return s or None


def normalizar(escolas: pd.DataFrame) -> pd.DataFrame:
    """Recebe as escolas distintas por ano como publicadas e acrescenta as formas normalizadas.

    Colunas de entrada: ano, cd_origem, nome, tipo, distrito, dre, setor, situacao, matriculas.
    As colunas brutas são preservadas com sufixo _bruto: são a chave de junção com o staging.
    """
    df = escolas.rename(columns={c: f"{c}_bruto" for c in
                                 ("cd_origem", "nome", "tipo", "distrito", "dre", "setor", "situacao")}).copy()
    df.rename(columns={"cd_origem_bruto": "cd_bruto"}, inplace=True)
    df["ano"] = df["ano"].astype(int)
    df["cd_origem"] = df["cd_bruto"].map(_str_ou_none)
    df["nome"] = df["nome_bruto"].map(n.texto)
    df["tipo"] = df["tipo_bruto"].map(n.tipo_escola)
    df["distrito"] = df["distrito_bruto"].map(n.distrito)
    df["dre"] = df["dre_bruto"].map(n.dre)
    df["setor"] = df["setor_bruto"].map(_str_ou_none)
    df["situacao"] = df["situacao_bruto"].map(n.situacao_escola)
    df["tripla"] = df["nome"].fillna("") + "|" + df["tipo"].fillna("") + "|" + df["distrito"].fillna("")
    return df


def avaliar_codigos(df: pd.DataFrame) -> dict[int, str]:
    """Qualidade do código da escola em cada ano.

    CORROMPIDO: notação científica ou um mesmo código cobrindo escolas diferentes.
    CONFIAVEL: numérico de até 8 dígitos e um para um.
    CONSISTENTE_NO_ANO: um para um, mas fora do formato do código SME.
    """
    resultado = {}
    for ano, g in df.groupby("ano"):
        codigos = g["cd_origem"].dropna()
        cientifica = codigos.str.upper().str.contains("E+", regex=False).any()
        colisao = (g.dropna(subset=["cd_origem"]).groupby("cd_origem")["tripla"].nunique() > 1).any()
        if cientifica or colisao:
            resultado[int(ano)] = CORROMPIDO
        elif codigos.map(lambda c: c.isdigit() and len(codigo_normalizado(c)) <= _TAMANHO_MAXIMO_CODIGO_SME).all():
            resultado[int(ano)] = CONFIAVEL
        else:
            resultado[int(ano)] = CONSISTENTE_NO_ANO
    return resultado


def _sintetica(chave: str) -> str:
    return "SINT-" + hashlib.sha1(chave.encode("utf-8")).hexdigest()[:10].upper()


def _referencia(df: pd.DataFrame) -> dict[str, str | None]:
    """Tripla -> código no último ano confiável em que ela aparece (None se ambígua)."""
    confiaveis = df[df["qualidade_codigo"] == CONFIAVEL].copy()
    confiaveis["cod"] = confiaveis["cd_origem"].map(codigo_normalizado)
    ultimo = confiaveis.groupby("tripla")["ano"].transform("max")
    recente = confiaveis[confiaveis["ano"] == ultimo]
    codigos = recente.groupby("tripla")["cod"].unique()
    return {t: (c[0] if len(c) == 1 else None) for t, c in codigos.items()}


def identificar(df: pd.DataFrame) -> pd.DataFrame:
    """Atribui a cada escola-ano o código natural (cod_escola) e o tipo de vínculo usado."""
    df = df.copy()
    qualidade = avaliar_codigos(df)
    df["qualidade_codigo"] = df["ano"].map(qualidade)
    ref = _referencia(df)
    homonimos_no_ano = df.groupby(["ano", "tripla"])["cd_origem"].transform("nunique") > 1

    cods, vinculos = [], []
    for row, homonimo in zip(df.itertuples(index=False), homonimos_no_ano):
        if row.qualidade_codigo == CONFIAVEL:
            cods.append(codigo_normalizado(row.cd_origem))
            vinculos.append(PUBLICADO)
        elif row.qualidade_codigo == CONSISTENTE_NO_ANO and homonimo:
            cods.append(_sintetica(f"{row.tripla}|{row.cd_origem}"))
            vinculos.append(SINTETICO)
        elif ref.get(row.tripla):
            cods.append(ref[row.tripla])
            vinculos.append(RECUPERADO)
        else:
            cods.append(_sintetica(row.tripla))
            vinculos.append(SINTETICO)
    df["cod_escola"] = cods
    df["vinculo"] = vinculos
    df["codigo_sintetico"] = df["vinculo"] == SINTETICO
    # nos anos sem código confiável o setor também chega corrompido
    df.loc[df["qualidade_codigo"] != CONFIAVEL, "setor"] = None
    return df


def _moda_ponderada(df: pd.DataFrame, chaves: list[str], coluna: str) -> pd.DataFrame:
    """Valor mais frequente de `coluna` em cada grupo, ponderado por matrículas.

    Empate é desfeito pela ordem alfabética, para o resultado ser determinístico.
    """
    validos = df.dropna(subset=[coluna])
    soma = validos.groupby([*chaves, coluna], sort=False)["matriculas"].sum().reset_index()
    soma = soma.sort_values([*chaves, "matriculas", coluna],
                            ascending=[True] * len(chaves) + [False, True])
    return soma.drop_duplicates(chaves)[[*chaves, coluna]]


def versionar(identificadas: pd.DataFrame) -> pd.DataFrame:
    """Dimensão Escola como mudança lenta tipo 2, uma linha por versão.

    Cada escola-ano recebe a forma mais frequente de cada atributo. Uma nova
    versão começa quando nome, tipo, distrito ou DRE diferem do ano anterior
    da mesma escola. Setor e situação são tipo 1 dentro da versão: guardam o
    último valor conhecido.
    """
    chaves = ["cod_escola", "ano"]
    base = identificadas.groupby(chaves, as_index=False).agg(codigo_sintetico=("codigo_sintetico", "all"))
    for atributo in (*_ATRIBUTOS_VERSIONADOS, "setor", "situacao"):
        base = base.merge(_moda_ponderada(identificadas, chaves, atributo), on=chaves, how="left")
    base = base.sort_values(chaves).reset_index(drop=True)

    assinatura = base[list(_ATRIBUTOS_VERSIONADOS)].fillna("<nulo>").astype(str).agg("|".join, axis=1)
    nova = (base["cod_escola"] != base["cod_escola"].shift()) | (assinatura != assinatura.shift())
    base["versao"] = nova.astype(int).groupby(base["cod_escola"]).cumsum()

    dim = base.groupby(["cod_escola", "versao"], as_index=False).agg(
        codigo_sintetico=("codigo_sintetico", "all"),
        ano_inicio=("ano", "min"), ano_fim=("ano", "max"),
        nome_escola=("nome", "first"), tipo_escola=("tipo", "first"),
        distrito=("distrito", "first"), dre=("dre", "first"),
        setor_sme=("setor", "last"), situacao=("situacao", "last"),
    )
    dim["rede"] = dim["tipo_escola"].map(n.rede)
    dim["versao_atual"] = dim["versao"] == dim.groupby("cod_escola")["versao"].transform("max")
    dim = dim.sort_values(["cod_escola", "versao"]).reset_index(drop=True)
    dim.insert(0, "chave_escola", range(1, len(dim) + 1))
    colunas = ["chave_escola", "cod_escola", "codigo_sintetico", "versao", "ano_inicio", "ano_fim",
               "versao_atual", "nome_escola", "tipo_escola", "rede", "distrito", "dre", "setor_sme", "situacao"]
    return dim[colunas]


def mapa_carga(identificadas: pd.DataFrame, versoes: pd.DataFrame) -> pd.DataFrame:
    """Combinação bruta do staging -> chave da versão de escola vigente no ano."""
    brutas = identificadas[["ano", "cd_bruto", "nome_bruto", "tipo_bruto", "distrito_bruto",
                            "cod_escola", "vinculo"]].drop_duplicates()
    m = brutas.merge(versoes[["chave_escola", "cod_escola", "ano_inicio", "ano_fim"]], on="cod_escola")
    m = m[(m["ano"] >= m["ano_inicio"]) & (m["ano"] <= m["ano_fim"])]
    return m.drop(columns=["ano_inicio", "ano_fim"]).reset_index(drop=True)


def resumo_vinculo(identificadas: pd.DataFrame) -> pd.DataFrame:
    """Matrículas por ano e tipo de vínculo da escola (para o relatório de qualidade)."""
    return (identificadas.pivot_table(index="ano", columns="vinculo", values="matriculas",
                                      aggfunc="sum", fill_value=0)
            .reindex(columns=[PUBLICADO, RECUPERADO, SINTETICO], fill_value=0))
