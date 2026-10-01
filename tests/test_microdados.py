"""Harmonização das colunas do microdado de matrícula entre os anos."""
import duckdb
import pandas as pd
import pytest

from dw_sme.transformacao import microdados as m

# Subconjuntos reais dos cabeçalhos de cada época
COLS_2015 = ["AN_LETIVO", "CD_UNIDADE_EDUCACAO", "NOME_DISTRITO", "TURMA_ESCOL", "idade_aluno_31_03",
             "DEF_AUTISMO", "DEF_N_POSSUI", "QTD_DIAS_MATR", "SIT_AL_APROV", "CD_INEP_ALUNO"]
COLS_2019 = ["AN_LETIVO", "CD_UNIDADE_EDUCACAO", "NOME_DISTRITO", "TURMA_ESCOL", "IDADE_ALUNO_3103",
             "DEF__AUTISMO", "DEF__N_POSSUI", "QTD_DIAS_MATR", "SIT_AL_APROV"]
COLS_2021 = ["AN_LETIVO", "CD_UNIDADE_EDUCACAO", "NOME_DISTRITO", "TURMA_ESCOL", "Hora_Inicio",
             "HORA_IN_TURMA", "IDADE_ALUNO_MAR", "DEF__AUTISMO", "QTD_DIAS_MAT", "SIT_AL_APROV"]
COLS_2023_BOM = ["﻿AN_LETIVO", "CD_UNIDADE_EDUCACAO", "NOME_DISTRITO", "TURMA_ESCOL",
                 "IDADE_ALUNO_MAR", "DEF__AUTISMO", "QTD_DIAS_MAT", "SIT_AL_APROV"]
COLS_2024 = ["AN_LETIVO", "CD_UNIDADE_EDUCACAO", "NOME_DISTRITO", "TURMA_ESCOL", "IDADE_ALUNO_MAR",
             "DEF__AUTISMO", "DEF_SURDEZ_UNILATERAL", "DEF_SINDROME_DOWN", "QTD_DIAS_MAT", "SIT_AL_APROV"]


@pytest.mark.parametrize("colunas, origem_idade, origem_dias", [
    (COLS_2015, "idade_aluno_31_03", "QTD_DIAS_MATR"),
    (COLS_2019, "IDADE_ALUNO_3103", "QTD_DIAS_MATR"),
    (COLS_2021, "IDADE_ALUNO_MAR", "QTD_DIAS_MAT"),
    (COLS_2024, "IDADE_ALUNO_MAR", "QTD_DIAS_MAT"),
])
def test_alias_por_epoca(colunas, origem_idade, origem_dias):
    expr = m.expressoes(colunas)
    assert expr["idade_publicada"] == f'"{origem_idade}"'
    assert expr["qtd_dias"] == f'"{origem_dias}"'


def test_bom_no_nome_da_primeira_coluna():
    assert m.expressoes(COLS_2023_BOM)["ano_publicado"] == '"﻿AN_LETIVO"'


def test_deficiencia_com_um_ou_dois_sublinhados():
    assert m.expressoes(COLS_2015)["def_autismo"] == '"DEF_AUTISMO"'
    assert m.expressoes(COLS_2019)["def_autismo"] == '"DEF__AUTISMO"'


def test_coluna_ausente_vira_nulo_tipado():
    expr = m.expressoes(COLS_2019)
    assert expr["def_sindrome_down"] == "CAST(NULL AS VARCHAR)"
    assert m.expressoes(COLS_2024)["def_sindrome_down"] == '"DEF_SINDROME_DOWN"'


def test_todas_as_colunas_canonicas_sempre_presentes():
    for cols in (COLS_2015, COLS_2019, COLS_2021, COLS_2023_BOM, COLS_2024):
        assert set(m.expressoes(cols)) == set(m.COLUNAS_CANONICAS)


def test_deficiencias_cobrem_os_17_indicadores_conhecidos():
    # 13 presentes desde 2015 + surdez unilateral, visão monocular, paralisia cerebral e
    # síndrome de Down, que entram em 2024. 'Não possui' e altas habilidades ficam fora.
    assert len(m.DEFICIENCIAS) == 17
    assert "sindrome_down" in m.DEFICIENCIAS
    assert "nao_possui" not in m.DEFICIENCIAS and "altas_habilidades" not in m.DEFICIENCIAS
    assert "def_nao_possui" in m.COLUNAS_CANONICAS


@pytest.mark.parametrize("nome, esperado", [
    ("Microdados_EOL_Matriculas_Ano_2015.csv", True),
    ("Microdados_Matricula_EOL_Escolarizacao_Outros_2024.csv", True),
    ("Microdados_EOL_Matriculas_Ano_2022_Atividades_Complementares.csv", False),
    ("Microdados_EOL_Matricula_Atividades_Complementares.csv", False),
])
def test_arquivo_de_escolarizacao(nome, esperado):
    assert m.arquivo_eh_escolarizacao(nome) is esperado


def _staging(colunas_e_linhas: dict, ano: int, arquivo: str) -> pd.DataFrame:
    con = duckdb.connect()
    df = pd.DataFrame(colunas_e_linhas)
    con.register("bruto", df)
    return con.execute(m.sql_staging("bruto", ano, arquivo, list(df.columns))).df()


def test_staging_filtra_escolarizacao_pelo_indicador_quando_valido():
    out = _staging({"TURMA_ESCOL": ["S", "N", None], "idade_aluno_31_03": ["5", "6", "7"],
                    "MODALIDADE": ["PRE", "ATCOMP", None]}, 2015, "Microdados_EOL_Matriculas_Ano_2015.csv")
    assert out["idade_publicada"].tolist() == ["5", "7"]   # N sai; nulo depende do arquivo
    assert set(out["ano_letivo"]) == {2015}


def test_staging_2023_ignora_indicador_corrompido_e_usa_o_arquivo():
    # Em 2023 TURMA_ESCOL traz o nome da turma ('4A'), não S/N.
    out = _staging({"TURMA_ESCOL": ["4A", "2B"], "IDADE_ALUNO_MAR": ["4", "2"]},
                   2023, "Microdados_Matricula_EOL_Escolarizacao_Educacao_Infantil_2023.csv")
    assert len(out) == 2


def test_staging_preserva_texto_original_e_registra_arquivo():
    out = _staging({"TURMA_ESCOL": ["S"], "NOME_DISTRITO": ["AGUA RASA "], "DEF__AUTISMO": ["1"]},
                   2019, "Microdados_EOL_Matriculas_Ano_2019.csv")
    linha = out.iloc[0]
    assert linha["distrito"] == "AGUA RASA "          # normalização acontece depois, por tabela de correspondência
    assert linha["def_autismo"] == "1"
    assert linha["arquivo"] == "Microdados_EOL_Matriculas_Ano_2019.csv"
    assert list(out.columns) == ["ano_letivo", "arquivo", *m.COLUNAS_CANONICAS]
