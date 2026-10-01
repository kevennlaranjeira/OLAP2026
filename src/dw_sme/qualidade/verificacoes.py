"""Verificações de qualidade sobre o data warehouse carregado.

FALHA: algo que o modelo garante e que não pode acontecer (chave órfã,
versões de escola sobrepostas, desfecho que não soma o total).
ALERTA: limitação ou defeito conhecido da fonte, registrado para ficar visível.
OK: verificado sem ressalvas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import duckdb
import pandas as pd

OK, ALERTA, FALHA = "OK", "ALERTA", "FALHA"

# fato -> [(coluna, dimensão, chave primária da dimensão)]
CHAVES_ESTRANGEIRAS = {
    "fato_matricula": [
        ("chave_ano_letivo", "dim_ano_letivo", "chave_ano_letivo"),
        ("chave_data_inicio", "dim_data", "chave_data"),
        ("chave_data_fim", "dim_data", "chave_data"),
        ("chave_escola", "dim_escola", "chave_escola"),
        ("chave_territorio", "dim_territorio", "chave_territorio"),
        ("chave_serie", "dim_serie", "chave_serie"),
        ("chave_turno", "dim_turno", "chave_turno"),
        ("chave_idade", "dim_idade", "chave_idade"),
        ("chave_perfil_aluno", "dim_perfil_aluno", "chave_perfil_aluno"),
        ("chave_deficiencia", "dim_deficiencia", "chave_deficiencia"),
        ("chave_situacao", "dim_situacao_matricula", "chave_situacao"),
    ],
    "fato_fila": [
        ("chave_tempo", "dim_tempo", "chave_tempo"),
        ("chave_territorio", "dim_territorio", "chave_territorio"),
        ("chave_etapa", "dim_etapa", "chave_etapa"),
    ],
    "fato_desfecho": [
        ("chave_ano_letivo", "dim_ano_letivo", "chave_ano_letivo"),
        ("chave_escola", "dim_escola", "chave_escola"),
        ("chave_territorio", "dim_territorio", "chave_territorio"),
        ("chave_serie", "dim_serie", "chave_serie"),
    ],
}
ETAPAS_RECONCILIADAS = ("CRECHE", "PRE", "FUND_I", "FUND_II")
TOLERANCIA_RECONCILIACAO = 0.02


@dataclass
class Verificacao:
    codigo: str
    titulo: str
    status: str
    resumo: str
    detalhe: pd.DataFrame | None = field(default=None, repr=False)


def _df(con, sql: str) -> pd.DataFrame:
    return con.execute(sql).df()


# ----------------------------------------------------------------------------- verificações

def integridade(con, chaves=CHAVES_ESTRANGEIRAS) -> Verificacao:
    linhas = []
    for fato, fks in chaves.items():
        for coluna, dim, pk in fks:
            orfas = con.execute(f"""SELECT count(*) FROM dw.{fato} f LEFT JOIN dw.{dim} d ON d.{pk} = f.{coluna}
                                    WHERE d.{pk} IS NULL""").fetchone()[0]
            linhas.append({"fato": fato, "chave": coluna, "dimensao": dim, "orfas": orfas})
    det = pd.DataFrame(linhas)
    total = int(det["orfas"].sum())
    return Verificacao("Q01", "Integridade referencial", FALHA if total else OK,
                       f"{len(det)} chaves estrangeiras conferidas; {total} linhas órfãs.", det)


def versoes_escola(con) -> Verificacao:
    sobrepostas = con.execute("""
        SELECT count(*) FROM dw.dim_escola a JOIN dw.dim_escola b
          ON a.cod_escola = b.cod_escola AND a.versao < b.versao AND a.ano_fim >= b.ano_inicio""").fetchone()[0]
    sem_atual = con.execute("""
        SELECT count(*) FROM (
            SELECT cod_escola FROM dw.dim_escola GROUP BY 1 HAVING sum(versao_atual::INT) <> 1)""").fetchone()[0]
    fora = con.execute("""
        SELECT count(*) FROM dw.fato_matricula f JOIN dw.dim_escola e USING (chave_escola)
        JOIN dw.dim_ano_letivo a USING (chave_ano_letivo)
        WHERE a.ano NOT BETWEEN e.ano_inicio AND e.ano_fim""").fetchone()[0]
    det = _df(con, """SELECT count(DISTINCT cod_escola) AS escolas, count(*) AS versoes,
                             count(*) FILTER (WHERE versao > 1) AS versoes_adicionais,
                             count(DISTINCT cod_escola) FILTER (WHERE codigo_sintetico) AS escolas_sinteticas
                      FROM dw.dim_escola""")
    problemas = sobrepostas + sem_atual + fora
    return Verificacao("Q02", "Versões da dimensão Escola (SCD tipo 2)", FALHA if problemas else OK,
                       f"{sobrepostas} sobreposições de vigência, {sem_atual} escolas sem exatamente uma versão "
                       f"atual, {fora} matrículas apontando para versão fora da vigência.", det)


def conservacao(con) -> Verificacao:
    det = _df(con, """
        SELECT (SELECT sum(qtd_matricula) FROM dw.fato_matricula) AS matriculas_no_fato_matricula,
               (SELECT sum(qtd_matriculas) FROM dw.fato_desfecho) AS matriculas_no_fato_desfecho,
               (SELECT count(*) FROM dw.fato_desfecho
                 WHERE qtd_aprovados + qtd_reprovados + qtd_abandonos + qtd_transferidos + qtd_concluintes
                     + qtd_falecidos + qtd_outras_saidas + qtd_em_curso + qtd_sem_desfecho <> qtd_matriculas)
                   AS linhas_desfecho_que_nao_somam""")
    r = det.iloc[0]
    ok = r.matriculas_no_fato_matricula == r.matriculas_no_fato_desfecho and r.linhas_desfecho_que_nao_somam == 0
    return Verificacao("Q03", "Conservação entre fato de matrícula e fato de desfecho", OK if ok else FALHA,
                       f"{int(r.matriculas_no_fato_matricula):,} matrículas no fato de matrícula e "
                       f"{int(r.matriculas_no_fato_desfecho):,} no fato de desfecho.".replace(",", "."), det)


def completude_fila(con) -> Verificacao:
    det = _df(con, """
        SELECT t.ano_mes, any_value(f.formato_planilha) AS formato,
               count(DISTINCT f.chave_territorio) AS distritos, count(DISTINCT f.chave_etapa) AS etapas,
               count(*) AS linhas
        FROM dw.fato_fila f JOIN dw.dim_tempo t USING (chave_tempo) GROUP BY 1 ORDER BY 1""")
    esperado = int(det["linhas"].max()) if len(det) else 0
    incompletos = det[det["linhas"] < esperado]
    return Verificacao("Q04", "Completude da fila por período", ALERTA if len(incompletos) else OK,
                       f"{len(det)} meses publicados no recorte; {len(incompletos)} com menos que "
                       f"{int(det['distritos'].max()) if len(det) else 0} distritos x "
                       f"{int(det['etapas'].max()) if len(det) else 0} etapas.", det)


def totais_publicados(fila_meta: list[dict]) -> Verificacao:
    linhas = [{"periodo": m["periodo"], "arquivo": m["arquivo"], "divergencia": d}
              for m in fila_meta for d in m.get("divergencias_total", [])]
    det = pd.DataFrame(linhas, columns=["periodo", "arquivo", "divergencia"])
    return Verificacao("Q05", "Soma dos distritos contra a linha TOTAL da planilha", ALERTA if linhas else OK,
                       f"{len(linhas)} divergências entre a soma dos distritos e a linha TOTAL publicada, em "
                       f"{det['arquivo'].nunique()} arquivo(s). Defeito da fonte; o valor por distrito é mantido.", det)


def total_e_partes(fila_meta: list[dict]) -> Verificacao:
    linhas = [{"periodo": m["periodo"], "arquivo": m["arquivo"], "inconsistencias": len(m.get("inconsistencias", []))}
              for m in fila_meta if m.get("inconsistencias")]
    det = pd.DataFrame(linhas, columns=["periodo", "arquivo", "inconsistencias"])
    total = int(det["inconsistencias"].sum()) if len(det) else 0
    return Verificacao("Q06", "Total da fila contra a soma das categorias", ALERTA if total else OK,
                       f"{total} distritos-etapa em que o total publicado difere da soma das categorias "
                       f"(sem opção até 30 dias, mais de 30 dias, com opção). O total publicado prevalece.", det)


def reconciliacao(con) -> Verificacao:
    """Matrículas ativas no fim de junho (microdado) contra a coluna de matrícula da fila de junho."""
    det = _df(con, f"""
        WITH ref AS (SELECT ano, data_referencia, last_day(data_referencia) AS corte
                     FROM dw.dim_tempo WHERE mes = 6 AND fila_publicada),
        anos_com_datas AS (
            SELECT a.ano FROM dw.fato_matricula f JOIN dw.dim_ano_letivo a USING (chave_ano_letivo)
            JOIN dw.dim_data d ON d.chave_data = f.chave_data_inicio GROUP BY 1 HAVING count(d.data) > 0),
        md AS (
            SELECT a.ano, s.codigo_etapa AS etapa, f.chave_territorio, sum(f.qtd_matricula) AS n
            FROM dw.fato_matricula f JOIN dw.dim_ano_letivo a USING (chave_ano_letivo)
            JOIN dw.dim_serie s USING (chave_serie)
            JOIN dw.dim_data di ON di.chave_data = f.chave_data_inicio
            JOIN dw.dim_data df ON df.chave_data = f.chave_data_fim
            JOIN ref r ON r.ano = a.ano
            WHERE di.data <= r.corte AND (df.data IS NULL OR df.data > r.corte)
            GROUP BY ALL),
        fl AS (
            SELECT t.ano, e.codigo AS etapa, f.chave_territorio, f.qtd_matriculas AS n
            FROM dw.fato_fila f JOIN dw.dim_tempo t USING (chave_tempo)
            JOIN ref r ON r.data_referencia = t.data_referencia
            JOIN dw.dim_etapa e USING (chave_etapa))
        SELECT fl.ano, fl.etapa,
               sum(coalesce(md.n, 0)) AS microdado_ativas_30_06, sum(fl.n) AS planilha_fila,
               round(sum(coalesce(md.n, 0)) / NULLIF(sum(fl.n), 0) - 1, 4) AS diferenca,
               avg(CASE WHEN abs(coalesce(md.n, 0) / NULLIF(fl.n, 0) - 1) <= {TOLERANCIA_RECONCILIACAO}
                        THEN 1.0 ELSE 0 END) AS fracao_distritos_na_tolerancia
        FROM fl LEFT JOIN md USING (ano, etapa, chave_territorio)
        WHERE fl.ano IN (SELECT ano FROM anos_com_datas)
          AND fl.etapa IN {ETAPAS_RECONCILIADAS} AND fl.n > 0
        GROUP BY ALL ORDER BY 1, 2""")
    if det.empty:
        return Verificacao("Q07", "Reconciliação entre as duas bases (junho)", OK,
                           "Nenhum ano com fila de junho e datas de matrícula ao mesmo tempo; nada a reconciliar.", det)
    fora = det[det["diferenca"].abs() > TOLERANCIA_RECONCILIACAO]
    return Verificacao("Q07", "Reconciliação entre as duas bases (junho)", ALERTA if len(fora) else OK,
                       f"{len(det)} combinações ano x etapa reconciliadas; {len(fora)} com diferença acima de "
                       f"{TOLERANCIA_RECONCILIACAO:.0%}. Mediana da diferença absoluta: "
                       f"{det['diferenca'].abs().median():.2%}.", det)


def vinculo_escolas(con) -> Verificacao:
    det = _df(con, """
        SELECT a.ano, a.qualidade_codigo_escola, sum(f.qtd_matricula) AS matriculas,
               round(sum(f.qtd_matricula) FILTER (WHERE e.codigo_sintetico) / sum(f.qtd_matricula), 4)
                   AS fracao_escola_sintetica
        FROM dw.fato_matricula f JOIN dw.dim_ano_letivo a USING (chave_ano_letivo)
        JOIN dw.dim_escola e USING (chave_escola) GROUP BY 1, 2 ORDER BY 1""")
    det["fracao_escola_sintetica"] = det["fracao_escola_sintetica"].fillna(0)
    pior = det["fracao_escola_sintetica"].max() if len(det) else 0
    return Verificacao("Q08", "Identificação das escolas por ano", ALERTA if pior > 0.10 else OK,
                       f"Maior fração de matrículas em escola com chave sintética num ano: {pior:.1%}.", det)


def membros_desconhecidos(con) -> Verificacao:
    det = _df(con, """
        SELECT a.ano,
               avg(CASE WHEN tr.distrito = 'NAO INFORMADO' THEN 1.0 ELSE 0 END) AS sem_territorio,
               avg(CASE WHEN i.idade IS NULL THEN 1.0 ELSE 0 END) AS sem_idade,
               avg(CASE WHEN t.turno = 'NAO INFORMADO' THEN 1.0 ELSE 0 END) AS sem_turno,
               avg(CASE WHEN d.data IS NULL THEN 1.0 ELSE 0 END) AS sem_data_inicio
        FROM dw.fato_matricula f JOIN dw.dim_ano_letivo a USING (chave_ano_letivo)
        JOIN dw.dim_territorio tr USING (chave_territorio) JOIN dw.dim_idade i USING (chave_idade)
        JOIN dw.dim_turno t USING (chave_turno) JOIN dw.dim_data d ON d.chave_data = f.chave_data_inicio
        GROUP BY 1 ORDER BY 1""")
    sem_territorio = det["sem_territorio"].max() if len(det) else 0
    return Verificacao("Q09", "Membros 'não informado' no fato de matrícula",
                       ALERTA if sem_territorio > 0.001 else OK,
                       "Fração das matrículas que caem no membro desconhecido de cada dimensão, por ano.", det)


def observacoes_ano(con) -> Verificacao:
    det = _df(con, "SELECT ano, qualidade_codigo_escola, observacao FROM dw.dim_ano_letivo ORDER BY ano")
    com_ressalva = det["observacao"].notna().sum()
    return Verificacao("Q10", "Limitações do microdado por ano letivo", ALERTA if com_ressalva else OK,
                       f"{com_ressalva} de {len(det)} anos com alguma limitação registrada na dimensão Ano Letivo.",
                       det)


def verificar(con: duckdb.DuckDBPyConnection, fila_meta: list[dict]) -> list[Verificacao]:
    return [integridade(con), versoes_escola(con), conservacao(con), completude_fila(con),
            totais_publicados(fila_meta), total_e_partes(fila_meta), reconciliacao(con),
            vinculo_escolas(con), membros_desconhecidos(con), observacoes_ano(con)]


# ----------------------------------------------------------------------------- relatório

def _formatar(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, float):
        return f"{v:.4f}".rstrip("0").rstrip(".") if abs(v) < 1 else f"{v:,.0f}".replace(",", ".")
    if isinstance(v, int) and not isinstance(v, bool):
        return f"{v:,}".replace(",", ".")
    return str(v).replace("|", "/")


def tabela_markdown(df: pd.DataFrame, limite: int = 60) -> str:
    if df is None or df.empty:
        return "_sem linhas_\n"
    corpo = df.head(limite)
    linhas = ["| " + " | ".join(str(c) for c in corpo.columns) + " |",
              "|" + "|".join("---" for _ in corpo.columns) + "|"]
    for r in corpo.itertuples(index=False):
        linhas.append("| " + " | ".join(_formatar(v.item() if hasattr(v, "item") else v) for v in r) + " |")
    if len(df) > limite:
        linhas.append(f"\n_… mais {len(df) - limite} linhas_")
    return "\n".join(linhas) + "\n"


def relatorio_markdown(verificacoes: list[Verificacao], resumo_carga: dict | None = None) -> str:
    partes = ["# Relatório de qualidade do data warehouse", "",
              f"Gerado em {datetime.now().astimezone():%d/%m/%Y %H:%M} pelo comando `dw-sme verificar`.", ""]
    if resumo_carga:
        partes += ["## Volumes carregados", "",
                   tabela_markdown(pd.DataFrame(
                       [{"tabela": k, "linhas": v} for k, v in resumo_carga.items() if isinstance(v, int)])), ""]
    partes += ["## Resumo", "", tabela_markdown(pd.DataFrame(
        [{"código": v.codigo, "verificação": v.titulo, "situação": v.status} for v in verificacoes])), ""]
    for v in verificacoes:
        partes += [f"## {v.codigo} · {v.titulo} · {v.status}", "", v.resumo, ""]
        if v.detalhe is not None and not v.detalhe.empty:
            partes += [tabela_markdown(v.detalhe), ""]
    return "\n".join(partes)
