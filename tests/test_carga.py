"""Carga completa do data warehouse sobre os dados sintéticos de tests/conftest.py."""
import duckdb
import pytest

from dw_sme.carga import carregar
from dw_sme.config import Configuracao


@pytest.fixture
def dw(dados_sinteticos, tmp_path):
    cfg = Configuracao(dir_dados=dados_sinteticos, anos=range(2015, 2025), banco=tmp_path / "dw_teste.duckdb")
    resumo = carregar.carregar_tudo(cfg)
    con = duckdb.connect(str(cfg.banco), read_only=True)
    yield con, resumo
    con.close()


def um(con, sql):
    return con.execute(sql).fetchone()[0]


def test_resumo_da_carga(dw):
    _, resumo = dw
    assert resumo["fato_matricula"] == 7
    assert resumo["excluidas_sem_etapa"] == 0       # atividade complementar sai antes, no filtro de escolarização
    assert resumo["fato_fila"] == 8 * 3 * 8          # 8 períodos no recorte x 3 distritos x 8 etapas


def test_fato_matricula_exclui_atividade_complementar(dw):
    con, _ = dw
    assert um(con, "select sum(qtd_matricula) from dw.fato_matricula") == 7
    assert um(con, """select count(*) from dw.fato_matricula f join dw.dim_serie s using (chave_serie)
                      where s.modalidade = 'ATCOMP'""") == 0


def test_dimensoes_basicas(dw):
    con, _ = dw
    assert um(con, "select count(*) from dw.dim_etapa") == 10
    assert um(con, "select count(*) from dw.dim_tempo") == 120             # jan/2015 a dez/2024
    assert um(con, "select count(*) from dw.dim_tempo where fila_publicada") == 8
    assert um(con, "select count(*) from dw.dim_idade") == 101              # 0 a 99 e 'não informada'
    assert con.execute("select ano from dw.dim_ano_letivo order by ano").fetchall() == [(2019,), (2021,), (2023,)]


def test_territorio_com_dre_predominante_e_membro_desconhecido(dw):
    con, _ = dw
    dres = dict(con.execute("select distrito, dre from dw.dim_territorio").fetchall())
    assert dres == {"AGUA RASA": "PENHA", "ANHANGUERA": "PIRITUBA/JARAGUA",
                    "ALTO DE PINHEIROS": "BUTANTA", "NAO INFORMADO": None}


def test_escola_scd2_e_codigo_recuperado(dw):
    con, _ = dw
    versoes = con.execute("""select cod_escola, versao, nome_escola, ano_inicio, ano_fim
                             from dw.dim_escola order by cod_escola, versao""").fetchall()
    assert ("19459", 1, "UNIAO DE VILA NOVA I", 2019, 2023) in versoes          # 2023 recuperado pelo nome
    assert ("308775", 1, "AQUARELA", 2019, 2019) in versoes
    assert ("308775", 2, "MARGARIDA", 2021, 2021) in versoes
    assert um(con, "select count(*) from dw.dim_escola where codigo_sintetico") == 1
    # a matrícula de 2021 da conveniada aponta para a versão MARGARIDA
    assert um(con, """select e.nome_escola from dw.fato_matricula f join dw.dim_escola e using (chave_escola)
                      join dw.dim_ano_letivo a using (chave_ano_letivo) where a.ano = 2021 and e.cod_escola = '308775'""") == "MARGARIDA"


def test_turno_de_2021_vem_do_codigo(dw):
    con, _ = dw
    linhas = con.execute("""select a.ano, t.turno, t.origem_turno from dw.fato_matricula f
                            join dw.dim_turno t using (chave_turno) join dw.dim_ano_letivo a using (chave_ano_letivo)
                            order by 1, 2""").fetchall()
    assert (2021, "INTEGRAL", "CODIGO_2021") in linhas and (2021, "TARDE", "CODIGO_2021") in linhas
    assert all(origem == "PUBLICADO" for ano, _, origem in linhas if ano != 2021)


def test_idade_calculada_quando_falta(dw):
    con, _ = dw
    idade = um(con, """select i.idade from dw.fato_matricula f join dw.dim_idade i using (chave_idade)
                       join dw.dim_ano_letivo a using (chave_ano_letivo) join dw.dim_escola e using (chave_escola)
                       where a.ano = 2021 and e.cod_escola = '308775'""")
    assert idade == 2   # nasceu em julho de 2018: 2 anos em 31/03/2021


def test_matricula_corrompida_fica_nula(dw):
    con, _ = dw
    por_ano = dict(con.execute("""select a.ano, count(f.cd_matricula_origem) from dw.fato_matricula f
                                  join dw.dim_ano_letivo a using (chave_ano_letivo) group by 1""").fetchall())
    assert por_ano == {2019: 3, 2021: 2, 2023: 0}


def test_bugigangas(dw):
    con, _ = dw
    assert um(con, "select count(*) from dw.fato_matricula f join dw.dim_deficiencia d using (chave_deficiencia) where d.autismo") == 1
    # indicadores inexistentes no arquivo ficam nulos (não coletados), não falsos
    assert um(con, "select count(*) from dw.dim_deficiencia where sindrome_down is not null") == 0
    racas = {r[0] for r in con.execute("select raca_cor from dw.dim_perfil_aluno").fetchall()}
    assert "NAO DECLARADA" in racas
    desfechos = dict(con.execute("""select s.desfecho, count(*) from dw.fato_matricula f
                                    join dw.dim_situacao_matricula s using (chave_situacao) group by 1""").fetchall())
    assert desfechos == {"APROVADO": 2, "ABANDONO": 1, "CONCLUIDO": 1, "REPROVADO": 1, "EM CURSO": 2}


def test_fato_desfecho_soma_igual_ao_fato_matricula(dw):
    con, _ = dw
    assert um(con, "select sum(qtd_matriculas) from dw.fato_desfecho") == 7
    soma_partes = um(con, """select sum(qtd_aprovados + qtd_reprovados + qtd_abandonos + qtd_transferidos + qtd_concluintes
                             + qtd_falecidos + qtd_outras_saidas + qtd_em_curso + qtd_sem_desfecho) from dw.fato_desfecho""")
    assert soma_partes == 7
    taxa = um(con, """select sum(qtd_abandonos) / sum(qtd_aprovados + qtd_reprovados + qtd_abandonos)
                      from dw.vw_desfecho_taxas v join dw.dim_ano_letivo a using (chave_ano_letivo) where a.ano = 2019""")
    assert taxa == pytest.approx(0.5)


def test_fato_fila_preserva_nulo_e_formato(dw):
    con, _ = dw
    r = con.execute("""select f.formato_planilha, f.qtd_demanda_total, f.qtd_demanda_sem_opcao, f.qtd_demanda_com_opcao
                       from dw.fato_fila f join dw.dim_tempo t using (chave_tempo)
                       join dw.dim_territorio d using (chave_territorio) join dw.dim_etapa e using (chave_etapa)
                       where t.ano_mes = '2019-09' and d.distrito = 'AGUA RASA' and e.codigo = 'CRECHE'""").fetchone()
    assert r == ("F", 236, 210, 26)
    assert um(con, """select f.qtd_demanda_sem_opcao from dw.fato_fila f join dw.dim_tempo t using (chave_tempo)
                      join dw.dim_territorio d using (chave_territorio) join dw.dim_etapa e using (chave_etapa)
                      where t.ano_mes = '2018-06' and d.distrito = 'AGUA RASA' and e.codigo = 'CRECHE'""") is None
    assert um(con, "select observacao from dw.dim_tempo where ano_mes = '2018-03'").upper().count("GREVE") == 1


def test_observacoes_do_ano_letivo_vem_do_dado(dw):
    con, _ = dw
    obs = dict(con.execute("select ano, observacao from dw.dim_ano_letivo").fetchall())
    assert "turno" in obs[2021].lower() and "datas" in obs[2021].lower()
    assert "código" in obs[2023].lower() and "em curso" in obs[2023].lower()
    assert obs[2019] is None


def test_staging_e_removido_por_padrao(dw):
    con, _ = dw
    assert um(con, "select count(*) from information_schema.schemata where schema_name = 'stg'") == 0


def test_nome_de_banco_que_colide_com_o_esquema_e_recusado(tmp_path):
    with pytest.raises(ValueError, match="dw.duckdb"):
        Configuracao(dir_dados=tmp_path, banco=tmp_path / "dw.duckdb")
