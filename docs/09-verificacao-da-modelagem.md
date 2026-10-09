# Verificação da modelagem

Revisão completa do modelo dimensional: os desenhos, o banco (DDL), o relatório, a documentação e os dados precisam contar a mesma história. Parte é automática e roda a cada push no CI; parte é revisão conceitual.

As imagens dos esquemas estão em [modelagem/](modelagem/): [modelagem.pdf](modelagem/modelagem.pdf) traz a constelação, as cinco estrelas e a matriz de barramento, uma por página, e há um PNG de cada esquema.

## Como foi verificado

| Camada | Onde | Quando roda |
|---|---|---|
| Desenhos × DDL × relatório × documentação | [tests/test_modelo.py](../tests/test_modelo.py), 22 testes | a cada push (GitHub Actions) e em `pytest` |
| Hierarquias e conformidade nos dados | verificações Q13 e Q14 de `dw-sme verificar` | a cada carga; com os dados reais, na próxima `dw-sme tudo` |
| Conceitos de modelagem e texto do relatório | revisão manual, registrada abaixo | uma vez, nesta revisão |

## Resultado das verificações automáticas

| Verificação | O que confere | Resultado |
|---|---|---|
| Fatos e dimensões | os desenhos têm as mesmas 5 tabelas de fatos e 14 dimensões do banco | OK |
| Atributos de cada caixa | todo rótulo dos 5 esquemas estrela existe no DDL, e toda coluna do DDL aparece na caixa (ou a caixa está marcada como parcial com "...") | OK depois das correções |
| Chaves estrangeiras | as FK de cada tabela de fatos no desenho são exatamente as do banco | OK |
| Ligações das estrelas | cada caixa de dimensão está ligada ao fato o número certo de vezes (Data duas vezes, pelos dois papéis) | OK |
| Chaves estrangeiras declaradas | toda coluna `chave_*` dos fatos está na lista conferida pela verificação Q01 | OK |
| Chave artificial | todas as 14 dimensões têm chave primária inteira `chave_*` | OK |
| Constelação | as ligações do desenho da constelação são as mesmas das FK do banco, e as linhas tracejadas são os 5 rollups encolhidos | OK depois das correções |
| Matriz de barramento | a matriz do relatório e a do PDF de modelagem marcam exatamente as dimensões que cada fato usa | OK |
| Hierarquias escritas | as hierarquias do relatório, dos comentários do DDL e de [03 Modelo dimensional](03-modelo-dimensional.md) são as mesmas | OK depois das correções |
| Hierarquias nos dados (Q13) | cada `A ≤ B` vale como dependência funcional: todo membro de A pertence a um único membro de B (23 relações) | OK nos dados de teste e nos dados reais (13,4 milhões de matrículas, 26.889 setores) |
| Conformidade (Q14) | Etapa tem os mesmos códigos, nomes e níveis da Série; toda faixa da Idade existe na Faixa Etária e contém a idade; anos e meses de Tempo, Ano Letivo e Data se correspondem; todo distrito de escola existe em Território | OK nos dados de teste e nos dados reais |
| Rollups encolhidos | cada par de dimensões conformadas compartilha o atributo de conformidade (ano; ano e mês; etapa e nível; faixa IBGE; distrito) | OK |

## Problemas encontrados e corrigidos

| # | Problema | Onde estava | Correção |
|---|---|---|---|
| 1 | **Hierarquia inválida na dimensão Idade.** O modelo declarava `idade ≤ faixa escolar ≤ grupo etário`, mas a faixa escolar não cabe num único grupo etário: 11 a 14 anos reúne criança (11) e adolescente (12 a 14), e 30 ou mais reúne adulto e idoso. A verificação Q13 mede 2 violações. | relatório (seções 1.5 e 2.1), DDL, docs/03 | três hierarquias paralelas: `idade ≤ faixa escolar`, `idade ≤ grupo etário`, `idade ≤ faixa IBGE`; um teste registra por que a cadeia antiga não vale |
| 2 | **Caixas incompletas sem aviso.** A caixa Série dos esquemas Desfecho e Ocupação de Turma omitia "ordem"; a caixa Data do esquema Matrícula omitia "nome do dia"; a caixa Escola omitia "versão atual". | esquemas estrela | atributos acrescentados |
| 3 | **Nome diferente para a mesma dimensão.** A constelação chamava de "Dimensão Situação" a dimensão que nas estrelas e no banco é Situação da Matrícula. | constelação | rótulo igualado |
| 4 | **Afirmação imprecisa.** O fato Matrícula era chamado de "tabela de fatos sem fato", mas tem uma medida (dias de matrícula). O que ele usa é a técnica das tabelas sem fato: a ocorrência contada por um campo artificial igual a 1. | relatório, docs/03, DDL, slides | texto corrigido nos quatro lugares |
| 5 | **Hierarquias não enunciadas no formato padrão.** docs/03 não trazia `etapa ≤ nível` e escrevia a hierarquia da Data no meio de outro parágrafo. | docs/03 | enunciadas no mesmo formato das demais |

Depois das correções, os desenhos, o PDF de modelagem, o relatório e os slides foram gerados de novo a partir dos mesmos arquivos TikZ.

## Checklist do enunciado sobre a modelagem

| Item | Situação |
|---|---|
| Grão de cada processo declarado antes das dimensões | 5 processos, cada um com grão (relatório, seção 1.4) |
| Dimensões que se aplicam a cada linha da tabela de fatos | tabela da seção 1.4 e matriz de barramento |
| Atributos de cada dimensão, com significado e relação entre eles | 14 tabelas de atributos com papel (chave, hierarquia, descritivo) e povoamento (seção 1.5) |
| Fato aditivo, semiaditivo ou não aditivo; derivação dos derivados | seção 1.6 (aditivos, semiaditivos em Fila e População, derivados não aditivos: taxas e alunos por turma) |
| Povoamento de cada atributo e fato, com integração | coluna "Povoamento" e seção 1.7 |
| Desenho de cada esquema estrela | 5 esquemas (seção 2 e [modelagem.pdf](modelagem/modelagem.pdf)) |
| Hierarquias com o operador de ordenação parcial | seção 2, conferidas nos dados (Q13) |
| Função de agregação de cada fato | seção 2, um parágrafo por estrela |
| Desenho da constelação e processo de projeto | seção 2.6, com matriz de barramento |
| Chave artificial, bugiganga, dimensão degenerada, tabela de fatos sem fato | as três primeiras usadas e conferidas; da quarta, a técnica (campo artificial) |
| Esquemas que suportam as consultas | as 8 consultas rodam sobre o modelo nos testes |

## Pontos de atenção (não são erros, estão documentados)

- **DRE da escola e DRE do distrito.** Território guarda a DRE predominante do distrito; Escola guarda a DRE da própria escola. Em poucos distritos as duas diferem. As consultas 1, 6 e 8 usam a de Território; a consulta 4 usa a da Escola.
- **Onde a criança mora e onde estuda.** A matrícula é contada pelo distrito da escola, e a população pelo distrito de residência. Por isso a consulta 7 fala em oferta por criança residente, não em taxa de atendimento.
- **Datas de referência diferentes.** A idade do aluno é a de 31/03 do ano letivo; o Censo é de 31/07/2022.
- **Turma multisseriada.** A turma é identificada por ano, escola, nome da turma, série e turno, então uma turma com várias séries aparece como uma turma por série.
- **Dados reais dos fatos novos.** Na carga com os dados reais, Q11 (ocupação), Q13 (hierarquias) e Q14 (conformidade) deram OK. Q12 (população) dá ALERTA porque o IBGE suprime 6.543 valores em setores pequenos, que ficam nulos; nenhum setor ficou sem distrito correspondente na SME.
- **Notação.** Os desenhos seguem a notação do artigo da disciplina. Vale conferir com a das aulas, como pede o enunciado.

## Como repetir a verificação

```bash
.venv/Scripts/python -m pytest tests/test_modelo.py -v
```

```bash
.venv/Scripts/python -m dw_sme verificar
```

O primeiro comando confere desenhos, DDL, relatório e documentação. O segundo confere Q13 e Q14 no banco carregado e grava o resultado em `data/relatorios/qualidade.md`.
