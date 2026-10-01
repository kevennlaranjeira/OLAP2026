-- codigo: C3
-- tipo: slice and dice
-- titulo: Creche por rede e jornada, antes e depois da pandemia
-- pergunta: Na creche, quanto da oferta é feita pela rede conveniada e quanto pela rede direta, e em que jornada (integral ou parcial), em 2019 e no ano mais recente?
-- justificativa: Boa parte da creche paulistana é operada por organizações conveniadas, e a jornada importa porque vaga de período parcial não atende quem trabalha o dia inteiro. O slice fixa a etapa em creche; o dice restringe a rede a direta e conveniada e o tempo a dois anos (2019, último ano antes da pandemia, e o mais recente), cruzando rede por jornada.
-- fatos: fato_matricula
SELECT
    a.ano,
    e.rede,
    t.jornada,
    sum(f.qtd_matricula)                                                    AS matriculas,
    round(sum(f.qtd_matricula) / sum(sum(f.qtd_matricula)) OVER (PARTITION BY a.ano), 4) AS participacao_no_ano
FROM dw.fato_matricula f
JOIN dw.dim_ano_letivo a ON a.chave_ano_letivo = f.chave_ano_letivo
JOIN dw.dim_serie s      ON s.chave_serie = f.chave_serie
JOIN dw.dim_escola e     ON e.chave_escola = f.chave_escola
JOIN dw.dim_turno t      ON t.chave_turno = f.chave_turno
WHERE s.codigo_etapa = 'CRECHE'                                              -- slice
  AND e.rede IN ('DIRETA', 'CONVENIADA')                                     -- dice
  AND a.ano IN (2019, (SELECT max(ano) FROM dw.dim_ano_letivo))              -- dice
GROUP BY a.ano, e.rede, t.jornada
ORDER BY a.ano, e.rede, matriculas DESC;
