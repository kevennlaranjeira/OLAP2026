-- codigo: C6
-- tipo: drill-across
-- titulo: Fila de creche e abandono no fundamental por DRE
-- pergunta: As regiões com mais crianças esperando vaga em creche em junho são as mesmas em que mais alunos abandonam o ensino fundamental ao longo do ano?
-- justificativa: Fila e abandono são sintomas diferentes de vulnerabilidade territorial: falta de vaga no começo da trajetória escolar e evasão no meio dela. A consulta cruza três tabelas de fatos, cada uma agregada até DRE e ano: fila de creche (fato_fila), matrículas de creche (fato_matricula, para pôr a fila em escala) e desfecho no ensino fundamental (fato_desfecho). Para a fila, que só tem distrito, a subida até DRE usa a hierarquia integrada da dimensão Território. A taxa de abandono é recalculada a partir das contagens e restrita ao fundamental, onde o indicador é o mesmo do INEP; na educação infantil não existe aprovação.
-- fatos: fato_fila, fato_matricula, fato_desfecho
WITH fila AS (
    SELECT t.ano, d.dre, sum(f.qtd_demanda_total) AS fila_creche_junho
    FROM dw.fato_fila f
    JOIN dw.dim_tempo t      ON t.chave_tempo = f.chave_tempo
    JOIN dw.dim_territorio d ON d.chave_territorio = f.chave_territorio
    JOIN dw.dim_etapa e      ON e.chave_etapa = f.chave_etapa
    WHERE t.mes = 6 AND e.codigo = 'CRECHE'
    GROUP BY ALL
),
creche AS (
    SELECT a.ano, d.dre, sum(f.qtd_matricula) AS matriculas_creche
    FROM dw.fato_matricula f
    JOIN dw.dim_ano_letivo a ON a.chave_ano_letivo = f.chave_ano_letivo
    JOIN dw.dim_territorio d ON d.chave_territorio = f.chave_territorio
    JOIN dw.dim_serie s      ON s.chave_serie = f.chave_serie
    WHERE s.codigo_etapa = 'CRECHE'
    GROUP BY ALL
),
fundamental AS (
    SELECT a.ano, d.dre,
           sum(x.qtd_abandonos)                                      AS abandonos_fundamental,
           sum(x.qtd_aprovados + x.qtd_reprovados + x.qtd_abandonos) AS base_rendimento
    FROM dw.fato_desfecho x
    JOIN dw.dim_ano_letivo a ON a.chave_ano_letivo = x.chave_ano_letivo
    JOIN dw.dim_territorio d ON d.chave_territorio = x.chave_territorio
    JOIN dw.dim_serie s      ON s.chave_serie = x.chave_serie
    WHERE s.nivel = 'ENSINO FUNDAMENTAL'
    GROUP BY ALL
),
eixo AS (
    SELECT ano, dre FROM fila UNION SELECT ano, dre FROM creche UNION SELECT ano, dre FROM fundamental
)
SELECT
    e.ano,
    coalesce(e.dre, '(SEM DRE)')                                                    AS dre,
    c.matriculas_creche,
    fl.fila_creche_junho,
    round(fl.fila_creche_junho * 1000.0 / NULLIF(c.matriculas_creche, 0), 1)       AS fila_por_mil_matriculas_creche,
    fu.abandonos_fundamental,
    round(fu.abandonos_fundamental / NULLIF(fu.base_rendimento, 0), 4)              AS taxa_abandono_fundamental
FROM eixo e
LEFT JOIN fila fl        ON fl.ano = e.ano AND fl.dre IS NOT DISTINCT FROM e.dre
LEFT JOIN creche c       ON c.ano = e.ano AND c.dre IS NOT DISTINCT FROM e.dre
LEFT JOIN fundamental fu ON fu.ano = e.ano AND fu.dre IS NOT DISTINCT FROM e.dre
ORDER BY e.ano, fila_por_mil_matriculas_creche DESC NULLS LAST, e.dre NULLS LAST;
