-- codigo: C7
-- tipo: drill-across
-- titulo: Crianças de 0 a 4 anos residentes, matriculadas e na fila, por distrito, na data do Censo 2022
-- pergunta: Em cada distrito, quantas crianças de 0 a 4 anos o Censo 2022 contou, quantas crianças dessa idade estavam matriculadas em escolas municipais do distrito na data de referência do Censo, e quantas esperavam vaga em creche ou pré-escola no último mês publicado antes dela?
-- justificativa: A fila mede quem pediu vaga; a população mede quantas crianças existem. Pôr as duas ao lado da matrícula mostra onde a oferta municipal é pequena diante do número de crianças residentes, mesmo quando a fila já é baixa, e ajuda a priorizar onde abrir vagas. A consulta cruza três tabelas de fatos com grãos diferentes, cada uma agregada até distrito: população (setor censitário x faixa etária, subindo de setor para distrito), matrícula (vínculo aluno-turma, contando as ativas em 31/07/2022 pelos dois papéis da dimensão Data) e fila (distrito x mês x etapa). As dimensões conformadas são Território (distrito), Tempo (mês do Censo; ano letivo) e Idade (faixa IBGE de dim_faixa_etaria, rollup encolhido de dim_idade). A matrícula é contada pelo distrito da escola e a população pelo distrito de residência; a razão entre elas é oferta por criança residente, não taxa de atendimento dos moradores. O corte do IBGE é quinquenal, por isso a faixa comparável é 0 a 4 anos, que cobre a creche e parte da pré-escola.
-- fatos: fato_populacao, fato_matricula, fato_fila
WITH censo AS (
    -- mês de referência do Censo, lido do próprio fato de população
    SELECT DISTINCT t.chave_tempo, t.ano, t.data_referencia, last_day(t.data_referencia) AS data_corte
    FROM dw.fato_populacao p JOIN dw.dim_tempo t USING (chave_tempo)
),
populacao AS (
    SELECT d.distrito, d.dre, sum(p.qtd_pessoas) AS criancas_0_4_residentes,
           count(*) FILTER (WHERE p.qtd_pessoas IS NULL) AS setores_sem_valor_publicado
    FROM dw.fato_populacao p
    JOIN censo c                  ON c.chave_tempo = p.chave_tempo
    JOIN dw.dim_territorio d      ON d.chave_territorio = p.chave_territorio
    JOIN dw.dim_faixa_etaria fe   ON fe.chave_faixa_etaria = p.chave_faixa_etaria
    WHERE fe.faixa_ibge = '0 A 4 ANOS'
    GROUP BY ALL
),
matricula AS (
    SELECT d.distrito, sum(f.qtd_matricula) AS matriculas_0_4_ativas
    FROM dw.fato_matricula f
    JOIN dw.dim_ano_letivo a  ON a.chave_ano_letivo = f.chave_ano_letivo
    JOIN censo c              ON c.ano = a.ano
    JOIN dw.dim_territorio d  ON d.chave_territorio = f.chave_territorio
    JOIN dw.dim_idade i       ON i.chave_idade = f.chave_idade
    JOIN dw.dim_data di       ON di.chave_data = f.chave_data_inicio     -- papel: início
    JOIN dw.dim_data df       ON df.chave_data = f.chave_data_fim        -- papel: fim
    WHERE i.faixa_ibge = '0 A 4 ANOS'                                    -- conformidade com dim_faixa_etaria
      AND di.data <= c.data_corte AND (df.data IS NULL OR df.data > c.data_corte)
    GROUP BY ALL
),
mes_fila AS (
    -- a fila é estoque: um único mês, o último publicado até a data do Censo
    SELECT max(t.chave_tempo) AS chave_tempo
    FROM dw.dim_tempo t JOIN censo c ON t.data_referencia <= c.data_referencia
    WHERE t.fila_publicada
),
fila AS (
    SELECT d.distrito, t.ano_mes AS mes_fila, sum(f.qtd_demanda_total) AS fila_creche_pre
    FROM dw.fato_fila f
    JOIN mes_fila m           ON m.chave_tempo = f.chave_tempo
    JOIN dw.dim_tempo t       ON t.chave_tempo = f.chave_tempo
    JOIN dw.dim_territorio d  ON d.chave_territorio = f.chave_territorio
    JOIN dw.dim_etapa e       ON e.chave_etapa = f.chave_etapa
    WHERE e.codigo IN ('CRECHE', 'PRE')
    GROUP BY ALL
)
SELECT
    coalesce(p.distrito, m.distrito, f.distrito)                                   AS distrito,
    p.dre,
    p.criancas_0_4_residentes,
    m.matriculas_0_4_ativas,
    f.mes_fila,
    f.fila_creche_pre,
    round(100.0 * m.matriculas_0_4_ativas / NULLIF(p.criancas_0_4_residentes, 0), 1) AS matriculas_por_100_criancas,
    round(1000.0 * f.fila_creche_pre / NULLIF(p.criancas_0_4_residentes, 0), 1)      AS fila_por_mil_criancas,
    p.setores_sem_valor_publicado
FROM populacao p
FULL OUTER JOIN matricula m ON m.distrito = p.distrito
FULL OUTER JOIN fila f      ON f.distrito = coalesce(p.distrito, m.distrito)
WHERE coalesce(p.distrito, m.distrito, f.distrito) <> 'NAO INFORMADO'
ORDER BY matriculas_por_100_criancas NULLS LAST, distrito;
