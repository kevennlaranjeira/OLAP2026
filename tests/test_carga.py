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
    # na educação infantil não há aprovação: a taxa de rendimento é nula, as contagens ficam
    linhas = con.execute("""select nivel, aplica_rendimento, qtd_abandonos, taxa_abandono from dw.vw_desfecho_taxas v
                            join dw.dim_ano_letivo a using (chave_ano_letivo) where a.ano = 2019 and qtd_abandonos > 0""").fetchall()
    assert linhas == [("EDUCACAO INFANTIL", False, 1, None)]


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


def test_staging_fica_fora_do_banco_final(dw, dados_sinteticos):
    con, _ = dw
    assert um(con, "select count(*) from information_schema.schemata where schema_name = 'stg'") == 0
    assert not (dados_sinteticos / "interim" / "staging.duckdb").exists()


def test_nome_de_banco_que_colide_com_o_esquema_e_recusado(tmp_path):
    with pytest.raises(ValueError, match="dw.duckdb"):
        Configuracao(dir_dados=tmp_path, banco=tmp_path / "dw.duckdb")


def test_dimensao_data_com_dois_papeis(dw):
    con, _ = dw
    assert um(con, "select count(*) from dw.dim_data") == 4383 + 1      # 2014 a 2025 e 'não informada'
    datas = con.execute("""select a.ano, di.data, df.data from dw.fato_matricula f
                           join dw.dim_ano_letivo a using (chave_ano_letivo)
                           join dw.dim_data di on di.chave_data = f.chave_data_inicio
                           join dw.dim_data df on df.chave_data = f.chave_data_fim
                           order by 1, 2""").fetchall()
    import datetime as dt
    assert (2019, dt.date(2019, 2, 4), dt.date(2019, 6, 10)) in datas
    assert all(ini is None and fim is None for ano, ini, fim in datas if ano == 2021)   # 2021 sem datas
    assert all(fim is None for ano, _, fim in datas if ano == 2023)                     # sem DT_FIM no exemplo


@pytest.mark.parametrize("valor, esperado", [
    ("1", "1"), ("0", "0"), ("1,00", "1"), ("0,00", "0"), (" 1 ", "1"),
    ("2", "-"),      # aparece em 5 linhas de deficiência em dez anos: ruído de digitação
    (None, "-"), ("x", "-"),
])
def test_leitura_de_indicador(valor, esperado):
    con = duckdb.connect()
    assert con.execute(f"select {carregar._flag('v')} from (select CAST(? AS VARCHAR) AS v)", [valor]).fetchone()[0] == esperado


def test_fato_turma_agrega_o_fato_de_matricula(dw):
    con, resumo = dw
    assert resumo["fato_turma"] == 6                     # duas turmas em cada um dos três anos
    linhas = con.execute("""select a.ano, s.codigo_etapa, t.qtd_turmas, t.qtd_matriculas,
                                   t.qtd_matriculas_ativas_junho, t.qtd_turmas_ativas_junho
                            from dw.fato_turma t join dw.dim_ano_letivo a using (chave_ano_letivo)
                            join dw.dim_serie s using (chave_serie) order by 1, 2""").fetchall()
    assert linhas == [
        (2019, "CRECHE", 1, 1, 1, 1),
        (2019, "PRE", 1, 2, 1, 1),        # um dos dois alunos saiu em 10/06: não está ativo em 30/06
        (2021, "CRECHE", 1, 1, None, None),   # 2021 não publicou datas: nulo, não zero
        (2021, "PRE", 1, 1, None, None),
        (2023, "CRECHE", 1, 1, 1, 1),
        (2023, "PRE", 1, 1, 1, 1),
    ]
    assert um(con, "select sum(qtd_matriculas) from dw.fato_turma") == um(
        con, "select sum(qtd_matricula) from dw.fato_matricula")
    media = um(con, """select alunos_por_turma_junho from dw.vw_ocupacao_turma t
                       join dw.dim_ano_letivo a using (chave_ano_letivo) join dw.dim_serie s using (chave_serie)
                       where a.ano = 2019 and s.codigo_etapa = 'PRE'""")
    assert media == 1.0


def test_populacao_do_censo(dw):
    con, resumo = dw
    assert resumo["populacao"]["carregada"] and resumo["populacao"]["distritos_sem_territorio"] == 1
    assert resumo["fato_populacao"] == 6 * 11
    assert um(con, "select count(*) from dw.dim_faixa_etaria") == 11
    assert um(con, "select count(*) from dw.dim_setor_censitario") == 6
    # um único mês de referência, julho de 2022, anotado na dimensão Tempo
    assert con.execute("""select distinct t.ano_mes from dw.fato_populacao p
                          join dw.dim_tempo t using (chave_tempo)""").fetchall() == [("2022-07",)]
    assert "Censo" in um(con, "select observacao from dw.dim_tempo where ano_mes = '2022-07'")
    por_distrito = dict(con.execute("""
        select d.distrito, sum(p.qtd_pessoas) from dw.fato_populacao p
        join dw.dim_territorio d using (chave_territorio) join dw.dim_faixa_etaria f using (chave_faixa_etaria)
        where f.faixa_ibge = '0 A 4 ANOS' group by 1""").fetchall())
    from conftest import POPULACAO_0_4
    assert por_distrito == {**POPULACAO_0_4, "NAO INFORMADO": 1}
    # o valor não publicado fica nulo, não zero
    assert um(con, "select count(*) from dw.fato_populacao where qtd_pessoas is null") == 1
    # conformidade: toda faixa da dimensão Idade existe na dimensão Faixa Etária
    assert um(con, """select count(*) from (select distinct faixa_ibge from dw.dim_idade
                      where faixa_ibge <> 'NAO INFORMADA') i
                      left join dw.dim_faixa_etaria f using (faixa_ibge) where f.chave_faixa_etaria is null""") == 0


def test_arquivo_do_ibge_fora_do_layout_nao_impede_a_carga_da_sme(dados_sinteticos, tmp_path):
    (dados_sinteticos / "raw" / "ibge" / "Agregados_por_setores_demografia_BR.csv").write_text(
        "CD_SETOR;OUTRA\n355030801000001;1\n", encoding="utf-8")
    cfg = Configuracao(dir_dados=dados_sinteticos, banco=tmp_path / "layout.duckdb", log=lambda *_: None)
    resumo = carregar.carregar_tudo(cfg)
    assert resumo["populacao"]["carregada"] is False and "colunas esperadas ausentes" in resumo["populacao"]["motivo"]
    assert resumo["fato_populacao"] == 0 and resumo["fato_matricula"] == 7


def test_populacao_fora_do_recorte_nao_carrega(dados_sinteticos, tmp_path):
    cfg = Configuracao(dir_dados=dados_sinteticos, anos=range(2019, 2022), banco=tmp_path / "recorte.duckdb",
                       log=lambda *_: None)
    resumo = carregar.carregar_tudo(cfg)
    assert resumo["populacao"]["carregada"] is False and resumo["populacao"]["motivo"] == "2022 fora do recorte"
    assert resumo["fato_populacao"] == 0
