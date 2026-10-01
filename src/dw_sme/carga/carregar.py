"""Carga do data warehouse no DuckDB.

Fluxo (todo dentro de um único arquivo .duckdb):

1. esquema dw recriado a partir de sql/ddl/*.sql;
2. stgdb.stg.matricula: os Parquet brutos do recorte, harmonizados (microdados.py);
3. tabelas de correspondência stgdb.stg.map_*: as regras de normalização aplicadas
   aos valores distintos de cada coluna, em Python, e juntadas em SQL;
4. stgdb.stg.matricula_preparada: cada matrícula com as chaves naturais de todas as
   dimensões já resolvidas;
5. dimensões, fatos e observações de qualidade por ano;
6. o arquivo de staging é apagado (a menos que manter_staging seja pedido).

O texto bruto nunca é alterado no staging. As junções com as tabelas de
correspondência usam o valor bruto, com nulo trocado por um marcador.
"""
from __future__ import annotations

import time
from datetime import date
from importlib import resources

import duckdb
import pandas as pd

from ..config import Configuracao
from ..preparacao import preparar_fila
from ..transformacao import datas, etapas, idade, microdados, situacao
from ..transformacao import escolas as esc
from ..transformacao import normalizacao as n

NULO = "<nulo>"
# O staging vive num arquivo DuckDB separado, anexado durante a carga. Assim o banco
# final só recebe dimensões e fatos e não guarda os blocos livres de 13 milhões de
# linhas apagadas (o DuckDB não devolve ao disco o espaço de tabela apagada).
STG = "stgdb.stg"
_MESES = ("JANEIRO", "FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO", "JULHO",
          "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO")


# ----------------------------------------------------------------------------- utilitários

def _df(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    """Resultado como DataFrame de objetos, com None no lugar de NaN/NA."""
    df = con.execute(sql).df().astype(object)
    return df.where(df.notna(), None)


def _registrar(con, nome: str, df: pd.DataFrame) -> None:
    con.register("_tmp", df)
    con.execute(f"CREATE OR REPLACE TABLE {nome} AS SELECT * FROM _tmp")
    con.unregister("_tmp")


def _b(coluna: str) -> str:
    """Valor bruto com nulo trocado pelo marcador (chave de junção das tabelas de correspondência)."""
    return f"coalesce({coluna}, '{NULO}')"


VALORES_VERDADEIROS = ("1", "1,00")
VALORES_FALSOS = ("0", "0,00")


def _flag(coluna: str) -> str:
    """Indicador 0/1 da origem -> '1', '0' ou '-' (ausente, ilegível ou o '2' que aparece em 5 linhas).

    Os valores publicados são só '0', '1', '0,00', '1,00' (2020), '2' e nulo;
    comparar texto é bem mais barato que converter número em 13 milhões de linhas.
    """
    v = f"trim({coluna})"
    sim = ", ".join(f"'{x}'" for x in VALORES_VERDADEIROS)
    nao = ", ".join(f"'{x}'" for x in VALORES_FALSOS)
    return f"(CASE WHEN {v} IN ({sim}) THEN '1' WHEN {v} IN ({nao}) THEN '0' ELSE '-' END)"


def _bool_da_posicao(coluna: str, posicao: int) -> str:
    return f"(CASE substr({coluna}, {posicao}, 1) WHEN '1' THEN true WHEN '0' THEN false END)"


def criar_esquema(con) -> None:
    con.execute("DROP SCHEMA IF EXISTS dw CASCADE")
    pasta = resources.files("dw_sme") / "sql" / "ddl"
    for arquivo in sorted(p.name for p in pasta.iterdir() if p.name.endswith(".sql")):
        con.execute((pasta / arquivo).read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------- staging

def _staging_matricula(con, cfg: Configuracao) -> int:
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {STG}")
    partes = []
    for parquet in sorted(cfg.dir_bruto.glob("ano=*/*.parquet")):
        ano = int(parquet.parent.name.split("=")[1])
        if ano not in cfg.anos:
            continue
        fonte = f"read_parquet('{parquet.as_posix()}')"
        colunas = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {fonte}").fetchall()]
        partes.append(microdados.sql_staging(fonte, ano, parquet.stem, colunas))
    if not partes:
        raise FileNotFoundError(f"nenhum Parquet bruto do recorte em {cfg.dir_bruto}; rode a etapa preparar")
    con.execute("CREATE OR REPLACE TABLE stgdb.stg.matricula AS " + "\nUNION ALL BY NAME\n".join(partes))
    return con.execute("SELECT count(*) FROM stgdb.stg.matricula").fetchone()[0]


def _mapas(con) -> dict:
    """Tabelas de correspondência construídas sobre os valores distintos."""
    def simples(coluna: str, funcao, nome: str, saida: str):
        v = _df(con, f"SELECT DISTINCT {coluna} AS bruto FROM stgdb.stg.matricula")
        v[saida] = v["bruto"].map(funcao)
        v["bruto"] = v["bruto"].map(lambda x: NULO if x is None else x)
        _registrar(con, f"stgdb.stg.map_{nome}", v)

    simples("distrito", n.distrito, "distrito", "distrito")
    simples("dre", n.dre, "dre", "dre")
    simples("raca_cor", n.raca_cor, "raca", "raca_cor")
    simples("sexo", n.sexo, "sexo", "sexo")
    simples("situacao_matricula", n.texto, "situacao", "situacao")

    # série -> etapa
    s = _df(con, "SELECT DISTINCT modalidade, segmento, serie FROM stgdb.stg.matricula")
    linhas = []
    for r in s.itertuples(index=False):
        c = etapas.classificar(r.modalidade, r.segmento, r.serie)
        linhas.append({
            "modalidade_b": r.modalidade or NULO, "segmento_b": r.segmento or NULO, "serie_b": r.serie or NULO,
            "valido": c is not None,
            "modalidade": c.modalidade if c else None, "segmento": c.segmento if c else None,
            "serie": c.serie if c else None, "ciclo": c.ciclo if c else None,
            "ordem_serie": c.ordem_serie if c else None,
            "educacao_especial": c.educacao_especial if c else None,
            "codigo_etapa": c.etapa if c else None,
        })
    _registrar(con, "stgdb.stg.map_serie", pd.DataFrame(linhas))

    # turno: descrição, código de 2021 ou horário
    t = _df(con, "SELECT DISTINCT ano_letivo, desc_turno, cd_turno, hora_inicio, hora_fim FROM stgdb.stg.matricula")
    res = [n.resolver_turno(int(r.ano_letivo), r.desc_turno, r.cd_turno, r.hora_inicio, r.hora_fim)
           for r in t.itertuples(index=False)]
    t["turno"] = [x[0] for x in res]
    t["origem_turno"] = [x[1] for x in res]
    for c in ("desc_turno", "cd_turno", "hora_inicio", "hora_fim"):
        t[c] = t[c].map(lambda x: NULO if x is None else x)
    _registrar(con, "stgdb.stg.map_turno", t)

    # escolas: identificação entre anos e versões (SCD tipo 2)
    brutas = _df(con, """
        SELECT ano_letivo AS ano, cd_escola_origem AS cd_origem, nome_escola AS nome, tipo_escola AS tipo,
               distrito, dre, setor_sme AS setor, situacao_escola AS situacao, count(*) AS matriculas
        FROM stgdb.stg.matricula GROUP BY ALL""")
    identificadas = esc.identificar(esc.normalizar(brutas))
    versoes = esc.versionar(identificadas)
    mapa = esc.mapa_carga(identificadas, versoes)
    for c in ("cd_bruto", "nome_bruto", "tipo_bruto", "distrito_bruto"):
        mapa[c] = mapa[c].map(lambda x: NULO if x is None or (isinstance(x, float) and pd.isna(x)) else x)
    _registrar(con, "stgdb.stg.map_escola", mapa[["ano", "cd_bruto", "nome_bruto", "tipo_bruto", "distrito_bruto",
                                            "chave_escola", "vinculo"]])
    return {"identificadas": identificadas, "versoes": versoes,
            "qualidade": esc.avaliar_codigos(identificadas)}


def _preparar_matricula(con) -> tuple[int, int]:
    def_cod = " || ".join(_flag(f"s.def_{d}") for d in microdados.DEFICIENCIAS)
    sit_cod = " || ".join(_flag(f"s.sit_{k}") for k in situacao.INDICADORES)
    idade_sql = idade.sql_idade_inteiros("c.ano_letivo", "c._pub", "c._an", "c._mes")
    estimada_sql = idade.sql_idade_estimada_inteiros("c.ano_letivo", "c._pub", "c._an", "c._mes")
    ah = _flag("s.nee_altas_habilidades")
    con.execute(f"""
        CREATE OR REPLACE TABLE stgdb.stg.matricula_preparada AS
        WITH convertida AS (
            -- cada conversão cara é feita uma única vez por linha
            SELECT m.*,
                   {idade.sql_inteiro_br('m.idade_publicada')} AS _pub,
                   {idade.sql_inteiro_br('m.ano_nascimento')} AS _an,
                   {idade.sql_inteiro_br('m.mes_nascimento')} AS _mes,
                   {datas.sql_data_bruta('m.dt_inicio')} AS _dti,
                   {datas.sql_data_bruta('m.dt_fim')} AS _dtf
            FROM stgdb.stg.matricula m
        ), com_idade AS (
            SELECT c.*, {idade_sql} AS _idade, coalesce({estimada_sql}, false) AS _estimada
            FROM convertida c
        )
        SELECT
            s.ano_letivo,
            me.chave_escola,
            me.vinculo,
            ms.modalidade || '|' || coalesce(ms.segmento, '') || '|' || coalesce(ms.serie, '') AS chave_serie_nat,
            mt.turno, mt.origem_turno,
            s._idade AS idade,
            s._estimada AS idade_estimada,
            coalesce(mx.sexo, 'NAO INFORMADO') || '|' || coalesce(mr.raca_cor, 'NAO INFORMADA') || '|'
                || (CASE {ah} WHEN '1' THEN 'true' WHEN '0' THEN 'false' ELSE '-' END) || '|'
                || CAST(s._estimada AS VARCHAR) AS cod_perfil,
            {def_cod} AS cod_deficiencia,
            {sit_cod} || '|' || coalesce(msit.situacao, '') AS cod_situacao,
            upper(trim(s.nome_turma)) AS nome_turma,
            trim(s.cd_matricula_origem) AS cd_matricula,
            {idade.sql_inteiro_br('s.qtd_dias')} AS qtd_dias,
            s.dt_inicio IS NOT NULL AS tem_datas,
            {datas.sql_na_janela('s._dti', 's.ano_letivo')} AS data_inicio,
            {datas.sql_na_janela('s._dtf', 's.ano_letivo')} AS data_fim
        FROM com_idade s
        JOIN stgdb.stg.map_serie ms
          ON ms.modalidade_b = {_b('s.modalidade')} AND ms.segmento_b = {_b('s.segmento')}
         AND ms.serie_b = {_b('s.serie')}
        JOIN stgdb.stg.map_escola me
          ON me.ano = s.ano_letivo AND me.cd_bruto = {_b('s.cd_escola_origem')}
         AND me.nome_bruto = {_b('s.nome_escola')}
         AND me.tipo_bruto = {_b('s.tipo_escola')} AND me.distrito_bruto = {_b('s.distrito')}
        JOIN stgdb.stg.map_turno mt
          ON mt.ano_letivo = s.ano_letivo AND mt.desc_turno = {_b('s.desc_turno')} AND mt.cd_turno = {_b('s.cd_turno')}
         AND mt.hora_inicio = {_b('s.hora_inicio')} AND mt.hora_fim = {_b('s.hora_fim')}
        LEFT JOIN stgdb.stg.map_raca mr ON mr.bruto = {_b('s.raca_cor')}
        LEFT JOIN stgdb.stg.map_sexo mx ON mx.bruto = {_b('s.sexo')}
        LEFT JOIN stgdb.stg.map_situacao msit ON msit.bruto = {_b('s.situacao_matricula')}
        WHERE ms.valido
    """)
    preparadas = con.execute("SELECT count(*) FROM stgdb.stg.matricula_preparada").fetchone()[0]
    total = con.execute("SELECT count(*) FROM stgdb.stg.matricula").fetchone()[0]
    return preparadas, total - preparadas


# ----------------------------------------------------------------------------- dimensões

def _dim_tempo(con, cfg: Configuracao, fila_meta: list[dict]) -> None:
    meta = {m["periodo"]: m for m in fila_meta}
    linhas = []
    for ano in cfg.anos:
        for mes in range(1, 13):
            d = date(ano, mes, 1)
            m = meta.get(d.isoformat())
            obs = " | ".join(m["observacoes"]) if m and m["observacoes"] else None
            linhas.append({
                "chave_tempo": len(linhas) + 1, "data_referencia": d, "ano_mes": f"{ano}-{mes:02d}",
                "mes": mes, "nome_mes": _MESES[mes - 1], "bimestre": (mes - 1) // 2 + 1,
                "trimestre": (mes - 1) // 3 + 1, "semestre": (mes - 1) // 6 + 1, "ano": ano,
                "fila_publicada": m is not None, "observacao": obs,
            })
    con.register("_tmp", pd.DataFrame(linhas))
    con.execute("INSERT INTO dw.dim_tempo SELECT * FROM _tmp")
    con.unregister("_tmp")


def _dim_data(con, cfg: Configuracao) -> None:
    dias = datas.calendario(min(cfg.anos) - 1, max(cfg.anos) + 1)
    df = pd.DataFrame(dias)
    df.insert(0, "chave_data", range(1, len(df) + 1))
    con.register("_tmp", df)
    con.execute("INSERT INTO dw.dim_data SELECT * FROM _tmp")
    con.unregister("_tmp")
    con.execute("""INSERT INTO dw.dim_data (chave_data) SELECT max(chave_data) + 1 FROM dw.dim_data""")


def _dim_ano_letivo(con, qualidade: dict[int, str]) -> None:
    sql = "SELECT DISTINCT ano_letivo FROM stgdb.stg.matricula_preparada ORDER BY 1"
    anos = [r[0] for r in con.execute(sql).fetchall()]
    for i, ano in enumerate(anos, 1):
        con.execute("INSERT INTO dw.dim_ano_letivo VALUES (?, ?, ?, NULL)", [i, ano, qualidade[ano]])


def _dim_territorio(con, fila_df: pd.DataFrame) -> None:
    con.execute("""
        CREATE OR REPLACE TEMP TABLE _dre AS
        SELECT md.distrito, mr.dre, count(*) AS n
        FROM stgdb.stg.matricula s
        JOIN stgdb.stg.map_distrito md ON md.bruto = coalesce(s.distrito, '<nulo>')
        JOIN stgdb.stg.map_dre mr ON mr.bruto = coalesce(s.dre, '<nulo>')
        WHERE md.distrito IS NOT NULL AND mr.dre IS NOT NULL
        GROUP BY ALL""")
    con.register("_fila_d", pd.DataFrame({"distrito": sorted(set(fila_df["distrito"]))}))
    con.execute("""
        INSERT INTO dw.dim_territorio
        WITH distritos AS (
            SELECT distrito FROM _fila_d
            UNION SELECT distrito FROM stgdb.stg.map_distrito WHERE distrito IS NOT NULL
        ), pred AS (
            SELECT distrito, arg_max(dre, n) AS dre, max(n) / sum(n) AS participacao FROM _dre GROUP BY 1
        )
        SELECT row_number() OVER (ORDER BY d.distrito), d.distrito, p.dre, p.participacao, 'SAO PAULO', 'SP'
        FROM distritos d LEFT JOIN pred p USING (distrito)""")
    con.unregister("_fila_d")
    con.execute("""INSERT INTO dw.dim_territorio
                   SELECT max(chave_territorio) + 1, 'NAO INFORMADO', NULL, NULL, 'SAO PAULO', 'SP'
                   FROM dw.dim_territorio""")


def _dim_escola(con, versoes: pd.DataFrame) -> None:
    con.register("_tmp", versoes)
    con.execute("INSERT INTO dw.dim_escola SELECT * FROM _tmp")
    con.unregister("_tmp")


def _dim_etapa_e_serie(con) -> None:
    for e in etapas.ETAPAS:
        con.execute("INSERT INTO dw.dim_etapa VALUES (?, ?, ?, ?, ?)", [e.ordem, e.codigo, e.nome, e.nivel, e.ordem])
    con.execute("""
        INSERT INTO dw.dim_serie
        SELECT row_number() OVER (ORDER BY e.ordem, ms.ordem_serie NULLS LAST, ms.modalidade, ms.segmento, ms.serie),
               ms.modalidade, ms.segmento, ms.serie, ms.ciclo, ms.ordem_serie, ms.educacao_especial,
               ms.codigo_etapa, e.etapa, e.nivel
        FROM (SELECT DISTINCT modalidade, segmento, serie, ciclo, ordem_serie, educacao_especial, codigo_etapa
              FROM stgdb.stg.map_serie WHERE valido) ms
        JOIN dw.dim_etapa e ON e.codigo = ms.codigo_etapa""")


def _dim_turno(con) -> None:
    sql = "SELECT DISTINCT turno, origem_turno FROM stgdb.stg.matricula_preparada ORDER BY 1, 2"
    for i, (t, origem) in enumerate(con.execute(sql).fetchall(), 1):
        jornada = n.jornada(t if t in n.TURNOS else None)
        con.execute("INSERT INTO dw.dim_turno VALUES (?, ?, ?, ?)", [i, t, jornada, origem])


def _dim_idade(con) -> None:
    valores = list(range(0, idade.IDADE_MAXIMA + 1)) + [None]
    for i, v in enumerate(valores, 1):
        con.execute("INSERT INTO dw.dim_idade VALUES (?, ?, ?, ?, ?)",
                    [i, v, idade.faixa_escolar(v), idade.faixa_ibge(v), idade.grupo_etario(v)])


def _dims_bugiganga(con) -> None:
    con.execute("""
        INSERT INTO dw.dim_perfil_aluno
        SELECT row_number() OVER (ORDER BY cod_perfil), cod_perfil,
               split_part(cod_perfil, '|', 1), split_part(cod_perfil, '|', 2),
               CASE split_part(cod_perfil, '|', 3) WHEN 'true' THEN true WHEN 'false' THEN false END,
               split_part(cod_perfil, '|', 4) = 'true'
        FROM (SELECT DISTINCT cod_perfil FROM stgdb.stg.matricula_preparada)""")
    flags = ", ".join(_bool_da_posicao("cod", i + 1) for i in range(len(microdados.DEFICIENCIAS)))
    con.execute(f"""
        INSERT INTO dw.dim_deficiencia
        SELECT row_number() OVER (ORDER BY cod), cod, position('1' IN cod) > 0,
               length(cod) - length(replace(cod, '1', '')), {flags}
        FROM (SELECT DISTINCT cod_deficiencia AS cod FROM stgdb.stg.matricula_preparada)""")
    posicao = {k: i + 1 for i, k in enumerate(situacao.INDICADORES)}
    desfecho = situacao.sql_desfecho(lambda k: _bool_da_posicao("cod", posicao[k]))
    flags_sit = ", ".join(_bool_da_posicao("cod", i) for i in posicao.values())
    con.execute(f"""
        INSERT INTO dw.dim_situacao_matricula
        SELECT row_number() OVER (ORDER BY cod), cod, NULLIF(split_part(cod, '|', 2), ''), {desfecho}, {flags_sit}
        FROM (SELECT DISTINCT cod_situacao AS cod FROM stgdb.stg.matricula_preparada)""")


# ----------------------------------------------------------------------------- fatos

def _fato_matricula(con) -> int:
    con.execute("""
        INSERT INTO dw.fato_matricula
        SELECT
            al.chave_ano_letivo,
            coalesce(dti.chave_data, dni.chave_data),
            coalesce(dtf.chave_data, dni.chave_data),
            p.chave_escola,
            coalesce(t.chave_territorio, tni.chave_territorio),
            ds.chave_serie,
            dt.chave_turno,
            di.chave_idade,
            dp.chave_perfil_aluno,
            dd.chave_deficiencia,
            dsit.chave_situacao,
            concat_ws('-', p.ano_letivo, p.chave_escola, coalesce(p.nome_turma, '?'), ds.chave_serie, dt.chave_turno),
            CASE WHEN al.qualidade_codigo_escola = 'CORROMPIDO' THEN NULL ELSE p.cd_matricula END,
            1,
            p.qtd_dias
        FROM stgdb.stg.matricula_preparada p
        JOIN dw.dim_ano_letivo al ON al.ano = p.ano_letivo
        JOIN dw.dim_escola e ON e.chave_escola = p.chave_escola
        LEFT JOIN dw.dim_territorio t ON t.distrito = e.distrito
        CROSS JOIN (SELECT chave_territorio FROM dw.dim_territorio WHERE distrito = 'NAO INFORMADO') tni
        CROSS JOIN (SELECT chave_data FROM dw.dim_data WHERE data IS NULL) dni
        LEFT JOIN dw.dim_data dti ON dti.data = p.data_inicio
        LEFT JOIN dw.dim_data dtf ON dtf.data = p.data_fim
        JOIN dw.dim_serie ds
          ON ds.modalidade || '|' || coalesce(ds.segmento, '') || '|' || coalesce(ds.serie, '') = p.chave_serie_nat
        JOIN dw.dim_turno dt ON dt.turno = p.turno AND dt.origem_turno = p.origem_turno
        JOIN dw.dim_idade di ON coalesce(di.idade, -1) = coalesce(p.idade, -1)
        JOIN dw.dim_perfil_aluno dp ON dp.codigo_combinacao = p.cod_perfil
        JOIN dw.dim_deficiencia dd ON dd.codigo_combinacao = p.cod_deficiencia
        JOIN dw.dim_situacao_matricula dsit ON dsit.codigo_combinacao = p.cod_situacao""")
    return con.execute("SELECT count(*) FROM dw.fato_matricula").fetchone()[0]


def _fato_fila(con, fila_df: pd.DataFrame) -> int:
    df = fila_df.copy()
    df["periodo"] = pd.to_datetime(df["periodo"]).dt.date
    con.register("_fila", df)
    con.execute("""
        INSERT INTO dw.fato_fila
        SELECT t.chave_tempo, d.chave_territorio, e.chave_etapa, f.layout,
               f.matriculas, f.matriculas_em_processo, f.demanda_total, f.demanda_sem_opcao,
               f.demanda_sem_opcao_ate_30d, f.demanda_sem_opcao_mais_30d, f.demanda_com_opcao
        FROM _fila f
        JOIN dw.dim_tempo t ON t.data_referencia = f.periodo
        JOIN dw.dim_territorio d ON d.distrito = f.distrito
        JOIN dw.dim_etapa e ON e.codigo = f.etapa""")
    con.unregister("_fila")
    return con.execute("SELECT count(*) FROM dw.fato_fila").fetchone()[0]


def _fato_desfecho(con) -> int:
    contagens = {
        "qtd_aprovados": "APROVADO", "qtd_reprovados": "REPROVADO", "qtd_abandonos": "ABANDONO",
        "qtd_transferidos": "TRANSFERIDO", "qtd_concluintes": "CONCLUIDO", "qtd_falecidos": "FALECIDO",
        "qtd_outras_saidas": "OUTRA SAIDA", "qtd_em_curso": "EM CURSO", "qtd_sem_desfecho": "SEM DESFECHO",
    }
    medidas = ",\n".join(f"count(*) FILTER (WHERE s.desfecho = '{v}')" for v in contagens.values())
    con.execute(f"""
        INSERT INTO dw.fato_desfecho
        SELECT f.chave_ano_letivo, f.chave_escola, f.chave_territorio, f.chave_serie, count(*), {medidas}
        FROM dw.fato_matricula f JOIN dw.dim_situacao_matricula s USING (chave_situacao)
        GROUP BY ALL""")
    return con.execute("SELECT count(*) FROM dw.fato_desfecho").fetchone()[0]


# ----------------------------------------------------------------------------- qualidade por ano

def _observacoes_ano(con, identificadas: pd.DataFrame) -> None:
    """Escreve em dim_ano_letivo as limitações do microdado de cada ano, medidas no próprio dado."""
    vinculo = esc.resumo_vinculo(identificadas)
    metricas = _df(con, """
        SELECT p.ano_letivo AS ano,
               avg(CASE WHEN p.origem_turno <> 'PUBLICADO' THEN 1.0 ELSE 0 END) AS turno_nao_publicado,
               max(CASE WHEN p.tem_datas THEN 1 ELSE 0 END) AS tem_datas,
               avg(CASE WHEN p.idade_estimada THEN 1.0 ELSE 0 END) AS idade_estimada,
               avg(CASE WHEN s.desfecho = 'EM CURSO' THEN 1.0 ELSE 0 END) AS em_curso
        FROM stgdb.stg.matricula_preparada p
        JOIN dw.dim_situacao_matricula s ON s.codigo_combinacao = p.cod_situacao
        GROUP BY 1""")
    qualidade = dict(con.execute("SELECT ano, qualidade_codigo_escola FROM dw.dim_ano_letivo").fetchall())
    for r in metricas.itertuples(index=False):
        notas = []
        if qualidade[r.ano] != esc.CONFIAVEL:
            linha = vinculo.loc[r.ano]
            ligadas = (linha[esc.PUBLICADO] + linha[esc.RECUPERADO]) / linha.sum()
            situacao_codigo = "corrompido" if qualidade[r.ano] == esc.CORROMPIDO else "fora do padrão"
            notas.append(f"Código da escola {situacao_codigo} no arquivo publicado: {100 * ligadas:.1f}% das "
                         "matrículas ligadas ao código real pelo nome, tipo e distrito; "
                         "o restante com chave sintética.")
        if r.turno_nao_publicado > 0.5:
            notas.append("Turno não publicado; derivado do código da turma ou do horário.")
        if not r.tem_datas:
            notas.append("Datas e duração da matrícula não publicadas.")
        if r.idade_estimada > 0.01:
            notas.append(f"{100 * r.idade_estimada:.1f}% das idades estimadas só pelo ano de nascimento.")
        if r.em_curso > 0.3:
            notas.append(f"Retrato publicado antes do fim do ano letivo: {100 * r.em_curso:.0f}% das matrículas "
                         f"ainda em curso, o que subestima aprovação, reprovação e abandono.")
        if notas:
            con.execute("UPDATE dw.dim_ano_letivo SET observacao = ? WHERE ano = ?", [" ".join(notas), r.ano])


# ----------------------------------------------------------------------------- orquestração

def carregar_tudo(cfg: Configuracao) -> dict:
    inicio = time.time()
    cfg.banco.parent.mkdir(parents=True, exist_ok=True)
    staging = cfg.dir_dados / "interim" / "staging.duckdb"
    staging.parent.mkdir(parents=True, exist_ok=True)
    staging.unlink(missing_ok=True)
    con = duckdb.connect(str(cfg.banco))
    try:
        criar_esquema(con)
        con.execute(f"ATTACH '{staging.as_posix()}' AS stgdb")
        cfg.log("  staging do microdado")
        linhas_staging = _staging_matricula(con, cfg)
        cfg.log("  tabelas de correspondência e identificação das escolas")
        aux = _mapas(con)
        preparadas, excluidas = _preparar_matricula(con)
        cfg.log("  planilhas de fila")
        fila_df, fila_meta = preparar_fila(cfg)

        cfg.log("  dimensões")
        _dim_tempo(con, cfg, fila_meta)
        _dim_data(con, cfg)
        _dim_ano_letivo(con, aux["qualidade"])
        _dim_territorio(con, fila_df)
        _dim_escola(con, aux["versoes"])
        _dim_etapa_e_serie(con)
        _dim_turno(con)
        _dim_idade(con)
        _dims_bugiganga(con)

        cfg.log("  fatos")
        resumo: dict[str, object] = {
            "linhas_staging": linhas_staging,
            "excluidas_sem_etapa": excluidas,
            "fato_matricula": _fato_matricula(con),
            "fato_fila": _fato_fila(con, fila_df),
            "fato_desfecho": _fato_desfecho(con),
        }
        _observacoes_ano(con, aux["identificadas"])
        for tabela in ("dim_tempo", "dim_data", "dim_ano_letivo", "dim_territorio", "dim_escola", "dim_etapa",
                       "dim_serie", "dim_turno", "dim_idade", "dim_perfil_aluno", "dim_deficiencia",
                       "dim_situacao_matricula"):
            resumo[tabela] = con.execute(f"SELECT count(*) FROM dw.{tabela}").fetchone()[0]
        resumo["vinculo_escola"] = esc.resumo_vinculo(aux["identificadas"]).astype(int).to_dict(orient="index")
        resumo["fila_metadados"] = fila_meta
        con.execute("DETACH stgdb")
        if not cfg.manter_staging:
            staging.unlink(missing_ok=True)
        con.execute("CHECKPOINT")
        resumo["segundos"] = round(time.time() - inicio, 1)
        return resumo
    finally:
        con.close()
