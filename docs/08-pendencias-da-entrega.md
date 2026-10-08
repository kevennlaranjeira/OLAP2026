# Pendências da entrega do Projeto 1

O que já está pronto e o que só o grupo pode fazer antes de entregar. O enunciado pede dois materiais: o documento em PDF e a apresentação.

## Situação dos itens do enunciado

| Item do enunciado | Onde está | Situação |
|---|---|---|
| Tema geral | relatório, seção 1.1 | pronto |
| Pelo menos 3 assuntos de interesse | relatório, seção 1.2 (os cinco da planilha do grupo) | pronto |
| Pelo menos 2 esquemas estrela | relatório, seções 2.1 a 2.5 (cinco estrelas) | pronto |
| Pelo menos 1 constelação de fatos, com desenho e processo de projeto | relatório, seção 2.6, e matriz de barramento | pronto |
| Pelo menos 2 fontes de dados | relatório, seção 1.3 (três fontes: duas da SME e o Censo 2022 do IBGE) | pronto |
| Pelo menos 5 consultas: 2 roll-up ou drill-down, 1 slice and dice, 1 pivot, 1 drill-across | relatório, seção 3 (oito consultas: 3, 1, 1 e 3) | pronto |
| Capa com instituição, curso, disciplina, professora, trabalho, integrantes com Nº USP e data | relatório, capa | **falta curso e data** |
| Índice | relatório | pronto |
| Grão, dimensões, fatos, atributos e relações, aditividade, fatos derivados | relatório, seções 1.4 a 1.6 | pronto |
| Povoamento de cada atributo e de cada fato, com integração | relatório, seções 1.5 a 1.7 (coluna "Povoamento" em cada dimensão) | pronto |
| Hierarquias com o operador de ordenação parcial e função de agregação de cada fato | relatório, seção 2 | pronto |
| Chave artificial, bugiganga, dimensão degenerada, campo artificial de fatos sem fato | relatório, seções 2.6 e 1.5 | pronto |
| Apresentação com motivação, fontes, estrelas, constelação, consultas e decisões, com tempo homogêneo | [apresentacao/apresentacao-projeto1.pptx](apresentacao/apresentacao-projeto1.pptx), 17 slides em quatro blocos | pronta; falta ensaiar |

## O que só o grupo pode fazer

1. **Preencher o curso e a data de entrega na capa.** No começo de [relatorio/relatorio-projeto1.tex](relatorio/relatorio-projeto1.tex) há duas linhas:

   ```latex
   \newcommand{\curso}{[NOME DO CURSO]}
   \newcommand{\dataentrega}{[DATA DE ENTREGA]}
   ```

   Troque o texto entre colchetes e compile de novo com XeLaTeX (`latexmk -xelatex relatorio-projeto1.tex` dentro de `docs/relatorio/`, ou no Overleaf enviando o `.tex` e a pasta `esquemas/` e escolhendo o compilador XeLaTeX). Se os integrantes forem de cursos diferentes, escreva os cursos separados por vírgula.

2. **Conferir a notação dos esquemas com a das aulas.** A verificação completa da modelagem está em [09 Verificação da modelagem](09-verificacao-da-modelagem.md). Os desenhos seguem a notação do artigo da disciplina (caixa com o nome da tabela, PK e FK, fato no centro com borda grossa) e as hierarquias usam `≤`. O enunciado diz que a notação tem de ser a mesma da sala de aula. Se a das aulas for diferente, os desenhos estão em `docs/relatorio/esquemas/*.tex` e o estilo comum em `estilo.tex`.

3. **Rodar a carga com o Censo 2022 e medir as consultas 7 e 8.** O Projeto 1 pede as consultas só na forma textual, então isso não bloqueia a entrega. Mas os fatos de turma e de população foram acrescentados depois da última carga com os dados reais, e os números deles ainda não existem. Num computador com internet:

   ```bash
   .venv/Scripts/python -m dw_sme tudo
   ```

   Se o download do IBGE falhar, baixe à mão os temas Básico e Demografia dos Agregados por Setores Censitários (ver [07 Como executar](07-como-executar.md#população-do-censo-2022)) para `data/raw/ibge/` e rode `carregar`, `verificar` e `consultar`. Depois:
   - confira as verificações Q11 e Q12 em `data/relatorios/qualidade.md` (Q12 mostra se algum setor ficou sem distrito correspondente na SME);
   - copie `data/relatorios/qualidade.md` para `docs/relatorios/qualidade.md`;
   - preencha as seções "Resultado" de C7 e C8 em [05 Consultas](05-consultas.md) com os números de `data/relatorios/consultas/c7_*.csv` e `c8_*.csv`, se quiserem mostrá-los na apresentação.

4. **Ensaiar a apresentação.** As notas de cada slide dizem quem apresenta e o que falar:

   | Bloco | Integrante | Slides | Conteúdo |
   |---|---|---|---|
   | 1 | Kevenn Laranjeira de Oliveira | 1 a 4 | abertura, problema, perguntas do gestor, por que São Paulo |
   | 2 | Thiago Rodrigues Gouveia da Silva | 5 a 8 | assuntos e processos, fontes, integração, qualidade |
   | 3 | Daniel Afonso Borges dos Santos | 9 a 13 | grão e aditividade, cinco estrelas, constelação |
   | 4 | Luís Antônio Arruda Soares | 14 a 17 | consultas, resultados, decisões, encerramento |

   O enunciado exige que todos apresentem com tempo parecido; ajuste ao limite que a professora definir. O bloco 3 tem um slide a mais, mas três deles são figuras.

5. **Entregar** o PDF [relatorio/relatorio-projeto1.pdf](relatorio/relatorio-projeto1.pdf) e a apresentação no local definido no critério de avaliação da disciplina.

## Para o Projeto 2

O enunciado do Projeto 1 diz que as correções apontadas na primeira parte devem ser feitas pelo grupo e que o documento corrigido do Projeto 1 é entregue junto com o da segunda parte. Guardem o retorno da professora.

## Regenerar a apresentação

Os slides são gerados por [apresentacao/gerar.js](apresentacao/gerar.js), com as figuras de [modelagem/](modelagem/) (as mesmas do relatório, convertidas de `modelagem/figuras.tex`). Para mudar texto ou números:

```bash
npm install pptxgenjs
```

```bash
node docs/apresentacao/gerar.js
```

O arquivo `.pptx` também pode ser editado direto no PowerPoint ou no Google Slides.
