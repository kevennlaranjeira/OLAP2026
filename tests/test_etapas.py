"""Classificação da série em etapa. Casos tirados das combinações reais de
MODALIDADE x MODALIDADE_SEGMENTO x DESC_SERIE dos microdados 2015-2024."""
import pytest

from dw_sme.transformacao import etapas as e


@pytest.mark.parametrize("modalidade, segmento, serie, etapa, especial", [
    ("CRECHE", "CRECHE", "BERCARIO I", "CRECHE", False),
    ("CRECHE", None, "MINI GRUPO II", "CRECHE", False),
    ("PRE", "PRE", "INFANTIL II", "PRE", False),
    ("FUND", "Fund1", "C.II 5.ANO F9", "FUND_I", False),
    ("FUND", "Fund2", "C.II 6.ANO F9", "FUND_II", False),
    ("FUND", "FUN1A4", "C.I 4.ANO F9", "FUND_I", False),
    ("FUND", "FUN5A8", "C.III 9.ANO F9", "FUND_II", False),
    ("FUND", None, "C.III 7.ANO F9", "FUND_II", False),      # sem segmento: usa a série
    ("EJA", "EJA1A4", "MII CIEJA", "EJA_I", False),
    ("EJA", "EJA5A8", "EJA FINAL II", "EJA_II", False),
    ("EJA", None, "EJA BASICA I", "EJA_I", False),
    ("EJA", None, "MIII CIEJA", "EJA_II", False),
    ("MEDIO", "MEDIO", "1A.C.NORMAL", "MEDIO", False),
    ("EDPROF", "EDPROF", "MI - ED PROF", "ED_PROF", False),
    ("MOVA", "MOVA", "MOVA", "MOVA", False),
    ("PROJ", "PROJ", "PROJOVEM", "PROJOVEM", False),
    ("ESPEC", "Fund2", "EEC.III 8.ANO F9", "FUND_II", True),
    ("ESPEC", "PRE", "EE INFANTIL I", "PRE", True),
    ("ESPEC", "ESPEC", "EE 2S MED", "MEDIO", True),
    ("ESPEC", "ESPEC", "EEC.I Biling", "FUND_I", True),
    ("ESPEC", "ESPEC", "EEC.II 4.ANO F9", "FUND_I", True),
    ("ESPEC", "ESPEC", "INFANTIL I E II ESP", "PRE", True),
])
def test_classifica_escolarizacao(modalidade, segmento, serie, etapa, especial):
    c = e.classificar(modalidade, segmento, serie)
    assert c is not None
    assert (c.etapa, c.educacao_especial) == (etapa, especial)


@pytest.mark.parametrize("modalidade", ["ATCOMP", "REC", "SAAI", "OIE", "OSL", "CONVEE", "EDFIS", "EJAQUA", None])
def test_nao_escolarizacao_retorna_none(modalidade):
    assert e.classificar(modalidade, modalidade, modalidade) is None


def test_ciclo_nao_se_aninha_na_etapa():
    # O ciclo interdisciplinar (C.II) cobre 4o, 5o e 6o anos: atravessa a fronteira
    # entre anos iniciais e finais. Por isso ciclo e etapa são hierarquias paralelas.
    quarto = e.classificar("FUND", "Fund1", "C.II 4.ANO F9")
    sexto = e.classificar("FUND", "Fund2", "C.II 6.ANO F9")
    assert quarto.ciclo == sexto.ciclo == "INTERDISCIPLINAR"
    assert quarto.etapa != sexto.etapa


@pytest.mark.parametrize("serie, ciclo", [
    ("C.I 1.ANO F9", "ALFABETIZACAO"),
    ("EEC.I 3.ANO F9", "ALFABETIZACAO"),
    ("C.III 9.ANO F9", "AUTORAL"),
    ("BERCARIO I", None),
])
def test_ciclo(serie, ciclo):
    modalidade = "FUND" if "ANO" in serie else "CRECHE"
    assert e.classificar(modalidade, None, serie).ciclo == ciclo


def test_ordem_da_serie_no_fundamental():
    assert e.classificar("FUND", "Fund2", "C.III 7.ANO F9").ordem_serie == 7


def test_serie_normalizada():
    assert e.classificar("FUND", "Fund1", "  c.i 1.ano f9 ").serie == "C.I 1.ANO F9"


def test_catalogo_de_etapas_e_coerente():
    codigos = [x.codigo for x in e.ETAPAS]
    assert len(codigos) == len(set(codigos))
    # toda etapa usada pela planilha de fila existe no catálogo
    assert set(e.ETAPA_DA_COLUNA_FILA.values()) <= set(codigos)
    # ordem de exibição sem repetição
    assert len({x.ordem for x in e.ETAPAS}) == len(e.ETAPAS)
    # nível e nome preenchidos
    assert all(x.nome and x.nivel for x in e.ETAPAS)
