-- codigo: C8
-- tipo: drill-down
-- titulo: Ocupação das turmas descendo do município para a DRE e o distrito
-- pergunta: Em 2019 e no ano mais recente, quantos alunos em média havia por turma em funcionamento em 30 de junho, em cada etapa da educação infantil e do ensino fundamental, no município, em cada DRE e em cada distrito?
-- justificativa: A fila diz onde falta vaga; a ocupação das turmas diz se a vaga que existe está cheia. Turmas mais cheias que a média da etapa indicam onde abrir vaga exige turma nova, e não só aproveitar lugar ocioso. As fontes não publicam a capacidade de cada turma, então a consulta mede a ocupação efetiva: alunos ativos em 30/06 por turma com ao menos um aluno ativo. A média é um fato derivado não aditivo, recalculada em cada nível como soma de alunos dividida pela soma de turmas, nunca como média de médias. A consulta parte do município e desce pela hierarquia distrito ≤ DRE ≤ município da dimensão Território, com slice em quatro etapas e dice em dois anos (2019, último antes da pandemia, e o mais recente).
-- fatos: fato_turma
WITH anos AS (
    SELECT ano FROM dw.dim_ano_letivo
    WHERE ano IN (2019, (SELECT max(ano) FROM dw.dim_ano_letivo))
)
SELECT
    a.ano,
    s.etapa,
    CASE
        WHEN GROUPING(d.dre) = 1 THEN 'MUNICIPIO'
        WHEN GROUPING(d.distrito) = 1 THEN 'DRE'
        ELSE 'DISTRITO'
    END                                                                            AS nivel,
    CASE WHEN GROUPING(d.dre) = 1 THEN '(TODAS)' ELSE coalesce(d.dre, '(SEM DRE)') END AS dre,
    d.distrito,
    sum(t.qtd_turmas_ativas_junho)                                                 AS turmas_ativas_junho,
    sum(t.qtd_matriculas_ativas_junho)                                             AS alunos_ativos_junho,
    round(sum(t.qtd_matriculas_ativas_junho) / NULLIF(sum(t.qtd_turmas_ativas_junho), 0), 1)
                                                                                   AS alunos_por_turma
FROM dw.fato_turma t
JOIN dw.dim_ano_letivo a  ON a.chave_ano_letivo = t.chave_ano_letivo
JOIN anos                 USING (ano)
JOIN dw.dim_serie s       ON s.chave_serie = t.chave_serie
JOIN dw.dim_territorio d  ON d.chave_territorio = t.chave_territorio
WHERE s.codigo_etapa IN ('CRECHE', 'PRE', 'FUND_I', 'FUND_II')                    -- slice nas etapas
  AND t.qtd_turmas_ativas_junho IS NOT NULL                                        -- só anos com datas publicadas
GROUP BY a.ano, s.etapa, ROLLUP (d.dre, d.distrito)
ORDER BY a.ano, s.etapa, GROUPING(d.dre) DESC, d.dre, GROUPING(d.distrito) DESC, alunos_por_turma DESC, d.distrito;
