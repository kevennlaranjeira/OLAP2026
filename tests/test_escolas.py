"""Identidade das escolas entre anos e versões da dimensão Escola (SCD tipo 2).

O cenário sintético reproduz as situações medidas nos dados reais:
códigos íntegros com zeros à esquerda variáveis (2015-2021), códigos
embaralhados mas um para um no ano (2022), códigos destruídos em notação
científica (2023-2024), homônimos, escola nova e conveniada que troca de nome.
"""
import pandas as pd
import pytest

from dw_sme.transformacao import escolas as e

COLUNAS = ["ano", "cd_origem", "nome", "tipo", "distrito", "dre", "setor", "situacao", "matriculas"]
DRE_LONGA = "DIRETORIA REGIONAL DE EDUCACAO SAO MIGUEL"


def cenario() -> pd.DataFrame:
    linhas = [
        # escola estável: zeros à esquerda variam entre anos; DRE muda só de grafia
        (2020, "019459", "UNIAO DE VILA NOVA I", "EMEI        ", "VILA JACUI", DRE_LONGA, "8701", "ATIVA", 300),
        (2021, "19459", "UNIAO DE VILA NOVA I", "EMEI", "VILA JACUI", "SAO MIGUEL", "8701", "Ativa", 310),
        (2022, "9209611322271640", "UNIAO DE VILA NOVA I", "EMEI", "VILA JACUI", "SAO MIGUEL", "1204430072353", "Ativa", 305),
        (2023, "9,20961E+15", "UNIAO DE VILA NOVA I", "EMEI", "VILA JACUI", "SAO MIGUEL", "8,24483E+12", "Ativa", 290),
        # conveniada que troca de nome mantendo o código
        (2020, "308775", "AQUARELA", "CR.P.CONV", "JARAGUA", "PIRITUBA", "4205", "ATIVA", 80),
        (2021, "308775", "MARGARIDA", "CR.P.CONV", "JARAGUA", "PIRITUBA/JARAGUA", "4205", "Ativa", 82),
        # homônimos: mesmo nome, tipo e distrito, códigos diferentes
        (2021, "500001", "BEIJA FLOR", "CR.P.CONV", "LAJEADO", "GUAIANASES", "1201", "Ativa", 40),
        (2021, "500002", "BEIJA FLOR", "CR.P.CONV", "LAJEADO", "GUAIANASES", "1202", "Ativa", 45),
        (2023, "9,20961E+15", "BEIJA FLOR", "CR.P.CONV", "LAJEADO", "GUAIANASES", "8,24483E+12", "Ativa", 90),
        # escola nova, só nos anos de código destruído
        (2023, "1,31584E+13", "NOVA ESPERANCA", "CEI INDIRET", "LAJEADO", "GUAIANASES", None, "Ativa", 60),
        (2024, "1,31584E+13", "NOVA ESPERANCA", "CEI INDIRET", "LAJEADO", "GUAIANASES", None, "Ativa", 62),
    ]
    return pd.DataFrame(linhas, columns=COLUNAS)


# ---------------------------------------------------------------- avaliação do código

def test_avaliacao_do_codigo_por_ano():
    q = e.avaliar_codigos(e.normalizar(cenario()))
    assert q == {2020: e.CONFIAVEL, 2021: e.CONFIAVEL, 2022: e.CONSISTENTE_NO_ANO,
                 2023: e.CORROMPIDO, 2024: e.CORROMPIDO}


def test_codigo_que_cobre_duas_escolas_no_mesmo_ano_e_corrompido():
    df = pd.DataFrame([(2030, "123", "A", "EMEF", "X", None, None, None, 1),
                       (2030, "123", "B", "EMEF", "X", None, None, None, 1)], columns=COLUNAS)
    assert e.avaliar_codigos(e.normalizar(df)) == {2030: e.CORROMPIDO}


@pytest.mark.parametrize("bruto, esperado", [("019459", "19459"), (" 19459 ", "19459"), ("0", "0"), ("", None), (None, None)])
def test_codigo_normalizado(bruto, esperado):
    assert e.codigo_normalizado(bruto) == esperado


# ---------------------------------------------------------------- identificação

@pytest.fixture
def identificadas():
    return e.identificar(e.normalizar(cenario()))


def _cod(df, ano, nome):
    return df[(df.ano == ano) & (df.nome == nome)]["cod_escola"].tolist()


def test_codigo_publicado_ignora_zeros_a_esquerda(identificadas):
    assert _cod(identificadas, 2020, "UNIAO DE VILA NOVA I") == ["19459"]
    assert _cod(identificadas, 2021, "UNIAO DE VILA NOVA I") == ["19459"]


def test_codigo_recuperado_pelo_nome_nos_anos_ruins(identificadas):
    for ano in (2022, 2023):
        linha = identificadas[(identificadas.ano == ano) & (identificadas.nome == "UNIAO DE VILA NOVA I")]
        assert linha["cod_escola"].tolist() == ["19459"]
        assert linha["vinculo"].tolist() == ["RECUPERADO_POR_NOME"]


def test_homonimo_em_ano_ruim_recebe_chave_sintetica(identificadas):
    cod = _cod(identificadas, 2023, "BEIJA FLOR")
    assert len(cod) == 1 and cod[0].startswith("SINT-")


def test_escola_nova_tem_chave_sintetica_estavel_entre_anos(identificadas):
    c23, c24 = _cod(identificadas, 2023, "NOVA ESPERANCA"), _cod(identificadas, 2024, "NOVA ESPERANCA")
    assert c23 == c24 and c23[0].startswith("SINT-")


def test_setor_so_e_aproveitado_em_ano_de_codigo_confiavel(identificadas):
    def setor(ano):
        linha = identificadas[(identificadas.ano == ano) & (identificadas.nome == "UNIAO DE VILA NOVA I")]
        return linha["setor"].iloc[0]
    assert setor(2021) == "8701"
    assert pd.isna(setor(2022)) and pd.isna(setor(2023))


# ---------------------------------------------------------------- versões (SCD tipo 2)

@pytest.fixture
def versoes(identificadas):
    return e.versionar(identificadas)


def test_troca_de_nome_gera_nova_versao(versoes):
    v = versoes[versoes.cod_escola == "308775"].sort_values("versao")
    assert v["nome_escola"].tolist() == ["AQUARELA", "MARGARIDA"]
    assert v[["ano_inicio", "ano_fim"]].values.tolist() == [[2020, 2020], [2021, 2021]]
    assert v["versao_atual"].tolist() == [False, True]


def test_mudanca_so_de_grafia_nao_gera_versao(versoes):
    v = versoes[versoes.cod_escola == "19459"]
    assert len(v) == 1
    assert (v.iloc[0]["ano_inicio"], v.iloc[0]["ano_fim"]) == (2020, 2023)
    assert v.iloc[0]["dre"] == "SAO MIGUEL" and v.iloc[0]["tipo_escola"] == "EMEI"
    assert v.iloc[0]["setor_sme"] == "8701"


def test_chave_artificial_unica_e_sequencial(versoes):
    assert versoes["chave_escola"].is_unique
    assert sorted(versoes["chave_escola"]) == list(range(1, len(versoes) + 1))


def test_atributos_derivados(versoes):
    v = versoes.set_index("cod_escola")
    assert v.loc["19459", "rede"] == "DIRETA"
    sint = versoes[versoes.codigo_sintetico]
    assert set(sint["rede"]) == {"CONVENIADA"}


# ---------------------------------------------------------------- mapa para a carga do fato

def test_mapa_liga_cada_combinacao_bruta_a_uma_versao(identificadas, versoes):
    mapa = e.mapa_carga(identificadas, versoes)
    assert len(mapa) == len(cenario())
    assert mapa["chave_escola"].notna().all()
    # a matrícula de 2020 da AQUARELA aponta para a versão AQUARELA
    linha = mapa[(mapa.ano == 2020) & (mapa.nome_bruto == "AQUARELA")]
    chave = linha["chave_escola"].iloc[0]
    assert versoes.set_index("chave_escola").loc[chave, "nome_escola"] == "AQUARELA"
    # as colunas brutas preservam o texto original, que é a chave de junção com o staging
    assert set(mapa.columns) >= {"ano", "cd_bruto", "nome_bruto", "tipo_bruto", "distrito_bruto", "chave_escola"}
    assert "EMEI        " in set(mapa["tipo_bruto"])


def test_resumo_de_vinculo(identificadas):
    r = e.resumo_vinculo(identificadas)
    assert r.loc[2023, "RECUPERADO_POR_NOME"] == 290
    assert r.loc[2023, "SINTETICO"] == 150
    assert r.loc[2021, "PUBLICADO"] == 310 + 82 + 40 + 45


def test_homonimo_em_ano_de_codigo_longo_mas_consistente_recebe_chave_sintetica():
    df = pd.DataFrame([
        (2022, "9209611322271641", "BEIJA FLOR", "CR.P.CONV", "LAJEADO", "GUAIANASES", None, "Ativa", 40),
        (2022, "9209611322271642", "BEIJA FLOR", "CR.P.CONV", "LAJEADO", "GUAIANASES", None, "Ativa", 45),
        (2022, "9209611322271640", "UNIAO DE VILA NOVA I", "EMEI", "VILA JACUI", "SAO MIGUEL", None, "Ativa", 300),
    ], columns=COLUNAS)
    ident = e.identificar(e.normalizar(df))
    assert e.avaliar_codigos(e.normalizar(df)) == {2022: e.CONSISTENTE_NO_ANO}
    beija = ident[ident["nome"] == "BEIJA FLOR"]
    assert set(beija["vinculo"]) == {e.SINTETICO}
    assert beija["cod_escola"].nunique() == 2 and beija["cod_escola"].str.startswith("SINT-").all()
