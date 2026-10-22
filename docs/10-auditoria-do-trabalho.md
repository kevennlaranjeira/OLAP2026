# Auditoria do trabalho

Revisão de ponta a ponta de tudo o que está no repositório: código, processo, documentação, relatório, apresentação e imagens. A verificação específica do modelo dimensional está em [09 Verificação da modelagem](09-verificacao-da-modelagem.md).

## O que foi conferido e como

| Frente | Como | Resultado |
|---|---|---|
| Testes e lint | `pytest` (482 testes) e `ruff` | todos passam; cobertura de 99%, sem linha de código sem teste |
| Checagem de tipos | `pyright` comparado com a `main` | o código novo não acrescenta erro de tipo real; os avisos restantes vêm dos stubs do pandas e do DuckDB, como antes (ver [07](07-como-executar.md)) |
| Processo pela linha de comando | `dw-sme baixar`, `preparar`, `carregar`, `verificar` e `consultar` sobre os dados reais, a partir de um clone limpo | as 5 etapas terminam com código 0; 14 verificações sem FALHA; 8 consultas gravadas (ver abaixo) |
| Saídas das consultas | leitura dos 8 CSV e do relatório de qualidade | 3 defeitos de apresentação, corrigidos (abaixo) |
| Coerência entre documentos | [tests/test_coerencia.py](../tests/test_coerencia.py), 41 testes, a cada push | contagens, consultas, integrantes, links, textos pendentes e hierarquias citadas iguais em README, docs/, relatório e slides; os quatro blocos da apresentação com o mesmo tempo |
| Modelo dimensional | [tests/test_modelo.py](../tests/test_modelo.py), 22 testes, e Q13/Q14 | ver [09](09-verificacao-da-modelagem.md) |
| Imagens dos esquemas | PNG gerado de novo a partir dos arquivos TikZ e comparado pixel a pixel | os 6 idênticos aos de [modelagem/](modelagem/) |
| Imagens nos slides | hash das imagens dentro do `.pptx` | iguais às de [modelagem/](modelagem/), conferido a cada push |
| PDFs | relatório e PDF de modelagem recompilados e comparados pelo texto | idênticos aos do repositório; nenhuma caixa vazando a margem |
| Revisão visual | 21 slides, 25 páginas do relatório e 7 do PDF de modelagem renderizados | sem texto cortado ou sobreposto |

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

## Segunda rodada: instalação do zero, dados reais e entrega da etapa 1

| Frente | Como | Resultado |
|---|---|---|
| Instalação do zero | clone limpo da branch, ambiente virtual novo, `pip install ".[dev]"` sem modo editável, antes e depois das correções desta rodada | o pacote leva as 8 consultas SQL; no estado final, 482 testes e o ruff passam no clone, e `carregar`, `verificar` e `consultar` terminam com código 0 sobre os dados reais (carga em 202 s) |
| Processo com os dados reais | o `dw-sme` do ambiente limpo, etapa por etapa, sobre a pasta de dados real, com o Censo 2022 baixado do servidor do IBGE | 5 etapas com código 0; carga em 211 s; 13.412.178 matrículas, 551.264 turmas, 295.779 linhas de população, 33.792 de fila e 159.369 de desfecho |
| Verificações nos dados reais | `dw-sme verificar` | Q11, Q13 e Q14 OK; Q12 em ALERTA pelos 6.543 valores que o IBGE suprime; nenhuma FALHA |
| População contra o total do IBGE | soma das faixas etárias contra a variável `v0001` do tema Básico | 11.434.513 contra 11.451.999 moradores (0,15% abaixo, pela supressão); os 26.889 setores ligados a um dos 96 distritos |
| Testes de funcionamento | [tests/test_funcionamento.py](../tests/test_funcionamento.py) | recarga sem duplicar; `verificar` e `tudo` saem com 1 em FALHA; 72.900 matrículas sintéticas conservam as contagens entre os fatos; consultas iguais quando repetidas e quando o dado entra em outra ordem |
| Lacunas de cobertura | um teste por comportamento não exercitado | cobertura de 96% para 99% |
| Apresentação contra as instruções de entrega | leitura do enunciado item a item, slides renderizados | ver abaixo |

### Erros encontrados e corrigidos nesta rodada

| # | Onde | Problema | Correção |
|---|---|---|---|
| 11 | consultas C2, C3 e C6 | o ORDER BY parava numa coluna que podia empatar; a C2 mudava a ordem das linhas até ao ser repetida no mesmo banco | critério de desempate em cada uma; o teste de determinismo pega a regressão |
| 12 | slide dos assuntos de interesse | o enunciado pede a motivação dos assuntos, e o slide só dizia onde cada um estava no modelo; o título falava em cinco e a tabela tinha seis linhas | tabela com "Por que importa" para os cinco assuntos e o desfecho como quinto processo à parte; a mesma coluna entrou no relatório |
| 13 | slides de estrelas | duas estrelas por slide deixavam o texto do desenho com cerca de 13 pixels numa tela de 1080 linhas | uma estrela por slide, na largura do slide |
| 14 | tempo dos integrantes | as notas diziam quem apresenta, mas não o tempo; o bloco 3 tinha mais conteúdo que os outros | tempo previsto em cada nota, quatro blocos de 5 minutos, slide de roteiro montado a partir das notas e teste que confere a igualdade |
| 15 | slides 6, 12, 15 e 17 e documentos | diziam que C7, C8 e a população seriam medidas "na próxima carga" | números reais em docs/05, docs/01, docs/09, README, relatório e slides |
| 16 | gráfico da fila nos slides | pulava 2016, 2018 e 2023 | série completa de 2015 a 2024, tirada da C5 |
| 17 | imagens nos slides | o texto alternativo era o caminho do arquivo na máquina onde os slides foram gerados | descrição de cada esquema |

## Terceira rodada: replicação a partir do GitHub, esquemas e relatório

| Frente | Como | Resultado |
|---|---|---|
| Replicação completa | clone do GitHub (`main`), ambiente virtual novo, `pip install ".[dev]"`, testes e `dw-sme tudo` numa pasta vazia, baixando tudo de novo | DuckDB 1.5.6 instalado pela restrição `<2`; testes e ruff passam; 647 MB baixados e pipeline completo em 566 s, sem FALHA, com as 8 consultas gravadas |
| Imagens dos esquemas | `figuras.tex` compilado de novo e cada página comparada com o PNG do repositório | os 6 idênticos pixel a pixel |
| Modelo no banco | leitura do DDL contra os conceitos da disciplina; Q13 e Q14 nos dados reais | grão declarado em cada fato, chave artificial em todas as dimensões, hierarquias válidas nos dados |
| Dados das bugigangas | indicadores de deficiência por ano no microdado | os quatro que só existem em 2024 ficam "não coletado" antes disso; 169 linhas de 2016 sem nenhum indicador e um valor "2" isolado em 2018 e 2023 ficam "não informado", como devem |
| Revisão de código | casos de borda, recursos abertos, exceções, `pyright` | 1 defeito (abaixo); nenhum erro de tipo real |
| Relatório | revisão de cada afirmação contra os dados e as fontes, estrutura contra o enunciado | 4 problemas de texto (abaixo) |

### Erros encontrados e corrigidos nesta rodada

| # | Onde | Problema | Correção |
|---|---|---|---|
| 18 | carga | recarregar no mesmo arquivo deixava nele o espaço das tabelas apagadas (o banco real tinha 636 MB, dos quais 1.118 blocos livres; feito do zero, tem 334 MB), e uma carga que falhasse no meio deixava o banco anterior pela metade | a carga monta um arquivo novo e só no fim troca o anterior; dois testes cobrem o tamanho em recargas e a falha no meio |
| 19 | carga e preparação | caminho com apóstrofo (`dados d'água`, sobrenome D'Ávila) quebrava a SQL | `texto_sql.literal()` em todo caminho que entra na SQL; dois testes |
| 20 | relatório, seção 1.1 | duas afirmações sem fonte: a falta de vaga como "principal problema" e a intenção da prefeitura ao publicar a fila | a primeira ancorada no número da Consulta 5; a segunda reescrita sem supor intenção |
| 21 | relatório, docs/01, docs/02, slide 7 | "44 planilhas" de fila; são 44 meses de referência em 33 arquivos, porque a série histórica traz 2015 a 2017 num arquivo só | texto corrigido nos quatro lugares |
| 22 | relatório | citava o artigo da disciplina, a Lei do PNE e o INEP sem seção de referências, e não dava o endereço das fontes | seção Referências com 6 entradas e datas de acesso; os endereços foram conferidos |
| 23 | relatório, apêndice | o resultado negativo da Consulta 6 e as limitações das fontes não estavam no relatório | um parágrafo para cada |

O CI ganhou um segundo fluxo, `relatorio.yml`, que compila o relatório com XeLaTeX sempre que algo em `docs/relatorio/` muda e deixa o PDF para baixar. Quem edita o `.tex` pelo navegador passa a saber se ele compila.

## O que continua dependendo do grupo

Está em [08 Pendências da entrega](08-pendencias-da-entrega.md):

- curso e data de entrega na capa;
- conferir a notação dos esquemas com a das aulas;
- ensaiar a apresentação.

O relatório de qualidade publicado em [relatorios/qualidade.md](relatorios/qualidade.md) é o da carga com os dados reais desta rodada, com as catorze verificações.
