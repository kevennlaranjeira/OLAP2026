-- codigo: C2
-- tipo: roll-up
-- titulo: Matrículas subindo da etapa para o nível de ensino, ano a ano
-- pergunta: Como evoluiu o número de matrículas da rede municipal entre 2015 e 2024, por etapa e, agregando, por nível de ensino?
-- justificativa: A série mostra em quais etapas a rede cresceu e em quais encolheu, para comparar com a evolução da fila em cada etapa. Subir de etapa para nível e para o total do ano usa a hierarquia série ≤ etapa ≤ nível da dimensão Série. A medida é aditiva: a soma dos vínculos aluno-turma é válida em qualquer nível.
-- fatos: fato_matricula
SELECT
    a.ano,
    CASE
        WHEN GROUPING(s.nivel) = 1 THEN 'TOTAL DO ANO'
        WHEN GROUPING(s.etapa) = 1 THEN 'NIVEL'
        ELSE 'ETAPA'
    END                       AS agregacao,
    s.nivel,
    s.etapa,
    sum(f.qtd_matricula)      AS matriculas
FROM dw.fato_matricula f
JOIN dw.dim_ano_letivo a ON a.chave_ano_letivo = f.chave_ano_letivo
JOIN dw.dim_serie s      ON s.chave_serie = f.chave_serie
GROUP BY a.ano, ROLLUP (s.nivel, s.etapa)
ORDER BY a.ano, GROUPING(s.nivel), s.nivel, GROUPING(s.etapa), matriculas DESC;
