"""Parser da planilha Demanda Registrada e Matrículas (SME-SP).

As fixtures em tests/fixtures/fila/ têm o cabeçalho e o rodapé originais de
cada um dos sete formatos publicados entre 2006 e 2026, reduzidos a três
distritos. Os valores esperados abaixo foram lidos diretamente desses arquivos.
"""
from datetime import date
from pathlib import Path

import pytest

from dw_sme.transformacao import fila

FIX = Path(__file__).parent / "fixtures" / "fila"


def registro(planilha, distrito, etapa):
    achados = [r for r in planilha.linhas if r["distrito"] == distrito and r["etapa"] == etapa]
    assert len(achados) == 1, f"{distrito}/{etapa}: {len(achados)} registros"
    return achados[0]


def medidas(r):
    return {k: r[k] for k in fila.MEDIDAS}


# --------------------------------------------------------------------------- período

@pytest.mark.parametrize("nome, esperado", [
    ("publicacao-demanda-e-matricula-abr-2024.csv", date(2024, 4, 1)),
    ("demanda-e-matriculas-setembro-2022.csv", date(2022, 9, 1)),
    ("publicacao-bimestral-dezembro-2023.csv", date(2023, 12, 1)),
    ("publicacao-demanda-e-matriculas-dez-2025-.csv", date(2025, 12, 1)),
    ("matriculas-e-demanda-marco-2020.csv", date(2020, 3, 1)),
    ("Demanda e Matrículas - Jun/2026", date(2026, 6, 1)),
    ("jun-06", date(2006, 6, 1)),
])
def test_periodo_do_nome(nome, esperado):
    assert fila.periodo_do_nome(nome) == esperado


def test_periodo_sem_mes_falha():
    with pytest.raises(ValueError):
        fila.periodo_do_nome("evolucaodemanda.csv")


# --------------------------------------------------------------------------- formatos

def test_formato_a_quebra_em_tres_categorias_com_total():
    p = fila.ler_planilha(FIX / "publicacao-demanda-e-matricula-abr-2024.csv")
    assert (p.layout, p.periodo) == ("A", date(2024, 4, 1))
    assert {r["distrito"] for r in p.linhas} == {"AGUA RASA", "ALTO DE PINHEIROS", "ANHANGUERA"}
    assert medidas(registro(p, "AGUA RASA", "CRECHE")) == dict(
        matriculas=1228, matriculas_em_processo=11, demanda_total=27, demanda_sem_opcao=14,
        demanda_sem_opcao_ate_30d=14, demanda_sem_opcao_mais_30d=0, demanda_com_opcao=13)
    fund = registro(p, "AGUA RASA", "FUND_I")
    assert (fund["matriculas"], fund["demanda_total"]) == (971, 0)
    # quebra não publicada para o fundamental: nulo, não zero
    assert fund["matriculas_em_processo"] is None
    assert fund["demanda_sem_opcao"] is None
    # ensino médio não tem coluna de demanda
    assert registro(p, "AGUA RASA", "MEDIO")["demanda_total"] is None


def test_formato_b_so_total():
    p = fila.ler_planilha(FIX / "demanda-e-matriculas-junho-2018.csv")
    assert (p.layout, p.periodo) == ("B", date(2018, 6, 1))
    r = registro(p, "ANHANGUERA", "CRECHE")
    assert (r["matriculas"], r["matriculas_em_processo"], r["demanda_total"]) == (2573, 119, 622)
    assert r["demanda_sem_opcao"] is None and r["demanda_com_opcao"] is None


def test_formato_c_matricula_em_processo_em_seis_etapas_e_nota_da_greve():
    p = fila.ler_planilha(FIX / "demanda-e-matriculas-marco-2018.csv")
    assert p.layout == "C"
    assert registro(p, "AGUA RASA", "FUND_II")["matriculas_em_processo"] == 8
    assert registro(p, "AGUA RASA", "EJA_II")["matriculas_em_processo"] == 2
    assert registro(p, "AGUA RASA", "CRECHE")["demanda_total"] == 141
    assert any("GREVE" in o.upper() for o in p.observacoes)


def test_formato_d_sem_total_e_com_colunas_soltas():
    p = fila.ler_planilha(FIX / "demanda-e-matriculas-setembro-2020.csv")
    assert p.layout == "D"
    assert medidas(registro(p, "AGUA RASA", "CRECHE")) == dict(
        matriculas=1142, matriculas_em_processo=35, demanda_total=32, demanda_sem_opcao=24,
        demanda_sem_opcao_ate_30d=18, demanda_sem_opcao_mais_30d=6, demanda_com_opcao=8)
    assert p.colunas_ignoradas, "as colunas 'mat' e 'mat pr' precisam ser registradas como ignoradas"
    assert any("TRANSPORTE" in o.upper() for o in p.observacoes)


def test_formato_e_sem_opcao_sem_quebra_de_prazo():
    p = fila.ler_planilha(FIX / "matriculas-e-demanda-junho-2020.csv")
    assert p.layout == "E"
    r = registro(p, "AGUA RASA", "CRECHE")
    assert (r["demanda_total"], r["demanda_sem_opcao"], r["demanda_com_opcao"]) == (93, 82, 11)
    assert r["demanda_sem_opcao_ate_30d"] is None and r["demanda_sem_opcao_mais_30d"] is None


def test_formato_f_recusou_vaga_conta_como_com_opcao_e_numero_sem_ponto():
    p = fila.ler_planilha(FIX / "matriculas-e-demanda-setembro-2019.csv")
    assert p.layout == "F"
    r = registro(p, "AGUA RASA", "CRECHE")
    assert (r["demanda_sem_opcao"], r["demanda_com_opcao"], r["demanda_total"]) == (210, 26, 236)
    pre = registro(p, "AGUA RASA", "PRE")
    assert pre["demanda_total"] == 0 and pre["demanda_sem_opcao"] is None
    assert registro(p, "ANHANGUERA", "CRECHE")["matriculas"] == 2752


def test_serie_historica_vira_uma_planilha_por_periodo():
    ps = fila.ler_serie_historica(FIX / "evolucaodemanda.csv")
    assert [p.periodo for p in ps] == [date(2014, 12, 1), date(2015, 3, 1), date(2017, 12, 1)]
    assert {p.layout for p in ps} == {"H"}
    mar15 = ps[1]
    r = registro(mar15, "AGUA RASA", "CRECHE")
    assert (r["matriculas"], r["matriculas_em_processo"], r["demanda_total"]) == (949, 2, 228)
    assert registro(mar15, "ANHANGUERA", "CRECHE")["matriculas"] == 2041
    assert registro(mar15, "AGUA RASA", "MEDIO")["demanda_total"] is None
    assert registro(ps[2], "AGUA RASA", "CRECHE")["matriculas"] == 1045


# --------------------------------------------------------------------------- conferências

@pytest.mark.parametrize("arquivo", sorted(p.name for p in FIX.glob("*.csv") if p.name != "evolucaodemanda.csv"))
def test_soma_dos_distritos_bate_com_linha_total(arquivo):
    p = fila.ler_planilha(FIX / arquivo)
    assert fila.conferir_totais(p) == []
    assert p.inconsistencias == []


def test_divergencia_com_linha_total_e_reportada(tmp_path):
    texto = (FIX / "demanda-e-matriculas-junho-2018.csv").read_text(encoding="latin1")
    adulterado = texto.replace("TOTAL;4.103", "TOTAL;4.104")
    alvo = tmp_path / "demanda-e-matriculas-junho-2018.csv"
    alvo.write_text(adulterado, encoding="latin1")
    divergencias = fila.conferir_totais(fila.ler_planilha(alvo))
    assert len(divergencias) == 1 and "CRECHE" in divergencias[0]


def _planilha_sintetica(tmp_path, rodape):
    conteudo = (
        "Distrito;Matrículas;Demanda;\n"
        ";Creche;Creche (1);Creche (2)\n"
        "AGUA RASA;10;1;2\n"
        "TOTAL;10;1;2\n" + rodape
    )
    alvo = tmp_path / "teste-marco-2030.csv"
    alvo.write_text(conteudo, encoding="latin1")
    return alvo


def test_nota_de_rodape_desconhecida_falha_alto(tmp_path):
    alvo = _planilha_sintetica(tmp_path, "(1) - texto sem significado conhecido;;;\n(2) - outro;;;\n")
    with pytest.raises(ValueError, match="nota"):
        fila.ler_planilha(alvo)


def test_coluna_numerada_sem_nota_falha_alto(tmp_path):
    alvo = _planilha_sintetica(tmp_path, "")
    with pytest.raises(ValueError, match="nota"):
        fila.ler_planilha(alvo)


def _sem_linha(origem: Path, destino: Path, trecho: str, substituto: str | None = None) -> Path:
    texto = origem.read_text(encoding="latin1")
    linhas = texto.splitlines()
    if substituto is None:
        linhas = [linha for linha in linhas if not linha.startswith(trecho)]
    else:
        linhas = [substituto if linha.startswith(trecho) else linha for linha in linhas]
    destino.write_text("\n".join(linhas) + "\n", encoding="latin1")
    return destino


def test_nota_ausente_e_herdada_do_formato_quando_as_demais_concordam(tmp_path):
    # Caso real: a planilha de dez/2024 publicou só as notas (2) e (3).
    original = FIX / "publicacao-demanda-e-matricula-abr-2024.csv"
    alvo = _sem_linha(original, tmp_path / "publicacao-demanda-e-matricula-abr-2024.csv", "(1)")
    p = fila.ler_planilha(alvo)
    esperado = fila.ler_planilha(original)
    assert p.linhas == esperado.linhas
    assert any("herdad" in o.lower() and "(1)" in o for o in p.observacoes)


def test_nota_presente_que_contradiz_o_formato_falha(tmp_path):
    original = FIX / "publicacao-demanda-e-matricula-abr-2024.csv"
    alvo = tmp_path / "publicacao-demanda-e-matricula-abr-2024.csv"
    _sem_linha(original, alvo, "(1)")
    _sem_linha(alvo, alvo, "(3)", "(3) - Demanda sem opção por unidade específica em espera até 30 dias;;")
    with pytest.raises(ValueError, match="contradiz"):
        fila.ler_planilha(alvo)


def test_quebra_de_linha_so_com_retorno_de_carro(tmp_path):
    # A série histórica real usa '\r' sozinho como fim de linha (padrão do Mac antigo).
    original = (FIX / "evolucaodemanda.csv").read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r")
    alvo = tmp_path / "evolucaodemanda.csv"
    alvo.write_bytes(original)
    ps = fila.ler_serie_historica(alvo)
    assert len(ps) == 3 and len(ps[1].linhas) == 3 * 8


def test_inconsistencia_identifica_arquivo_e_distrito(tmp_path):
    original = FIX / "publicacao-demanda-e-matricula-abr-2024.csv"
    alvo = _sem_linha(original, tmp_path / "publicacao-demanda-e-matricula-abr-2024.csv",
                      "AGUA RASA", "AGUA RASA ;1.228;736;971;929;0;25;0;0;11;1;14;0;13;99;0;0;0;0;0;0;0;0")
    p = fila.ler_planilha(alvo)
    assert len(p.inconsistencias) == 1
    assert "publicacao-demanda-e-matricula-abr-2024.csv" in p.inconsistencias[0]
    assert "AGUA RASA" in p.inconsistencias[0]
    assert registro(p, "AGUA RASA", "CRECHE")["demanda_total"] == 99  # total publicado prevalece


def test_dataframe_canonico(tmp_path):
    ps = [fila.ler_planilha(FIX / "publicacao-demanda-e-matricula-abr-2024.csv")]
    df = fila.para_dataframe(ps)
    assert list(df.columns) == ["periodo", "distrito", "etapa", *fila.MEDIDAS, "layout", "arquivo"]
    assert len(df) == 3 * 8
    assert df["demanda_sem_opcao"].isna().sum() > 0  # nulos preservados


# ------------------------------------------------------------------ arquivos fora do formato

def test_arquivo_sem_cabecalho_de_duas_linhas(tmp_path):
    alvo = tmp_path / "demanda-jun-2024.csv"
    alvo.write_text("DISTRITO;CRECHE\n", encoding="latin-1")
    with pytest.raises(ValueError, match="cabeçalho de duas linhas"):
        fila.ler_planilha(alvo)


def test_cabecalho_sem_coluna_reconhecida(tmp_path):
    alvo = tmp_path / "demanda-jun-2024.csv"
    alvo.write_text("A;B;C\nD;E;F\nX;1;2\nTOTAL;1;2\n", encoding="latin-1")
    with pytest.raises(ValueError, match="nenhuma coluna reconhecida"):
        fila.ler_planilha(alvo)


def test_planilha_sem_linha_total(tmp_path):
    origem = FIX / "publicacao-demanda-e-matricula-abr-2024.csv"
    alvo = _sem_linha(origem, tmp_path / origem.name, "TOTAL")
    with pytest.raises(ValueError, match="linha TOTAL"):
        fila.ler_planilha(alvo)


def test_linha_em_branco_no_meio_dos_distritos_e_ignorada(tmp_path):
    origem = FIX / "publicacao-demanda-e-matricula-abr-2024.csv"
    linhas = origem.read_text(encoding="latin1").splitlines()
    alvo = tmp_path / origem.name
    alvo.write_text("\n".join([*linhas[:3], ";;;;", "", *linhas[3:]]) + "\n", encoding="latin1")
    assert fila.ler_planilha(alvo).linhas == fila.ler_planilha(origem).linhas


def test_coluna_de_demanda_sem_nota_nao_vira_numero_com_sentido_errado():
    with pytest.raises(ValueError, match="sem nota de rodapé"):
        fila._combinar({("demanda", "9"): 5}, {}, "CRECHE", [], "teste")
