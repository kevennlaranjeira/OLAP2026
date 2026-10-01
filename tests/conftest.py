"""Dados sintéticos com o formato dos arquivos reais, para os testes de carga, qualidade e consultas."""
from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path

import duckdb
import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures"

SIT = ["SIT_AL_APROV", "SIT_AL_REPROV", "SIT_AL_ABAND", "SIT_AL_CONCL", "SIT_AL_TRANSF", "SIT_AL_FALEC",
       "SIT_AL_NCOM", "SIT_AL_EXCL", "SIT_AL_CES", "SIT_AL_REMAN", "SIT_AL_RECLAS", "SIT_AL_ATIVO"]


def _linha(ano, escola, turma, serie, aluno, desfecho="APROV", **extra):
    """Uma matrícula no formato do microdado. `escola` e `turma` são dicionários com os campos de origem."""
    base = {
        "AN_LETIVO": str(ano), **escola, **turma, **serie,
        "ANO_NASC_ALUNO": aluno.get("nasc", "2015"), "MES_NASC_ALUNO": aluno.get("mes", "5"),
        "CD_SEXO": aluno.get("sexo", "F"), "DESC_RACA_COR": aluno.get("raca", "PARDA"),
        "NEE_ALT_HAB": "0", "DEF__AUTISMO": aluno.get("autismo", "0"), "DEF__N_POSSUI": "1",
        "CD_MAT": aluno.get("mat", "1"), "SITUACAO_MAT": "CONCLUIDO",
        **{c: "0" for c in SIT},
    }
    base[f"SIT_AL_{desfecho}"] = "1"
    base.update(extra)
    return base


ESCOLA_A_2019 = {"CD_UNIDADE_EDUCACAO": "019459", "NOME_ESCOLA": "UNIAO DE VILA NOVA I", "TIPO_ESCOLA": "EMEI        ",
                 "NOME_DISTRITO": "AGUA RASA", "DRE": "DIRETORIA REGIONAL DE EDUCACAO PENHA", "CD_SETOR": "1001",
                 "CD_INEP_ESCOLA": "35443220", "SITUACAO_ESCOLA": "ATIVA"}
ESCOLA_B_2019 = {"CD_UNIDADE_EDUCACAO": "308775", "NOME_ESCOLA": "AQUARELA", "TIPO_ESCOLA": "CR.P.CONV   ",
                 "NOME_DISTRITO": "ANHANGUERA", "DRE": "DIRETORIA REGIONAL DE EDUCACAO PIRITUBA/JARAGUA",
                 "CD_SETOR": "4205", "CD_INEP_ESCOLA": "35271056", "SITUACAO_ESCOLA": "ATIVA"}

PRE_TARDE = {"CD_TURMA": "1882314", "NOME_TURMA": "2A", "CD_TURNO": "03", "DESC_TURNO": "TARDE",
             "HORA_IN_TURMA": "1300", "HORA_FIM_TURMA": "1900", "TURMA_ESCOL": "S"}
CRECHE_INTEGRAL = {"CD_TURMA": "1900001", "NOME_TURMA": "3F", "CD_TURNO": "06", "DESC_TURNO": "INTEGRAL",
                   "HORA_IN_TURMA": "0700", "HORA_FIM_TURMA": "1700", "TURMA_ESCOL": "S"}
SERIE_PRE = {"MODALIDADE": "PRE", "MODALIDADE_SEGMENTO": "PRE", "DESC_SERIE": "INFANTIL II", "CD_SERIE": "00274"}
SERIE_CRECHE = {"MODALIDADE": "CRECHE", "MODALIDADE_SEGMENTO": "CRECHE", "DESC_SERIE": "MINI GRUPO II", "CD_SERIE": "00267"}
ATCOMP = {"MODALIDADE": "ATCOMP", "MODALIDADE_SEGMENTO": "ATCOMP", "DESC_SERIE": "ATCOMP", "CD_SERIE": "20286"}


def microdado_2019() -> pd.DataFrame:
    linhas = [
        _linha(2019, ESCOLA_A_2019, PRE_TARDE, SERIE_PRE, {"nasc": "2014", "mes": "2", "mat": "100"}, "APROV",
               IDADE_ALUNO_3103="5", QTD_DIAS_MATR="200", DT_IN_MAT="2019-02-04 00:00:00", DT_FIM_MAT="2019-12-20 00:00:00"),
        _linha(2019, ESCOLA_A_2019, PRE_TARDE, SERIE_PRE, {"nasc": "2014", "mes": "8", "mat": "101", "sexo": "M"}, "ABAND",
               IDADE_ALUNO_3103="4", QTD_DIAS_MATR="90", DT_IN_MAT="2019-02-04 00:00:00", DT_FIM_MAT="2019-06-10 00:00:00"),
        _linha(2019, ESCOLA_B_2019, CRECHE_INTEGRAL, SERIE_CRECHE, {"nasc": "2016", "mes": "3", "mat": "102", "autismo": "1"},
               "CONCL", IDADE_ALUNO_3103="3", QTD_DIAS_MATR="210", DT_IN_MAT="2019-02-04 00:00:00",
               DT_FIM_MAT="2019-12-20 00:00:00"),
        # atividade complementar: TURMA_ESCOL = N, não entra
        _linha(2019, ESCOLA_A_2019, {**PRE_TARDE, "TURMA_ESCOL": "N"}, ATCOMP, {"mat": "103"}, "ATIVO",
               IDADE_ALUNO_3103="9", QTD_DIAS_MATR="30"),
    ]
    return pd.DataFrame(linhas)


def microdado_2021() -> pd.DataFrame:
    """2021: descrição do turno vazia, código 4-9, sem datas nem dias de matrícula."""
    a = {**ESCOLA_A_2019, "CD_UNIDADE_EDUCACAO": "19459", "TIPO_ESCOLA": "EMEI", "DRE": "PENHA"}
    b = {**ESCOLA_B_2019, "NOME_ESCOLA": "MARGARIDA", "DRE": "PIRITUBA/JARAGUA"}   # troca de nome
    turma_a = {**PRE_TARDE, "CD_TURNO": "6", "DESC_TURNO": None}                     # 6 = tarde em 2021
    turma_b = {**CRECHE_INTEGRAL, "CD_TURNO": "9", "DESC_TURNO": None}               # 9 = integral em 2021
    linhas = [
        _linha(2021, a, turma_a, SERIE_PRE, {"nasc": "2016", "mes": "1", "mat": "200"}, "APROV",
               IDADE_ALUNO_MAR="5", Hora_Inicio="1300"),
        _linha(2021, b, turma_b, SERIE_CRECHE, {"nasc": "2018", "mes": "7", "mat": "201"}, "REPROV",
               IDADE_ALUNO_MAR=None, Hora_Inicio="0700"),
    ]
    return pd.DataFrame(linhas)


def microdado_2023() -> tuple[pd.DataFrame, pd.DataFrame]:
    """2023: código destruído (colide entre escolas), TURMA_ESCOL com o nome da turma, desfecho em curso."""
    a = {**ESCOLA_A_2019, "CD_UNIDADE_EDUCACAO": "9209610000000000", "TIPO_ESCOLA": "EMEI", "DRE": "PENHA",
         "CD_SETOR": "8244830000000"}
    nova = {"CD_UNIDADE_EDUCACAO": "9209610000000000", "NOME_ESCOLA": "NOVA ESPERANCA", "TIPO_ESCOLA": "CEI INDIRET",
            "NOME_DISTRITO": "ALTO DE PINHEIROS", "DRE": "BUTANTA", "CD_SETOR": "8244830000000",
            "CD_INEP_ESCOLA": "92755800000000000", "SITUACAO_ESCOLA": "Ativa"}
    turma_a = {**PRE_TARDE, "DESC_TURNO": "Tarde", "TURMA_ESCOL": "2A", "CD_TURNO": "93911283491"}
    turma_n = {**CRECHE_INTEGRAL, "DESC_TURNO": "Integral", "TURMA_ESCOL": "3F", "CD_TURNO": "6361983595"}
    infantil = [
        _linha(2023, a, turma_a, SERIE_PRE, {"nasc": "2018", "mes": "11", "mat": "0"}, "ATIVO", IDADE_ALUNO_MAR="4",
               QTD_DIAS_MAT="150", DT_IN_MAT="2023-02-06 00:00:00"),
        _linha(2023, nova, turma_n, SERIE_CRECHE, {"nasc": "2021", "mes": "4", "mat": "0", "raca": "N�O DECLARADA"},
               "ATIVO", IDADE_ALUNO_MAR="1", QTD_DIAS_MAT="150", DT_IN_MAT="2023-02-06 00:00:00"),
    ]
    complementar = [
        _linha(2023, a, turma_a, ATCOMP, {"mat": "0"}, "ATIVO", IDADE_ALUNO_MAR="7"),
    ]
    return pd.DataFrame(infantil), pd.DataFrame(complementar)


# Censo 2022 sintético no layout dos Agregados por Setores (temas Básico e Demografia).
# Códigos de setor de 15 dígitos; os de São Paulo começam por 3550308.
IBGE_BASICO = [
    ("355030801000001", "3550308", "São Paulo", "Água Rasa"),
    ("355030801000002", "3550308", "São Paulo", "Água Rasa"),
    ("355030802000001", "3550308", "São Paulo", "Alto de Pinheiros"),
    ("355030803000001", "3550308", "São Paulo", "Anhanguera"),
    ("355030899000001", "3550308", "São Paulo", "Distrito Sintético"),     # sem correspondente na SME
    ("350010505000001", "3500105", "Adamantina", "Adamantina"),            # outro município: fica fora
]
# CD_SETOR -> V01031 ... V01041 (0 a 4, 5 a 9, ..., 70 ou mais); 'X' = valor não publicado
IBGE_DEMOGRAFIA = {
    "355030801000001": [30, 25, 20, 22, 30, 31, 60, 55, 50, 40, 35],
    "355030801000002": [10, 12, 11, 9, 14, 15, 30, 28, 22, 18, 12],
    "355030801000003": [5, 4, "X", 3, 6, 6, 10, 9, 8, 7, 5],             # ausente do Básico: herda o distrito
    "355030802000001": [8, 9, 10, 12, 15, 16, 30, 30, 28, 25, 30],
    "355030803000001": [40, 35, 30, 28, 30, 33, 55, 45, 35, 20, 10],
    "355030899000001": [1] * 11,
    "350010505000001": [99] * 11,
}
POPULACAO_0_4 = {"AGUA RASA": 45, "ALTO DE PINHEIROS": 8, "ANHANGUERA": 40}


def gravar_ibge(destino: Path) -> None:
    """Tema Básico num .zip (latin-1, ';') e Demografia em .csv (UTF-8, ',', 'CD_setor' em caixa mista)."""
    destino.mkdir(parents=True, exist_ok=True)
    basico = "CD_SETOR;CD_MUN;NM_MUN;NM_DIST;v0001\n" + "".join(
        f"{s};{m};{nm};{d};10\n" for s, m, nm, d in IBGE_BASICO)
    with zipfile.ZipFile(destino / "Agregados_por_setores_basico_BR.zip", "w") as z:
        z.writestr("Agregados_por_setores_basico_BR.csv", basico.encode("latin-1"))
    variaveis = [f"V{1031 + i:05d}" for i in range(11)]
    linhas = ["CD_setor,V01006," + ",".join(variaveis)]
    for setor, valores in IBGE_DEMOGRAFIA.items():
        linhas.append(f"{setor},999," + ",".join(str(v) for v in valores))
    (destino / "Agregados_por_setores_demografia_BR.csv").write_bytes(("\n".join(linhas) + "\n").encode("utf-8"))


def zip_em_memoria(arquivos: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for nome, conteudo in arquivos.items():
            z.writestr(nome, conteudo)
    return buffer.getvalue()


def _gravar(df: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.register("df", df.astype("string"))
    con.execute(f"copy (select * from df) to '{caminho.as_posix()}' (format parquet)")


@pytest.fixture
def dados_sinteticos(tmp_path) -> Path:
    """Árvore data/ mínima: bruto dos microdados (3 anos), planilhas de fila de exemplo e Censo 2022 sintético."""
    dados = tmp_path / "data"
    bruto = dados / "interim" / "bruto"
    _gravar(microdado_2019(), bruto / "ano=2019" / "Microdados_EOL_Matriculas_Ano_2019.parquet")
    _gravar(microdado_2021(), bruto / "ano=2021" / "Microdados_EOL_Matriculas_Ano_2021.parquet")
    infantil, complementar = microdado_2023()
    _gravar(infantil, bruto / "ano=2023" / "Microdados_Matricula_EOL_Escolarizacao_Educacao_Infantil_2023.parquet")
    _gravar(complementar, bruto / "ano=2023" / "Microdados_EOL_Matricula_Atividades_Complementares.parquet")
    fila = dados / "raw" / "demanda"
    fila.mkdir(parents=True)
    for f in (FIXTURES / "fila").glob("*.csv"):
        shutil.copy(f, fila / f.name)
    gravar_ibge(dados / "raw" / "ibge")
    return dados
