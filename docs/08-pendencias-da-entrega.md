# Pendências da entrega do Projeto 1

Nossa lista do que já está pronto e do que ainda falta antes de entregar. O enunciado pede dois materiais: o documento em PDF e a apresentação.

## Situação dos itens do enunciado

| Item do enunciado | Onde está | Situação |
|---|---|---|
| Tema geral | relatório, seção 1.1 | pronto |
| Pelo menos 3 assuntos de interesse | relatório, seção 1.2 (os cinco da nossa planilha, com a motivação de cada um) | pronto |
| Pelo menos 2 esquemas estrela | relatório, seções 2.1 a 2.5 (cinco estrelas) | pronto |
| Pelo menos 1 constelação de fatos, com desenho e processo de projeto | relatório, seção 2.6, e matriz de barramento | pronto |
| Pelo menos 2 fontes de dados | relatório, seção 1.3 (três fontes: duas da SME e o Censo 2022 do IBGE) | pronto |
| Pelo menos 5 consultas: 2 roll-up ou drill-down, 1 slice and dice, 1 pivot, 1 drill-across | relatório, seção 3 (oito consultas: 3, 1, 1 e 3) | pronto |
| Capa com instituição, curso, disciplina, professora, trabalho, integrantes com Nº USP e data | relatório, capa | pronto (cursos: Ciência de Dados, Ciência da Computação e Mestrado em Ciência da Computação; data de entrega 29 de outubro de 2026) |
| Índice | relatório | pronto |
| Grão, dimensões, fatos, atributos e relações, aditividade, fatos derivados | relatório, seções 1.4 a 1.6 | pronto |
| Povoamento de cada atributo e de cada fato, com integração | relatório, seções 1.5 a 1.7 (coluna "Povoamento" em cada dimensão) | pronto |
| Hierarquias com o operador de ordenação parcial e função de agregação de cada fato | relatório, seção 2 | pronto |
| Chave artificial, bugiganga, dimensão degenerada, campo artificial de fatos sem fato | relatório, seções 2.6 e 1.5 | pronto |
| Apresentação com motivação do tema e dos assuntos, fontes, estrelas, constelação, consultas e decisões; todos apresentam, com tempo homogêneo | [apresentacao/apresentacao-projeto1.pptx](apresentacao/apresentacao-projeto1.pptx), 24 slides em quatro blocos de 5 minutos; a mesma apresentação em [HTML](apresentacao/apresentacao-projeto1.html), para o navegador, e em [PDF](apresentacao/apresentacao-projeto1.pdf), para ver no GitHub | pronta; falta ensaiar |

Os números do relatório, da documentação e dos slides vêm da carga com os dados reais: SME de 2015 a 2024 e Censo 2022, com as oito consultas medidas.

## O que ainda falta a gente fazer

1. **Conferir a notação dos esquemas com a das aulas.** A verificação completa da modelagem está em [09 Verificação da modelagem](09-verificacao-da-modelagem.md). Os desenhos seguem a notação do artigo da disciplina (caixa com o nome da tabela, PK e FK, fato no centro com borda grossa) e as hierarquias usam `≤`. O enunciado diz que a notação tem de ser a mesma da sala de aula. Se a das aulas for diferente, os desenhos estão em `docs/relatorio/esquemas/*.tex` e o estilo comum em `estilo.tex`.

2. **Ensaiar a apresentação.** As apresentações serão no dia 29 de outubro, e a de cada grupo deve durar 20 minutos. O slide 9 fecha o bloco 1 com o roteiro, e as notas de cada slide dizem quem apresenta, o tempo previsto e o que falar:

   | Bloco | Integrante | Slides | Conteúdo | Tempo |
   |---|---|---|---|---|
   | 1 | Kevenn Laranjeira de Oliveira | 1 a 9 | abertura, a persona (a Ana, hipotética), o problema, a nossa solução, as perguntas do gestor, a resposta para a Ana com os dados reais, por que São Paulo, os cinco assuntos e o roteiro | 5 min |
   | 2 | Thiago Rodrigues Gouveia da Silva | 10 a 14 | fontes, integração, problemas nos dados, grão e aditividade, estrela Matrícula | 5 min |
   | 3 | Daniel Afonso Borges dos Santos | 15 a 19 | estrelas Fila, Desfecho, Ocupação de Turma e População, constelação | 5 min |
   | 4 | Luís Antônio Arruda Soares | 20 a 24 | consultas, resultados com os dados reais, decisões, encerramento | 5 min |

   O enunciado exige que todos apresentem e que o tempo de cada um seja homogêneo; um teste confere que os quatro blocos somam o mesmo tempo nas notas. Os quatro blocos de 5 minutos fecham os 20 minutos pedidos; as perguntas vêm durante a apresentação. A mensagem de cada slide, as perguntas prováveis e o checklist do dia estão em [12 Ensaio da apresentação](12-ensaio-da-apresentacao.md).

3. **Entregar** o PDF [relatorio/relatorio-projeto1.pdf](relatorio/relatorio-projeto1.pdf) e a apresentação no local definido no critério de avaliação da disciplina.

## Para o Projeto 2

O enunciado do Projeto 1 diz que as correções apontadas na primeira parte devem ser feitas por nós e que o documento corrigido do Projeto 1 é entregue junto com o da segunda parte. Vamos guardar o retorno da professora.

## Regenerar a apresentação

Os slides são gerados por [apresentacao/gerar.js](apresentacao/gerar.js), com as figuras de [modelagem/](modelagem/) (as mesmas do relatório, convertidas de `modelagem/figuras.tex`). Para mudar texto ou números:

```bash
npm install pptxgenjs
```

```bash
node docs/apresentacao/gerar.js
```

Se o pptxgenjs estiver instalado em outra pasta, a variável `PPTXGENJS` aponta para ela. O slide de roteiro é montado no fim do script a partir do bloco de cada slide, então mudar um slide de bloco atualiza o roteiro sozinho. O roteiro não mostra tempo; o tempo previsto de cada slide fica só nas notas. O arquivo `.pptx` também pode ser editado direto no PowerPoint ou no Google Slides.

O visual também sai do script. As cores ficam no objeto `COR`, no começo do `gerar.js`, e entram no tema do arquivo; no PowerPoint elas aparecem na paleta de cores do tema. Cada slide traz a etiqueta do bloco e de quem apresenta acima do título, e o rodapé mostra o número da página ("7 / 21"). Todos os slides entram com transição de esmaecimento. Os cartões e números de destaque aparecem em sequência, sem clique, a cada 0,25 s. Para um elemento novo entrar animado, dê a ele a ordem de entrada com `ordem` (ou `anim(n)`), como fazem os cartões existentes.

A versão em [HTML](apresentacao/apresentacao-projeto1.html) não sai do `gerar.js`: o texto de cada slide se edita no próprio arquivo. A seção [Versão em HTML](11-guia-do-grupo.md#versão-em-html) do guia do grupo explica as teclas, como gerar o PDF e como atualizar as figuras guardadas dentro dele.
