"""As consultas rodam sobre o DW e o modelo as suporta (Observação 2 do enunciado)."""
import duckdb
import pandas as pd
import pytest

from dw_sme.carga import carregar
from dw_sme.config import Configuracao
from dw_sme.consultas import executar as ex


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    import shutil

    from conftest import FIXTURES, _gravar, gravar_ibge, microdado_2021, microdado_2023
    raiz = tmp_path_factory.mktemp("consultas")
    dados = raiz / "data"
    bruto = dados / "interim" / "bruto"
    _gravar(microdado_2019_com_fundamental(), bruto / "ano=2019" / "Microdados_EOL_Matriculas_Ano_2019.parquet")
    _gravar(microdado_2021(), bruto / "ano=2021" / "Microdados_EOL_Matriculas_Ano_2021.parquet")
    _gravar(microdado_2022(), bruto / "ano=2022" / "Microdados_EOL_Matriculas_Ano_2022.parquet")
    gravar_ibge(dados / "raw" / "ibge")
    infantil, _ = microdado_2023()
    _gravar(infantil, bruto / "ano=2023" / "Microdados_Matricula_EOL_Escolarizacao_Educacao_Infantil_2023.parquet")
    (dados / "raw" / "demanda").mkdir(parents=True)
    for f in (FIXTURES / "fila").glob("*.csv"):
        shutil.copy(f, dados / "raw" / "demanda" / f.name)
    cfg = Configuracao(dir_dados=dados, banco=raiz / "dw_consultas.duckdb", log=lambda *_: None)
    carregar.carregar_tudo(cfg)
    c = duckdb.connect(str(cfg.banco), read_only=True)
    yield c
    c.close()


def microdado_2019_com_fundamental():
    """2019 sintético mais duas matrículas de fundamental numa EMEF da DRE Penha (uma aprovada, uma abandono)."""
    from conftest import _linha, microdado_2019
    emef = {"CD_UNIDADE_EDUCACAO": "000123", "NOME_ESCOLA": "MARIO COVAS, GOV.", "TIPO_ESCOLA": "EMEF",
            "NOME_DISTRITO": "AGUA RASA", "DRE": "PENHA", "CD_SETOR": "1001", "CD_INEP_ESCOLA": "35000123",
            "SITUACAO_ESCOLA": "ATIVA"}
    turma = {"CD_TURMA": "777", "NOME_TURMA": "6D", "CD_TURNO": "01", "DESC_TURNO": "MANHA",
             "HORA_IN_TURMA": "0700", "HORA_FIM_TURMA": "1200", "TURMA_ESCOL": "S"}
    serie = {"MODALIDADE": "FUND", "MODALIDADE_SEGMENTO": "Fund2", "DESC_SERIE": "C.II 6.ANO F9", "CD_SERIE": "2096"}
    extra = [_linha(2019, emef, turma, serie, {"nasc": "2008", "mat": "300"}, "APROV", IDADE_ALUNO_3103="11"),
             _linha(2019, emef, turma, serie, {"nasc": "2008", "mat": "301"}, "ABAND", IDADE_ALUNO_3103="11")]
    return pd.concat([microdado_2019(), pd.DataFrame(extra)], ignore_index=True)


def microdado_2022():
    """Ano do Censo: três crianças de 0 a 4 anos, uma delas com matrícula encerrada antes de 31/07."""
    from conftest import CRECHE_INTEGRAL, ESCOLA_A_2019, ESCOLA_B_2019, PRE_TARDE, SERIE_CRECHE, SERIE_PRE, _linha
    linhas = [
        _linha(2022, ESCOLA_A_2019, CRECHE_INTEGRAL, SERIE_CRECHE, {"nasc": "2019", "mes": "5", "mat": "400"}, "ATIVO",
               IDADE_ALUNO_MAR="2", DT_IN_MAT="2022-02-07 00:00:00"),
        _linha(2022, ESCOLA_A_2019, CRECHE_INTEGRAL, SERIE_CRECHE, {"nasc": "2019", "mes": "1", "mat": "401"}, "TRANSF",
               IDADE_ALUNO_MAR="3", DT_IN_MAT="2022-02-07 00:00:00", DT_FIM_MAT="2022-05-10 00:00:00"),
        _linha(2022, ESCOLA_B_2019, PRE_TARDE, SERIE_PRE, {"nasc": "2017", "mes": "6", "mat": "402"}, "ATIVO",
               IDADE_ALUNO_MAR="4", DT_IN_MAT="2022-02-07 00:00:00"),
    ]
    return pd.DataFrame(linhas)


def consulta(codigo):
    return next(c for c in ex.listar() if c.codigo == codigo)


def test_cobre_os_tipos_exigidos_pelo_enunciado():
    consultas = ex.listar()
    assert len(consultas) >= 5
    tipos = [c.tipo for c in consultas]
    assert set(tipos) >= ex.TIPOS_EXIGIDOS
    assert sum(t in ("roll-up", "drill-down") for t in tipos) >= 2
    assert all(c.pergunta and c.justificativa for c in consultas)


def test_drill_across_usa_mais_de_um_fato():
    for c in ex.listar():
        if c.tipo == "drill-across":
            assert len(c.fatos) >= 2
            for f in c.fatos:
                assert f"dw.{f}" in c.sql


def test_c1_municipio_igual_a_soma_dos_distritos(con):
    r = ex.executar(con, consulta("C1"))
    municipio = r[r.nivel == "MUNICIPIO"]["criancas_na_fila"].iloc[0]
    assert municipio == r[r.nivel == "DISTRITO"]["criancas_na_fila"].sum() == 55   # abr/2024: 27 + 4 + 24
    assert set(r[r.nivel == "DRE"]["dre"]) == {"PENHA", "PIRITUBA/JARAGUA", "BUTANTA"}
    assert r[r.nivel == "MUNICIPIO"]["dre"].tolist() == ["(TODAS)"]   # total, não falta de DRE
    assert set(r["mes_referencia"]) == {"2024-04"}


def test_c2_total_do_ano_igual_a_soma_das_etapas(con):
    r = ex.executar(con, consulta("C2"))
    totais = dict(r[r.agregacao == "TOTAL DO ANO"][["ano", "matriculas"]].values.tolist())
    assert totais == {2019: 5, 2021: 2, 2022: 3, 2023: 2}
    etapas_2019 = r[(r.ano == 2019) & (r.agregacao == "ETAPA")]["matriculas"].sum()
    assert etapas_2019 == 5


def test_c3_fatia_creche_e_corta_anos(con):
    r = ex.executar(con, consulta("C3"))
    assert set(r["ano"]) == {2019, 2023}
    assert set(r["rede"]) == {"CONVENIADA"}
    assert set(r["jornada"]) == {"INTEGRAL"}


def test_c4_jornada_vira_coluna(con):
    r = ex.executar(con, consulta("C4"))
    assert "dre" in r.columns
    assert {"PARCIAL DIURNO", "INTEGRAL"} <= set(r.columns)
    assert int(r.drop(columns="dre").sum().sum()) == 2      # 2023 tem duas matrículas


def test_c5_une_fila_e_matricula_pelas_dimensoes_conformadas(con):
    r = ex.executar(con, consulta("C5"))
    assert {"fila", "matriculas_planilha", "matriculas_ativas_em_junho", "matriculas_no_ano",
            "fracao_fora", "divergencia_entre_bases"} <= set(r.columns)
    com_fila = r[r.fila.notna() & r.matriculas_planilha.notna()]
    esperado = com_fila.fila / (com_fila.fila + com_fila.matriculas_planilha)
    assert (com_fila.fracao_fora - esperado.round(4)).abs().max() < 1e-9
    so_fila = r[r.matriculas_no_ano.isna()]
    so_matricula = r[r.fila.isna()]
    assert len(so_fila) > 0 and len(so_matricula) > 0       # outer join preserva os dois lados
    assert set(r["etapa"]) <= {"CRECHE", "PRE"}


def test_c6_cruza_tres_fatos_por_dre(con):
    r = ex.executar(con, consulta("C6"))
    assert {"matriculas_creche", "fila_creche_junho", "abandonos_fundamental",
            "taxa_abandono_fundamental"} <= set(r.columns)
    penha = r[(r.ano == 2019) & (r.dre == "PENHA")].iloc[0]
    # o abandono da pré-escola sintética (EMEI) não entra: só o fundamental conta
    assert penha["abandonos_fundamental"] == 1 and penha["taxa_abandono_fundamental"] == pytest.approx(0.5)
    pirituba = r[(r.ano == 2019) & (r.dre == "PIRITUBA/JARAGUA")].iloc[0]
    assert pirituba["matriculas_creche"] == 1


def test_c7_cruza_populacao_matricula_e_fila_por_distrito(con):
    r = ex.executar(con, consulta("C7")).set_index("distrito")
    assert "NAO INFORMADO" not in r.index
    agua_rasa = r.loc["AGUA RASA"]
    assert agua_rasa["criancas_0_4_residentes"] == 45
    assert agua_rasa["matriculas_0_4_ativas"] == 1          # a transferida em maio não conta em 31/07
    assert agua_rasa["mes_fila"] == "2020-09"               # último mês publicado até a data do Censo
    fila = con.execute("""select sum(f.qtd_demanda_total) from dw.fato_fila f join dw.dim_tempo t using (chave_tempo)
                          join dw.dim_territorio d using (chave_territorio) join dw.dim_etapa e using (chave_etapa)
                          where t.ano_mes = '2020-09' and d.distrito = 'AGUA RASA'
                            and e.codigo in ('CRECHE', 'PRE')""").fetchone()[0]
    assert agua_rasa["fila_creche_pre"] == fila
    assert agua_rasa["matriculas_por_100_criancas"] == pytest.approx(round(100 / 45, 1))
    assert agua_rasa["fila_por_mil_criancas"] == pytest.approx(round(1000 * fila / 45, 1))
    assert r.loc["ANHANGUERA", "matriculas_0_4_ativas"] == 1
    assert pd.isna(r.loc["ALTO DE PINHEIROS", "matriculas_0_4_ativas"])


def test_c8_media_por_turma_recalculada_em_cada_nivel(con):
    r = ex.executar(con, consulta("C8"))
    assert set(r["ano"]) == {2019, 2023}
    pre_2019 = r[(r.ano == 2019) & (r.etapa == "PRE-ESCOLA")]
    municipio = pre_2019[pre_2019.nivel == "MUNICIPIO"].iloc[0]
    assert municipio["dre"] == "(TODAS)"
    assert municipio["turmas_ativas_junho"] == 1 and municipio["alunos_ativos_junho"] == 1
    assert municipio["alunos_por_turma"] == pytest.approx(1.0)
    for ano, etapa in r[["ano", "etapa"]].drop_duplicates().itertuples(index=False):
        bloco = r[(r.ano == ano) & (r.etapa == etapa)]
        topo = bloco[bloco.nivel == "MUNICIPIO"]["alunos_ativos_junho"].sum()
        assert topo == bloco[bloco.nivel == "DISTRITO"]["alunos_ativos_junho"].sum()


def test_executar_todas_grava_csv(con, tmp_path):
    banco = con.execute("select path from duckdb_databases() where database_name not in ('system', 'temp')").fetchone()[0]
    resultados = ex.executar_todas(banco, tmp_path / "saida")
    assert set(resultados) == {c.codigo for c in ex.listar()}
    assert len(list((tmp_path / "saida").glob("*.csv"))) == len(resultados)
    c1 = (tmp_path / "saida" / "c1_drill_down_fila_territorio.csv").read_text(encoding="utf-8")
    assert ",55\n" in c1 and ".0\n" not in c1          # contagem sai como inteiro no CSV


def test_cabecalho_incompleto_e_recusado():
    with pytest.raises(ValueError, match="cabeçalho"):
        ex._ler("x.sql", "-- codigo: X\n-- tipo: pivot\nSELECT 1")
