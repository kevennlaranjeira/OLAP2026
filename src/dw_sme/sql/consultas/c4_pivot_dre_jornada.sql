-- codigo: C4
-- tipo: pivot
-- titulo: Matrículas por DRE com a jornada girada para as colunas
-- pergunta: No ano mais recente, como as matrículas de cada DRE se dividem entre jornada integral, parcial diurna e noturna?
-- justificativa: Com DRE nas linhas e jornada nas colunas, a tabela mostra de relance quais regiões dependem de turno parcial e quais concentram jornada integral, que é a que atende famílias em que os responsáveis trabalham o dia inteiro. O pivot gira o eixo jornada, que no resultado de um GROUP BY comum ficaria repetido nas linhas.
-- fatos: fato_matricula
PIVOT (
    SELECT coalesce(e.dre, '(SEM DRE)') AS dre, t.jornada, f.qtd_matricula
    FROM dw.fato_matricula f
    JOIN dw.dim_ano_letivo a ON a.chave_ano_letivo = f.chave_ano_letivo
    JOIN dw.dim_escola e     ON e.chave_escola = f.chave_escola
    JOIN dw.dim_turno t      ON t.chave_turno = f.chave_turno
    WHERE a.ano = (SELECT max(ano) FROM dw.dim_ano_letivo)
)
ON jornada
USING sum(qtd_matricula)
GROUP BY dre
ORDER BY dre;
