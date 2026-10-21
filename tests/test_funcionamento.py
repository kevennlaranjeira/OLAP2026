"""Testes de funcionamento: o pipeline como o grupo vai usá-lo, pela linha de comando e em volume.

- recarregar o mesmo banco não duplica nada;
- `verificar` e `tudo` saem com código 1 quando alguma verificação dá FALHA;
- as consultas devolvem as mesmas linhas, na mesma ordem, quando o mesmo dado é carregado em outra ordem física;
- a carga de um volume maior conserva as contagens entre os fatos e passa nas verificações do modelo.
"""
import json
import runpy
import sys

import duckdb
import pytest

from dw_sme import __version__, cli, pipeline
from dw_sme.config import Configuracao
from dw_sme.qualidade.verificacoes import ALERTA, FALHA, OK

from conftest import gravar_volume

TABELAS = ("fato_matricula", "fato_fila", "fato_desfecho", "fato_turma", "fato_populacao",
           "dim_tempo", "dim_data", "dim_ano_letivo", "dim_territorio", "dim_escola", "dim_etapa", "dim_serie",
           "dim_turno", "dim_idade", "dim_faixa_etaria", "dim_setor_censitario", "dim_perfil_aluno",
           "dim_deficiencia", "dim_situacao_matricula")


def contagens(banco) -> dict[str, int]:
    con = duckdb.connect(str(banco), read_only=True)
    try:
        return {t: con.execute(f"SELECT count(*) FROM dw.{t}").fetchone()[0] for t in TABELAS}
    finally:
        con.close()


def somas(banco) -> dict[str, int]:
    con = duckdb.connect(str(banco), read_only=True)
    try:
        return dict(zip(("matriculas", "pessoas", "fila"), con.execute("""
            SELECT (SELECT sum(qtd_matricula) FROM dw.fato_matricula),
                   (SELECT sum(qtd_pessoas) FROM dw.fato_populacao),
                   (SELECT sum(qtd_demanda_total) FROM dw.fato_fila)""").fetchone(), strict=True))
    finally:
        con.close()


# ----------------------------------------------------------------------------- recarga

def test_recarregar_o_mesmo_banco_nao_duplica(dados_sinteticos):
    base = ["--dados", str(dados_sinteticos)]
    banco = dados_sinteticos / "dw" / "dw_sme.duckdb"
    assert cli.main(["carregar", *base]) == 0
    primeira, somas_1 = contagens(banco), somas(banco)
    resumo_1 = json.loads((dados_sinteticos / "relatorios" / "carga.json").read_text(encoding="utf-8"))

    assert cli.main(["carregar", *base]) == 0
    assert contagens(banco) == primeira
    assert somas(banco) == somas_1
    resumo_2 = json.loads((dados_sinteticos / "relatorios" / "carga.json").read_text(encoding="utf-8"))
    resumo_1.pop("segundos"), resumo_2.pop("segundos")
    assert resumo_2 == resumo_1
    assert cli.main(["verificar", *base]) == 0


# ----------------------------------------------------------------------------- código de saída

def test_verificar_sai_com_1_quando_ha_falha(dados_sinteticos, capsys):
    base = ["--dados", str(dados_sinteticos)]
    assert cli.main(["carregar", *base]) == 0
    con = duckdb.connect(str(dados_sinteticos / "dw" / "dw_sme.duckdb"))
    # fato_matricula não declara FK no DDL (decisão de desempenho): uma linha órfã entra, e Q01 tem de pegá-la
    con.execute("INSERT INTO dw.fato_matricula SELECT * REPLACE (987654 AS chave_escola) FROM dw.fato_matricula LIMIT 1")
    con.close()

    assert cli.main(["verificar", *base]) == 1
    assert "Q01 FALHA" in capsys.readouterr().out
    relatorio = (dados_sinteticos / "relatorios" / "qualidade.md").read_text(encoding="utf-8")
    assert "Integridade referencial · FALHA" in relatorio


def test_tudo_sai_com_1_quando_ha_falha(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "executar_tudo", lambda cfg: {"verificar": {"Q01": FALHA, "Q02": OK}})
    assert cli.main(["tudo", "--dados", str(tmp_path)]) == 1
    monkeypatch.setattr(pipeline, "executar_tudo", lambda cfg: {"verificar": {"Q01": OK, "Q07": ALERTA}})
    assert cli.main(["tudo", "--dados", str(tmp_path)]) == 0


def test_baixar_e_preparar_pela_linha_de_comando(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(pipeline, "baixar", lambda cfg: {"microdados": 5, "demanda": 33, "ibge": 2})
    monkeypatch.setattr(pipeline, "preparar", lambda cfg: [{"ano": 2019}, {"ano": 2020}])
    assert cli.main(["baixar", "--dados", str(tmp_path), "--sem-ibge"]) == 0
    assert cli.main(["preparar", "--dados", str(tmp_path)]) == 0
    saida = capsys.readouterr().out
    assert "baixados: {'microdados': 5" in saida and "arquivos preparados: 2" in saida


def test_python_m_dw_sme(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["dw_sme", "--version"])
    with pytest.raises(SystemExit) as saida:
        runpy.run_module("dw_sme", run_name="__main__")
    assert saida.value.code == 0
    assert __version__ in capsys.readouterr().out


# ----------------------------------------------------------------------------- volume e determinismo

ANOS = (2019, 2020, 2022)
TAMANHO = {"escolas": 90, "turmas_por_etapa": 3, "alunos_por_turma": 30}   # 24.300 matrículas por ano


def carregar_volume(raiz, embaralhar=None):
    dados = raiz / "data"
    total = gravar_volume(dados, anos=ANOS, embaralhar=embaralhar, **TAMANHO)
    cfg = Configuracao(dir_dados=dados, log=lambda *_: None)
    resumo = pipeline.carregar(cfg)
    return cfg, total, resumo


@pytest.fixture(scope="module")
def volume(tmp_path_factory):
    return carregar_volume(tmp_path_factory.mktemp("volume"))


def test_carga_com_volume_maior_conserva_as_contagens(volume):
    cfg, total, resumo = volume
    escolas, turmas, alunos = TAMANHO["escolas"], TAMANHO["turmas_por_etapa"], TAMANHO["alunos_por_turma"]
    assert total == len(ANOS) * escolas * 3 * turmas * alunos == 72_900
    assert resumo["fato_matricula"] == total
    assert resumo["fato_turma"] == len(ANOS) * escolas * 3 * turmas          # uma linha por turma
    assert resumo["fato_desfecho"] == len(ANOS) * escolas * 3                 # escola x ano x série
    assert resumo["dim_escola"] == escolas                                    # código estável: uma versão por escola

    con = duckdb.connect(str(cfg.banco), read_only=True)
    try:
        por_ano = dict(con.execute("""SELECT a.ano, sum(f.qtd_matricula) FROM dw.fato_matricula f
                                      JOIN dw.dim_ano_letivo a USING (chave_ano_letivo) GROUP BY 1""").fetchall())
        desfecho = con.execute("SELECT sum(qtd_matriculas), sum(qtd_abandonos), sum(qtd_aprovados) "
                               "FROM dw.fato_desfecho").fetchone()
        turma = con.execute("SELECT sum(qtd_matriculas), sum(qtd_turmas) FROM dw.fato_turma").fetchone()
    finally:
        con.close()
    assert por_ano == {ano: total // len(ANOS) for ano in ANOS}
    # o gerador escolhe o desfecho pela posição (escola + turma + aluno) numa lista de oito
    posicoes = [(e + t + a) % 8 for e in range(escolas) for t in range(turmas) for a in range(alunos)]
    por_etapa_e_ano = 3 * len(ANOS)
    assert desfecho[0] == total
    assert desfecho[1] == por_etapa_e_ano * posicoes.count(5)                    # ABAND
    assert desfecho[2] == por_etapa_e_ano * sum(posicoes.count(i) for i in range(4))   # APROV
    assert turma == (total, resumo["fato_turma"])


def test_volume_maior_passa_nas_verificacoes_do_modelo(volume):
    cfg, _, _ = volume
    status = {v.codigo: v.status for v in pipeline.verificar(cfg)}
    assert FALHA not in status.values()
    # integridade, conservação, ocupação, hierarquias: o modelo tem de valer com qualquer volume
    for codigo in ("Q01", "Q02", "Q03", "Q08", "Q09", "Q11", "Q13"):
        assert status[codigo] == OK, codigo


def test_consultas_iguais_quando_o_dado_entra_em_outra_ordem(volume, tmp_path):
    cfg, _, _ = volume
    outro, _, _ = carregar_volume(tmp_path, embaralhar=7)
    a = pipeline.consultar(cfg)
    b = pipeline.consultar(outro)
    assert set(a) == set(b) == {f"C{i}" for i in range(1, 9)}
    for codigo in a:
        assert not a[codigo].empty, codigo
        assert a[codigo].equals(b[codigo]), f"{codigo} mudou de conteúdo ou de ordem"
    for csv in (cfg.dir_relatorios / "consultas").glob("*.csv"):
        assert csv.read_bytes() == (outro.dir_relatorios / "consultas" / csv.name).read_bytes(), csv.name


def test_consultas_iguais_quando_repetidas(volume):
    cfg, _, _ = volume
    primeira = pipeline.consultar(cfg)
    for codigo, df in pipeline.consultar(cfg).items():
        assert df.equals(primeira[codigo]), codigo


def test_c3_soma_certa_em_volume(volume):
    """Confere o valor, não só a repetição: o DuckDB 2.0.0 truncava esta soma em 8 bits (4.050 virava -46)."""
    cfg, _, _ = volume
    c3 = pipeline.consultar(cfg)["C3"]
    creche_por_ano = TAMANHO["escolas"] * TAMANHO["turmas_por_etapa"] * TAMANHO["alunos_por_turma"]   # 8.100
    assert c3.groupby("ano")["matriculas"].sum().to_dict() == {ano: creche_por_ano for ano in (2019, 2022)}
    assert set(c3["matriculas"]) == {creche_por_ano // 2}        # metade das escolas direta, metade conveniada
    assert c3.groupby("ano")["participacao_no_ano"].sum().round(4).eq(1).all()


# ----------------------------------------------------------------------------- caminhos com apóstrofo

def test_pasta_com_apostrofo_e_acento_no_caminho(dados_sinteticos, tmp_path):
    """Sobrenomes como D'Ávila aparecem em pastas de usuário; o caminho entra na SQL entre aspas simples."""
    import shutil
    dados = tmp_path / "dados d'água"
    shutil.copytree(dados_sinteticos, dados)
    base = ["--dados", str(dados)]
    assert cli.main(["carregar", *base]) == 0
    assert cli.main(["verificar", *base]) == 0
    assert cli.main(["consultar", *base]) == 0
    assert contagens(dados / "dw" / "dw_sme.duckdb")["fato_matricula"] == 7


def test_csv_em_caminho_com_apostrofo_vira_parquet(tmp_path):
    from dw_sme.preparacao import _csv_para_parquet
    pasta = tmp_path / "planilhas d'Ávila"
    pasta.mkdir()
    csv = pasta / "Microdados_EOL_Matriculas_Ano_2019.csv"
    csv.write_text("AN_LETIVO;NOME_ESCOLA\n2019;ESCOLA D'OESTE\n2019;OUTRA\n", encoding="utf-8")
    r = _csv_para_parquet(csv, pasta / "saida d'água" / "x.parquet")
    assert (r["linhas"], r["rejeitadas"]) == (2, 0)
    con = duckdb.connect()
    nomes = [n for (n,) in con.execute("SELECT NOME_ESCOLA FROM read_parquet(?) ORDER BY 1",
                                       [str(pasta / "saida d'água" / "x.parquet")]).fetchall()]
    con.close()
    assert nomes == ["ESCOLA D'OESTE", "OUTRA"]


# ----------------------------------------------------------------------------- arquivo do banco

def test_recarga_nao_infla_o_arquivo_do_banco(dados_sinteticos):
    """O DuckDB não devolve ao disco o espaço das tabelas apagadas: recarregar no mesmo arquivo o fazia crescer."""
    base = ["--dados", str(dados_sinteticos)]
    banco = dados_sinteticos / "dw" / "dw_sme.duckdb"
    tamanhos = []
    for _ in range(3):
        assert cli.main(["carregar", *base]) == 0
        tamanhos.append(banco.stat().st_size)
    assert tamanhos[2] <= tamanhos[0] * 1.05, tamanhos
    assert not list(banco.parent.glob("*_carregando*"))


def test_carga_que_falha_preserva_o_banco_anterior(dados_sinteticos, monkeypatch):
    from dw_sme.carga import carregar
    cfg = Configuracao(dir_dados=dados_sinteticos, log=lambda *_: None)
    carregar.carregar_tudo(cfg)
    antes = contagens(cfg.banco)

    def quebra(con):
        raise RuntimeError("falha simulada no meio da carga")

    monkeypatch.setattr(carregar, "_fato_turma", quebra)
    with pytest.raises(RuntimeError, match="falha simulada"):
        carregar.carregar_tudo(cfg)
    assert contagens(cfg.banco) == antes
    assert not list(cfg.banco.parent.glob("*_carregando*"))
