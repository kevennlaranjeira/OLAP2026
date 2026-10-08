# Auditoria do trabalho

Revisão de ponta a ponta de tudo o que está no repositório: código, processo, documentação, relatório, apresentação e imagens. A verificação específica do modelo dimensional está em [09 Verificação da modelagem](09-verificacao-da-modelagem.md).

## O que foi conferido e como

| Frente | Como | Resultado |
|---|---|---|
| Testes e lint | `pytest` (440 testes) e `ruff` | todos passam; cobertura de 95% |
| Checagem de tipos | `pyright` comparado com a `main` | o código novo não acrescenta erro de tipo real; os avisos restantes vêm dos stubs do pandas e do DuckDB, como antes (ver [07](07-como-executar.md)) |
| Processo pela linha de comando | `dw-sme carregar`, `verificar` e `consultar` sobre os dados de teste | as 3 etapas terminam com código 0; 14 verificações sem FALHA; 8 consultas gravadas |
| Saídas das consultas | leitura dos 8 CSV e do relatório de qualidade | 3 defeitos de apresentação, corrigidos (abaixo) |
| Coerência entre documentos | [tests/test_coerencia.py](../tests/test_coerencia.py), 40 testes, a cada push | contagens, consultas, integrantes, links, textos pendentes e hierarquias citadas iguais em README, docs/, relatório e slides |
| Modelo dimensional | [tests/test_modelo.py](../tests/test_modelo.py), 22 testes, e Q13/Q14 | ver [09](09-verificacao-da-modelagem.md) |
| Imagens dos esquemas | PNG gerado de novo a partir dos arquivos TikZ e comparado pixel a pixel | os 6 idênticos aos de [modelagem/](modelagem/) |
| Imagens nos slides | hash das imagens dentro do `.pptx` | iguais às de [modelagem/](modelagem/), conferido a cada push |
| PDFs | relatório e PDF de modelagem recompilados e comparados pelo texto | idênticos aos do repositório; nenhuma caixa vazando a margem |
| Revisão visual | 17 slides, 25 páginas do relatório e 7 do PDF de modelagem renderizados | sem texto cortado ou sobreposto; um título longo encurtado |

## Erros encontrados e corrigidos

| # | Onde | Problema | Correção |
|---|---|---|---|
| 1 | consultas C1 e C8 | a linha do total do município saía com a DRE "(SEM DRE)", como se faltasse o dado | a linha do total mostra "(TODAS)"; "(SEM DRE)" fica só para distrito sem DRE |
| 2 | relatório de qualidade | anos apareciam com ponto de milhar ("2.019") | a coluna `ano` sai sem separador ("2019") |
| 3 | CSV das consultas | contagens com nulo saíam como "55.0" | contagens gravadas como inteiro |
| 4 | carga do Censo 2022 | um arquivo do IBGE fora do layout parava a carga inteira, inclusive os fatos da SME, contrariando a decisão D23 | só a população é recusada; o motivo fica no resumo da carga e Q12 fica em ALERTA |
| 5 | leitura do Censo 2022 | um setor repetido no arquivo virava um erro de chave primária difícil de entender | a leitura para com a mensagem "setor censitário repetido" |
| 6 | download do IBGE | uma subpasta inacessível na listagem interrompia a busca inteira | a subpasta é pulada; só a falha na pasta principal interrompe |
| 7 | notas do slide 12 | "setor ≤ distrito", sem o nome completo do nível | "setor censitário ≤ distrito" |
| 8 | comentários do DDL | Tempo e Ano Letivo não citavam todos os fatos que as usam | comentários atualizados (População; Ocupação de Turma) |
| 9 | slide 7 | título em duas linhas, encostando na tabela | título encurtado |
| 10 | pasta `.qa/` vazia | sobra de uma conversão antiga | removida |

Cada correção de código tem teste novo: C1 e C8 com "(TODAS)", formatação do ano, CSV com inteiros, arquivo do IBGE fora do layout, setor repetido e subpasta inacessível.

## O que continua dependendo do grupo

Está em [08 Pendências da entrega](08-pendencias-da-entrega.md):

- curso e data de entrega na capa;
- conferir a notação dos esquemas com a das aulas;
- rodar `dw-sme tudo` num computador com internet, para ter os números reais da população, das consultas 7 e 8 e das verificações Q11 a Q14;
- ensaiar a apresentação.

Uma observação sobre o último relatório de qualidade com os dados reais, [relatorios/qualidade.md](relatorios/qualidade.md): ele foi gerado antes destas correções. Por isso ainda mostra os anos com ponto ("2.015") e só dez verificações. Ele não foi editado à mão. A próxima carga gera a versão nova.
