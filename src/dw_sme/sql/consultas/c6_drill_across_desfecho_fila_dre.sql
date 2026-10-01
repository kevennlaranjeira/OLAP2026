-- codigo: C6
-- tipo: drill-across
-- titulo: Abandono, fila e tamanho da rede por DRE
-- pergunta: As regiões com mais crianças na fila em junho são as mesmas em que mais alunos abandonam a escola ao longo do ano?
-- justificativa: Fila e abandono são sintomas diferentes da mesma vulnerabilidade territorial: falta de vaga no começo da trajetória escolar e evasão no meio dela. A consulta cruza três tabelas de fatos (fila, desfecho e matrícula), cada uma agregada até DRE e ano. Para a fila, que só tem distrito, a subida até DRE usa a hierarquia integrada da dimensão Território. A taxa de abandono é recalculada a partir das contagens, nunca como média de taxas.
-- fatos: fato_fila, fato_desfecho, fato_matricula
WITH fila AS (
    SELECT t.ano, d.dre, sum(f.qtd_demanda_total) AS fila_junho
    FROM dw.fato_fila f
    JOIN dw.dim_tempo t      ON t.chave_tempo = f.chave_tempo
    JOIN dw.dim_territorio d ON d.chave_territorio = f.chave_territorio
    WHERE t.mes = 6
    GROUP BY ALL
),
desfecho AS (
    SELECT a.ano, d.dre,
           sum(x.qtd_abandonos)                                         AS abandonos,
           sum(x.qtd_aprovados + x.qtd_reprovados + x.qtd_abandonos)    AS base_rendimento
    FROM dw.fato_desfecho x
    JOIN dw.dim_ano_letivo a ON a.chave_ano_letivo = x.chave_ano_letivo
    JOIN dw.dim_territorio d ON d.chave_territorio = x.chave_territorio
    GROUP BY ALL
),
matricula AS (
    SELECT a.ano, d.dre, sum(f.qtd_matricula) AS matriculas
    FROM dw.fato_matricula f
    JOIN dw.dim_ano_letivo a ON a.chave_ano_letivo = f.chave_ano_letivo
    JOIN dw.dim_territorio d ON d.chave_territorio = f.chave_territorio
    GROUP BY ALL
)
SELECT
    m.ano,
    coalesce(m.dre, '(SEM DRE)')                           AS dre,
    m.matriculas,
    fl.fila_junho,
    ds.abandonos,
    round(ds.abandonos / NULLIF(ds.base_rendimento, 0), 4) AS taxa_abandono,
    round(fl.fila_junho * 1000.0 / NULLIF(m.matriculas, 0), 2) AS fila_por_mil_matriculas
FROM matricula m
LEFT JOIN desfecho ds ON ds.ano = m.ano AND ds.dre IS NOT DISTINCT FROM m.dre
LEFT JOIN fila fl     ON fl.ano = m.ano AND fl.dre IS NOT DISTINCT FROM m.dre
ORDER BY m.ano, taxa_abandono DESC NULLS LAST;
