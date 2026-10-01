-- codigo: C5
-- tipo: drill-across
-- titulo: Pressão de demanda por distrito: fila contra matrículas ativas em junho
-- pergunta: Em cada distrito e ano, quantas crianças esperavam vaga em creche ou pré-escola em junho, contra quantas estavam matriculadas na mesma data, e qual a fração da demanda que ficou de fora?
-- justificativa: É a pergunta central do tema. Duas tabelas de fatos com grãos diferentes (fila por distrito, mês e etapa; matrícula por vínculo aluno-turma) são agregadas separadamente até um grão comum e unidas pelas dimensões conformadas: território (distrito), etapa (dim_etapa x dim_serie, rollup encolhido) e tempo (dim_tempo x dim_data, via data de início e de fim da matrícula). Junho é usado porque é publicado em todos os anos e cai no meio do ano letivo; em dezembro o ano já terminou e quase nenhuma matrícula está ativa. A fila é estoque e por isso entra pelo valor de um único mês. A fração fora usa a matrícula publicada na própria planilha (mesma fonte, mesma data); a matrícula ativa do microdado fica ao lado como comparação. As duas concordam em menos de 1% de 2015 a 2020; de 2022 em diante o microdado superestima as ativas porque vínculos encerrados foram publicados sem data de fim (ver verificação Q07).
-- fatos: fato_fila, fato_matricula
WITH referencia AS (
    SELECT ano, data_referencia, last_day(data_referencia) AS data_corte
    FROM dw.dim_tempo
    WHERE mes = 6 AND fila_publicada
),
fila AS (
    SELECT r.ano, d.distrito, e.codigo AS etapa, sum(f.qtd_demanda_total) AS fila,
           sum(f.qtd_matriculas) AS matriculas_planilha
    FROM dw.fato_fila f
    JOIN dw.dim_tempo t       ON t.chave_tempo = f.chave_tempo
    JOIN referencia r         ON r.data_referencia = t.data_referencia
    JOIN dw.dim_territorio d  ON d.chave_territorio = f.chave_territorio
    JOIN dw.dim_etapa e       ON e.chave_etapa = f.chave_etapa
    WHERE e.codigo IN ('CRECHE', 'PRE')
    GROUP BY ALL
),
matricula AS (
    SELECT a.ano, d.distrito, s.codigo_etapa AS etapa,
           sum(f.qtd_matricula) AS matriculas_no_ano,
           sum(f.qtd_matricula) FILTER (
               WHERE di.data <= r.data_corte AND (df.data IS NULL OR df.data > r.data_corte)
           )                    AS matriculas_ativas_em_junho
    FROM dw.fato_matricula f
    JOIN dw.dim_ano_letivo a  ON a.chave_ano_letivo = f.chave_ano_letivo
    JOIN dw.dim_territorio d  ON d.chave_territorio = f.chave_territorio
    JOIN dw.dim_serie s       ON s.chave_serie = f.chave_serie
    JOIN dw.dim_data di       ON di.chave_data = f.chave_data_inicio     -- papel: início
    JOIN dw.dim_data df       ON df.chave_data = f.chave_data_fim        -- papel: fim
    LEFT JOIN referencia r    ON r.ano = a.ano
    WHERE s.codigo_etapa IN ('CRECHE', 'PRE')
    GROUP BY ALL
)
SELECT
    coalesce(f.ano, m.ano)                 AS ano,
    coalesce(f.distrito, m.distrito)       AS distrito,
    coalesce(f.etapa, m.etapa)             AS etapa,
    f.fila,
    f.matriculas_planilha,
    m.matriculas_ativas_em_junho,
    m.matriculas_no_ano,
    round(f.fila / NULLIF(f.fila + f.matriculas_planilha, 0), 4)                    AS fracao_fora,
    round(m.matriculas_ativas_em_junho / NULLIF(f.matriculas_planilha, 0) - 1, 4)   AS divergencia_entre_bases
FROM fila f
FULL OUTER JOIN matricula m
  ON m.ano = f.ano AND m.distrito = f.distrito AND m.etapa = f.etapa
ORDER BY ano, fracao_fora DESC NULLS LAST, distrito, etapa;
