"""As consultas rodam sobre o DW e o modelo as suporta (Observação 2 do enunciado)."""
import duckdb
import pytest

from dw_sme.carga import carregar
from dw_sme.config import Configuracao
from dw_sme.consultas import executar as ex


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    from conftest import _gravar, microdado_2019, microdado_2021, microdado_2023, FIXTURES
    import shutil
    raiz = tmp_path_factory.mktemp("consultas")
    dados = raiz / "data"
    bruto = dados / "interim" / "bruto"
    _gravar(microdado_2019(), bruto / "ano=2019" / "Microdados_EOL_Matriculas_Ano_2019.parquet")
    _gravar(microdado_2021(), bruto / "ano=2021" / "Microdados_EOL_Matriculas_Ano_2021.parquet")
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


def consulta(codigo):
    return next(c for c in ex.listar() if c.codigo == codigo)


def test_cobre_os_tipos_exigidos_pelo_enunciado():
    consultas = ex.listar()
    assert len(consultas) >= 5
    tipos = [c.tipo for c in consultas]
    assert ex.TIPOS_EXIGIDOS <= set(tipos)
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
    assert set(r["mes_referencia"]) == {"2024-04"}


def test_c2_total_do_ano_igual_a_soma_das_etapas(con):
    r = ex.executar(con, consulta("C2"))
    totais = dict(r[r.agregacao == "TOTAL DO ANO"][["ano", "matriculas"]].values.tolist())
    assert totais == {2019: 3, 2021: 2, 2023: 2}
    etapas_2019 = r[(r.ano == 2019) & (r.agregacao == "ETAPA")]["matriculas"].sum()
    assert etapas_2019 == 3


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
    assert {"matriculas", "fila_junho", "abandonos", "taxa_abandono"} <= set(r.columns)
    linha = r[(r.ano == 2019) & (r.dre == "PENHA")].iloc[0]
    assert linha["matriculas"] == 2 and linha["abandonos"] == 1
    assert linha["taxa_abandono"] == pytest.approx(0.5)


def test_executar_todas_grava_csv(con, tmp_path):
    banco = con.execute("select path from duckdb_databases() where database_name not in ('system', 'temp')").fetchone()[0]
    resultados = ex.executar_todas(banco, tmp_path / "saida")
    assert set(resultados) == {c.codigo for c in ex.listar()}
    assert len(list((tmp_path / "saida").glob("*.csv"))) == len(resultados)


def test_cabecalho_incompleto_e_recusado():
    with pytest.raises(ValueError, match="cabeçalho"):
        ex._ler("x.sql", "-- codigo: X\n-- tipo: pivot\nSELECT 1")
