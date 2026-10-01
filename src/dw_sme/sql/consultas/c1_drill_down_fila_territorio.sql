-- codigo: C1
-- tipo: drill-down
-- titulo: Fila de creche descendo da DRE para o distrito
-- pergunta: No último mês publicado, quantas crianças esperavam vaga em creche em cada Diretoria Regional de Educação, e em quais distritos dessa DRE a fila se concentra?
-- justificativa: A DRE é a instância que administra a rede, mas é no distrito que a prefeitura decide onde abrir vaga. A consulta parte do total do município, desce para a DRE e depois para o distrito, seguindo a hierarquia distrito ⊑ DRE ⊑ município da dimensão Território. Essa hierarquia não existe na planilha de fila, que só traz o distrito: ela vem da integração com o microdado (DRE predominante de cada distrito).
-- fatos: fato_fila
WITH referencia AS (
    -- a fila é estoque: usa-se um único mês, nunca a soma de meses
    SELECT max(chave_tempo) AS chave_tempo FROM dw.dim_tempo WHERE fila_publicada
)
SELECT
    CASE
        WHEN GROUPING(d.dre) = 1 THEN 'MUNICIPIO'
        WHEN GROUPING(d.distrito) = 1 THEN 'DRE'
        ELSE 'DISTRITO'
    END                                   AS nivel,
    t.ano_mes                             AS mes_referencia,
    coalesce(d.dre, '(SEM DRE)')          AS dre,
    d.distrito,
    sum(f.qtd_demanda_total)              AS criancas_na_fila
FROM dw.fato_fila f
JOIN referencia r            ON r.chave_tempo = f.chave_tempo
JOIN dw.dim_tempo t          ON t.chave_tempo = f.chave_tempo
JOIN dw.dim_territorio d     ON d.chave_territorio = f.chave_territorio
JOIN dw.dim_etapa e          ON e.chave_etapa = f.chave_etapa
WHERE e.codigo = 'CRECHE'
GROUP BY t.ano_mes, ROLLUP (d.dre, d.distrito)
ORDER BY GROUPING(d.dre) DESC, sum(sum(f.qtd_demanda_total)) OVER (PARTITION BY d.dre) DESC,
         d.dre, GROUPING(d.distrito) DESC, criancas_na_fila DESC, d.distrito;
