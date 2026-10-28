# Auditoria do trabalho

Nossas anotações da revisão de ponta a ponta do repositório: código, processo, documentação, relatório, apresentação e imagens. A verificação específica do modelo dimensional está em [09 Verificação da modelagem](09-verificacao-da-modelagem.md).

## O que é conferido e como

| Frente | Como | Resultado |
|---|---|---|
| Testes e lint | `pytest` (505 testes) e `ruff`, a cada push no GitHub, com Python 3.11 e 3.13 | todos passam; cobertura de 99% |
| Coerência entre documentos | [tests/test_coerencia.py](../tests/test_coerencia.py), 54 testes | contagens, consultas, integrantes, links, textos pendentes, hierarquias e números iguais em README, docs/, relatório e nas duas versões da apresentação (`.pptx` e HTML); o PDF com uma página por slide; o tempo combinado de cada bloco |
| Modelo dimensional | [tests/test_modelo.py](../tests/test_modelo.py), 22 testes, e as verificações Q13 e Q14 | ver [09](09-verificacao-da-modelagem.md) |
| Funcionamento | [tests/test_funcionamento.py](../tests/test_funcionamento.py), 14 testes | recarga sem duplicar; `verificar` e `tudo` saem com 1 em FALHA; 72.900 matrículas sintéticas conservam as contagens entre os fatos; consultas iguais quando repetidas e quando o dado entra em outra ordem; caminho com apóstrofo; carga que falha no meio preserva o banco anterior |
| Checagem de tipos | `pyright` | nenhum erro de tipo real; os avisos restantes vêm dos stubs do pandas e do DuckDB (ver [07](07-como-executar.md)) |
| Replicação completa | clone do GitHub, ambiente virtual novo, `pip install ".[dev]"`, testes e `dw-sme tudo` numa pasta vazia, baixando tudo de novo | DuckDB 1.5.6 instalado pela restrição `<2`; 647 MB baixados; pipeline completo em 566 s, sem FALHA, com as 8 consultas gravadas |
| Dados reais | `dw-sme` etapa por etapa sobre a pasta de dados real, com o Censo 2022 baixado do IBGE | 13.412.178 matrículas, 551.264 turmas, 295.779 linhas de população, 33.792 de fila e 159.369 de desfecho; Q12 em ALERTA pelos 6.543 valores que o IBGE suprime; nenhuma FALHA |
| População contra o total do IBGE | soma das faixas etárias contra a variável `v0001` do tema Básico | 11.434.513 contra 11.451.999 moradores (0,15% abaixo, pela supressão); os 26.889 setores ligados a um dos 96 distritos |
| Dados das bugigangas | indicadores de deficiência por ano no microdado | os quatro que só existem em 2024 ficam "não coletado" antes disso; 169 linhas de 2016 sem nenhum indicador e um valor "2" isolado em 2018 e 2023 ficam "não informado" |
| Saídas das consultas | leitura dos 8 CSV e do relatório de qualidade | totais com "(TODAS)", anos sem separador de milhar, contagens como inteiro |
| Imagens dos esquemas | `figuras.tex` compilado de novo e cada página comparada com o PNG do repositório; hash das imagens dentro do `.pptx` e do HTML | os 6 PNG idênticos pixel a pixel; as duas apresentações usam os PNG atuais, conferido a cada push |
| PDFs | relatório e PDF de modelagem compilados com XeLaTeX; o fluxo `relatorio.yml` do GitHub compila o relatório a cada mudança em `docs/relatorio/` e deixa o PDF para baixar | compilam sem erro; nenhuma caixa vazando a margem |
| Revisão visual | 28 slides em cada versão da apresentação, 27 páginas do relatório e 7 do PDF de modelagem renderizados | sem texto cortado ou sobreposto |

## Erros encontrados e corrigidos

| # | Onde | Problema | Correção |
|---|---|---|---|
| 1 | consultas C1 e C8 | a linha do total do município saía com a DRE "(SEM DRE)", como se faltasse o dado | a linha do total mostra "(TODAS)"; "(SEM DRE)" fica só para distrito sem DRE |
| 2 | relatório de qualidade | anos apareciam com ponto de milhar ("2.019") | a coluna `ano` sai sem separador ("2019") |
| 3 | CSV das consultas | contagens com nulo saíam como "55.0" | contagens gravadas como inteiro |
| 4 | carga do Censo 2022 | um arquivo do IBGE fora do layout parava a carga inteira, inclusive os fatos da SME, contrariando a decisão D23 | só a população é recusada; o motivo fica no resumo da carga e Q12 fica em ALERTA |
| 5 | leitura do Censo 2022 | um setor repetido no arquivo virava um erro de chave primária difícil de entender | a leitura para com a mensagem "setor censitário repetido" |
| 6 | download do IBGE | uma subpasta inacessível na listagem interrompia a busca inteira | a subpasta é pulada; só a falha na pasta principal interrompe |
| 7 | notas do slide das estrelas | "setor ≤ distrito", sem o nome completo do nível | "setor censitário ≤ distrito" |
| 8 | comentários do DDL | Tempo e Ano Letivo não citavam todos os fatos que as usam | comentários atualizados (População; Ocupação de Turma) |
| 9 | slide das fontes | título em duas linhas, encostando na tabela | título encurtado |
| 10 | pasta `.qa/` vazia | sobra de uma conversão antiga | removida |
| 11 | consultas C2, C3 e C6 | o ORDER BY parava numa coluna que podia empatar; a C2 mudava a ordem das linhas ao ser repetida no mesmo banco | critério de desempate em cada uma; o teste de determinismo pega a regressão |
| 12 | slide dos assuntos de interesse | o enunciado pede a motivação dos assuntos, e o slide só dizia onde cada um estava no modelo | "Por que importa" para os cinco assuntos e o desfecho como quinto processo à parte; a mesma coluna entrou no relatório |
| 13 | slides de estrelas | duas estrelas por slide deixavam o texto do desenho com cerca de 13 pixels numa tela de 1080 linhas | uma estrela por slide, na largura do slide |
| 14 | tempo dos integrantes | as notas diziam quem apresenta, mas não o tempo; o bloco 3 tinha mais conteúdo que os outros | tempo previsto em cada nota, quatro blocos de 5 minutos, slide de roteiro montado a partir das notas e teste que confere a igualdade |
| 15 | slides e documentos | diziam que C7, C8 e a população seriam medidas "na próxima carga" | números reais em docs/05, docs/01, docs/09, README, relatório e slides |
| 16 | gráfico da fila nos slides | pulava 2016, 2018 e 2023 | série completa de 2015 a 2024, tirada da C5 |
| 17 | imagens nos slides | o texto alternativo era o caminho do arquivo na máquina onde os slides foram gerados | descrição de cada esquema |
| 18 | carga | recarregar no mesmo arquivo deixava nele o espaço das tabelas apagadas (636 MB contra 334 MB feito do zero), e uma carga que falhasse no meio deixava o banco anterior pela metade | a carga monta um arquivo novo e só no fim troca o anterior; dois testes cobrem o tamanho em recargas e a falha no meio |
| 19 | carga e preparação | caminho com apóstrofo (`dados d'água`, sobrenome D'Ávila) quebrava a SQL | `texto_sql.literal()` em todo caminho que entra na SQL; dois testes |
| 20 | relatório, seção 1.1 | duas afirmações sem fonte: a falta de vaga como "principal problema" e a intenção da prefeitura ao publicar a fila | a primeira ancorada no número da Consulta 5; a segunda reescrita sem supor intenção |
| 21 | relatório, docs/01, docs/02 e slide das fontes | "44 planilhas" de fila; são 44 meses de referência em 33 arquivos, porque a série histórica traz 2015 a 2017 num arquivo só | texto corrigido nos quatro lugares |
| 22 | relatório | citava o artigo da disciplina, a Lei do PNE e o INEP sem seção de referências, e não dava o endereço das fontes | seção Referências com 6 entradas e datas de acesso; os endereços foram conferidos |
| 23 | relatório, apêndice | o resultado negativo da Consulta 6 e as limitações das fontes não estavam no relatório | um parágrafo para cada |
| 24 | carga, dias de matrícula | a SME publica dias negativos em 6.093 vínculos com o fim antes do início, e a medida aditiva entrava negativa na soma | duração impossível fica nula; teste novo; banco recarregado, com as 8 consultas idênticas às anteriores |

Cada correção de código tem um teste que pega a regressão.

## O que ainda falta para nós

Está em [08 Pendências da entrega](08-pendencias-da-entrega.md): conferir a notação dos esquemas com a das aulas e ensaiar a apresentação. A capa do relatório está completa, com os nossos cursos e a data de entrega, 29 de outubro de 2026.

O relatório de qualidade publicado em [relatorios/qualidade.md](relatorios/qualidade.md) é o da carga com os dados reais, com as catorze verificações.
