"""Regras de normalização. Cada caso vem de uma grafia encontrada nos dados reais."""
import pytest

from dw_sme.transformacao import normalizacao as n


class TestTexto:
    def test_remove_acento_espaco_e_caixa(self):
        assert n.texto("  São   Miguel ") == "SAO MIGUEL"

    def test_nulo_e_vazio_viram_none(self):
        assert n.texto(None) is None
        assert n.texto("   ") is None

    def test_nan_do_pandas_vira_none_e_nao_o_texto_nan(self):
        # Caso real: escola em branco em 2020 virava uma escola chamada "NAN"
        assert n.texto(float("nan")) is None
        assert n.inteiro_br(float("nan")) is None

    def test_caractere_de_substituicao_de_latin1_mal_lido(self):
        # 'NÃO DECLARADA' lido com encoding errado chega como 'N\ufffdO DECLARADA'
        assert n.texto("N\ufffdO DECLARADA") == "NAO DECLARADA"


class TestInteiroBr:
    @pytest.mark.parametrize("bruto, esperado", [
        ("1.188", 1188),        # ponto de milhar da planilha de fila
        ("326.048", 326048),
        ("337022", 337022),     # set/2019 vem sem ponto
        ("5,00", 5),            # idade de 2020 vem com vírgula decimal
        ("0", 0),
        (" 12 ", 12),
    ])
    def test_converte(self, bruto, esperado):
        assert n.inteiro_br(bruto) == esperado

    @pytest.mark.parametrize("bruto", [None, "", "  ", "abc", "1,32551E+13"])
    def test_invalido_vira_none(self, bruto):
        assert n.inteiro_br(bruto) is None


class TestDistrito:
    def test_espaco_sobrando_da_planilha_de_fila(self):
        assert n.distrito("AGUA RASA ") == "AGUA RASA"

    def test_acento_e_caixa(self):
        assert n.distrito("Água Rasa") == "AGUA RASA"


class TestDre:
    @pytest.mark.parametrize("bruto", [
        "DIRETORIA REGIONAL DE EDUCACAO PIRITUBA/JARAGUA",
        "PIRITUBA/JARAGUA",
        "PIRITUBA",
    ])
    def test_pirituba_em_tres_grafias(self, bruto):
        assert n.dre(bruto) == "PIRITUBA/JARAGUA"

    def test_prefixo_removido(self):
        assert n.dre("DIRETORIA REGIONAL DE EDUCACAO SAO MIGUEL") == "SAO MIGUEL"

    def test_todas_as_treze_dres_sao_reconhecidas(self):
        assert len(n.DRES) == 13
        for d in n.DRES:
            assert n.dre(d) == d

    def test_valor_desconhecido_vira_none(self):
        assert n.dre("DRE INEXISTENTE") is None


class TestTipoEscola:
    @pytest.mark.parametrize("bruto, esperado", [
        ("CR.P.CONV   ", "CR.P.CONV"),
        ("CEI INDIRET", "CEI INDIR"),
        ("CEIINDIR", "CEI INDIR"),
        ("CEI DIRET", "CEI DIRET"),
        ("CCI-CIPS", "CCI/CIPS"),
        ("CEU AT COMPL", "CEU AT COMPL"),
        ("CEUATCOM", "CEU AT COMPL"),
        ("ETECNICA", "E TECNICA"),
        ("ETEC", "E TECNICA"),
        ("ET", "E TECNICA"),
        ("EMEF        ", "EMEF"),
        ("EMEI P FOM", "EMEI P FOM"),
    ])
    def test_variantes(self, bruto, esperado):
        assert n.tipo_escola(bruto) == esperado

    def test_desconhecido_preserva_texto_normalizado(self):
        assert n.tipo_escola("tipo novo") == "TIPO NOVO"


class TestRede:
    @pytest.mark.parametrize("tipo, rede", [
        ("CR.P.CONV", "CONVENIADA"),
        ("CEI INDIR", "CONVENIADA"),
        ("ESP CONV", "CONVENIADA"),
        ("MOVA", "CONVENIADA"),
        ("EMEF", "DIRETA"),
        ("CEU EMEI", "DIRETA"),
        ("CCA", "OUTRAS SECRETARIAS"),
        ("E TECNICA", "OUTRAS SECRETARIAS"),
        ("ESC.PART.", "PARTICULAR"),
        (None, "NAO INFORMADA"),
    ])
    def test_classifica(self, tipo, rede):
        assert n.rede(tipo) == rede


class TestTurno:
    @pytest.mark.parametrize("bruto, esperado", [
        ("Manh\ufffd", "MANHA"),
        ("MANHA", "MANHA"),
        ("Intermedi\ufffdrio", "INTERMEDIARIO"),
        ("Integral            ", "INTEGRAL"),
        ("Vespertino", "VESPERTINO"),
        ("NOITE", "NOITE"),
        (None, None),
    ])
    def test_descricao(self, bruto, esperado):
        assert n.turno(bruto) == esperado

    @pytest.mark.parametrize("codigo, esperado", [
        ("4", "MANHA"), ("5", "INTERMEDIARIO"), ("6", "TARDE"),
        ("7", "VESPERTINO"), ("8", "NOITE"), ("9", "INTEGRAL"),
        ("1", None), (None, None),
    ])
    def test_codigo_de_2021(self, codigo, esperado):
        # Em 2021 a descrição vem vazia e o código é o de 2020 somado de 3
        assert n.turno_codigo_2021(codigo) == esperado

    @pytest.mark.parametrize("inicio, fim, esperado", [
        ("700", "1700", "INTEGRAL"),
        ("0700", "1200", "MANHA"),
        ("700", "1300", "MANHA"),
        ("1330", "1830", "TARDE"),
        ("1300", "1900", "TARDE"),
        ("1900", "2300", "NOITE"),
        ("800", "1600", "INTEGRAL"),
        ("x", "1200", None),
        (None, None, None),
    ])
    def test_por_horario(self, inicio, fim, esperado):
        assert n.turno_por_horario(inicio, fim) == esperado

    @pytest.mark.parametrize("turno, jornada", [
        ("MANHA", "PARCIAL DIURNO"), ("TARDE", "PARCIAL DIURNO"),
        ("INTERMEDIARIO", "PARCIAL DIURNO"), ("VESPERTINO", "PARCIAL DIURNO"),
        ("NOITE", "NOTURNO"), ("INTEGRAL", "INTEGRAL"), (None, "NAO INFORMADA"),
    ])
    def test_jornada(self, turno, jornada):
        assert n.jornada(turno) == jornada


class TestPessoa:
    @pytest.mark.parametrize("bruto, esperado", [
        ("NAO DECLARADA", "NAO DECLARADA"),
        ("N\ufffdO DECLARADA", "NAO DECLARADA"),
        ("NÃO DECLARADA", "NAO DECLARADA"),
        ("RECUSOU INFORMA", "RECUSOU INFORMAR"),
        ("INDIGENA", "INDIGENA"),
        ("Parda", "PARDA"),
        (None, "NAO INFORMADA"),
    ])
    def test_raca(self, bruto, esperado):
        assert n.raca_cor(bruto) == esperado

    @pytest.mark.parametrize("bruto, esperado", [
        ("F", "FEMININO"), ("m", "MASCULINO"), (None, "NAO INFORMADO"), ("X", "NAO INFORMADO"),
    ])
    def test_sexo(self, bruto, esperado):
        assert n.sexo(bruto) == esperado


class TestSituacaoEscola:
    @pytest.mark.parametrize("bruto, esperado", [
        ("ATIVA", "ATIVA"), ("Ativa", "ATIVA"), ("ESC PARALI", "PARALISADA"),
        ("Escola Paralisada", "PARALISADA"), ("EXTINTA", "EXTINTA"),
        ("CRIADA", "CRIADA"), (None, "NAO INFORMADA"),
    ])
    def test_situacao(self, bruto, esperado):
        assert n.situacao_escola(bruto) == esperado
