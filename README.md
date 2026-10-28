# Rede Municipal Paulistana: oferta escolar e demanda não atendida

[![testes](https://github.com/kevennlaranjeira/OLAP2026/actions/workflows/testes.yml/badge.svg)](https://github.com/kevennlaranjeira/OLAP2026/actions/workflows/testes.yml)

Nosso data warehouse sobre a rede municipal de educação de São Paulo, feito para os trabalhos práticos da disciplina **SCC0245 Processamento Analítico de Dados** (ICMC-USP, profa. Cristina Dutra de Aguiar).

A pergunta que organiza o modelo: **onde existe fila por vaga, onde existe oferta, e o que acontece com quem consegue a vaga**. Ela só é respondível porque a Secretaria Municipal de Educação publica, ao mesmo tempo, o microdado de cada matrícula e a fila de espera por distrito. O Censo 2022 do IBGE acrescenta quantas crianças moram em cada lugar.

Tema da disciplina: política pública municipal. O data warehouse serve para o gestor decidir onde abrir vagas de educação infantil, acompanhar a ocupação das turmas e monitorar o abandono escolar por região.

Chegou agora no grupo? Leia o [Guia do grupo](docs/11-guia-do-grupo.md): ele explica como entrar no repositório, sugerir mudanças, editar o relatório e os slides e rodar os testes.

## Onde fica cada coisa

| Procuro... | Está em |
|---|---|
| o relatório para ler (PDF de entrega) | [docs/relatorio/relatorio-projeto1.pdf](docs/relatorio/relatorio-projeto1.pdf) |
| o texto-fonte do relatório, para editar (LaTeX) | [docs/relatorio/relatorio-projeto1.tex](docs/relatorio/relatorio-projeto1.tex) |
| os desenhos dos esquemas estrela e da constelação | fonte em [docs/relatorio/esquemas/](docs/relatorio/esquemas/) (um `.tex` por desenho); imagens PNG e PDF em [docs/modelagem/](docs/modelagem/) |
| a apresentação | [docs/apresentacao/apresentacao-projeto1.pptx](docs/apresentacao/apresentacao-projeto1.pptx), gerada por [docs/apresentacao/gerar.js](docs/apresentacao/gerar.js), e a mesma em HTML, [docs/apresentacao/apresentacao-projeto1.html](docs/apresentacao/apresentacao-projeto1.html), que abre no navegador, e em PDF, [docs/apresentacao/apresentacao-projeto1.pdf](docs/apresentacao/apresentacao-projeto1.pdf), que dá para ver no próprio GitHub |
| o que falta para a entrega e quem apresenta cada parte | [docs/08-pendencias-da-entrega.md](docs/08-pendencias-da-entrega.md) |
| as consultas OLAP em SQL | [src/dw_sme/sql/consultas/](src/dw_sme/sql/consultas/), uma por arquivo; explicadas em [docs/05-consultas.md](docs/05-consultas.md) |
| a criação das tabelas do data warehouse | [src/dw_sme/sql/ddl/](src/dw_sme/sql/ddl/) |
| o resultado das 14 verificações de qualidade | [docs/relatorios/qualidade.md](docs/relatorios/qualidade.md) |
| o código do pipeline | [src/dw_sme/](src/dw_sme/) (ver [Estrutura](#estrutura)) |
| os testes | [tests/](tests/); o que cada um confere está no [guia, parte 7](docs/11-guia-do-grupo.md#7-rodar-os-testes) |
| o que o GitHub roda a cada envio | [.github/workflows/testes.yml](.github/workflows/testes.yml) (lint e testes) e [.github/workflows/relatorio.yml](.github/workflows/relatorio.yml) (compila o relatório e deixa o PDF para baixar) |
| os dados baixados e o banco | na pasta `data/` do seu computador, depois de rodar o pipeline; ela não vai para o GitHub |

## O que tem aqui

| | |
|---|---|
| Fontes | Microdados da Rede Municipal de Educação (Matrículas) e Demanda Registrada e Matrículas, ambas da SME-SP; Censo Demográfico 2022, Agregados por Setores Censitários, do IBGE |
| Assuntos de interesse | matrículas; fila (demanda registrada); capacidade e ocupação das turmas; população em idade escolar; oferta escolar por setor |
| Recorte | 2015 a 2024 (configurável); população na data do Censo 2022 |
| Volume | 13,4 milhões de matrículas, 551 mil turmas, 44 meses de fila × 96 distritos × 8 etapas, 26.889 setores censitários com 11,4 milhões de moradores |
| Modelo | constelação com 5 tabelas de fatos e 14 dimensões |
| Banco | DuckDB, um arquivo de ~335 MB, carregado em ~3,5 minutos |
| Testes | 505 testes unitários, de integração e de funcionamento (22 conferem a modelagem, 54 a coerência entre código, documentos, slides e imagens, 14 o uso pela linha de comando e em volume), cobertura de 99%, sem depender de internet nem dos dados reais |
| Consultas | dois drill-down, um roll-up, slice and dice, pivot e três drill-across |

## O que os dados mostram

- A fila de creche em junho caiu de **124.741 crianças em 2015 para 3.633 em 2024**. A fração da demanda que ficava fora da rede passou de 34% para 1%. A pré-escola zerou a fila em 2018.
- No mesmo período as matrículas de creche passaram de 320 mil para 474 mil, e **85% delas estão na rede conveniada**, quase todas em jornada integral.
- As duas bases da prefeitura concordam com diferença abaixo de 1% de 2015 a 2020, quando se contam as matrículas ativas em junho. De 2022 em diante o microdado publicado passa a ter códigos corrompidos e vínculos encerrados sem data de fim, e a concordância cai; o pipeline mede e registra isso em vez de esconder.
- Na data do Censo 2022 moravam no município 598 mil crianças de 0 a 4 anos, e a rede municipal tinha 514 mil matrículas ativas dessa idade, **86 por 100 crianças**. A média esconde distâncias grandes: em 25 distritos são menos de 50 por 100, em outros 25 mais de 100, porque a matrícula conta onde a escola fica e a população onde a criança mora.
- A creche funciona com perto de **11 crianças por turma** em todas as DREs; no fundamental, o município tem de 28,7 a 31,6 alunos por turma em 2019 e 2024.

## Como rodar

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python -m pip install -e ".[dev]"
```

```bash
.venv/Scripts/python -m dw_sme tudo
```

O comando baixa as bases do portal da prefeitura e o Censo 2022 do IBGE, prepara, carrega o DuckDB em `data/dw/dw_sme.duckdb`, roda as verificações de qualidade e as consultas. Detalhes, etapas separadas e opções em [docs/07-como-executar.md](docs/07-como-executar.md). O pacote de 2019 a 2021 vem em `.rar` e exige o 7-Zip.

## Verificações

```bash
.venv/Scripts/python -m pytest --cov=dw_sme
```

```bash
.venv/Scripts/python -m ruff check src tests
```

O GitHub Actions roda as duas a cada push, em Python 3.11 e 3.13, e falha se a cobertura cair abaixo de 85%. Com os dados reais, `dw-sme verificar` acrescenta catorze verificações sobre o banco carregado (integridade referencial, conservação entre fatos, reconciliação entre as bases, ligação da população ao território, hierarquias e conformidade das dimensões); o resultado da última carga com os dados reais está em [docs/relatorios/qualidade.md](docs/relatorios/qualidade.md).

## Documentação

| Documento | Conteúdo |
|---|---|
| [11 Guia do grupo](docs/11-guia-do-grupo.md) | **comece por aqui**: acesso ao repositório, onde fica o texto-fonte do relatório, como sugerir mudanças, editar o relatório e os slides, testar e enviar pelo GitHub |
| [01 Fontes de dados](docs/01-fontes-de-dados.md) | as três bases, os sete formatos da planilha de fila, as variações do microdado ano a ano, o layout do Censo 2022 |
| [02 Fluxo de dados](docs/02-fluxo-de-dados.md) | do portal ao banco, etapa por etapa, com o argumento de cada escolha |
| [03 Modelo dimensional](docs/03-modelo-dimensional.md) | grãos, dimensões, hierarquias, fatos, aditividade e a constelação |
| [04 Integração e qualidade](docs/04-integracao-e-qualidade.md) | cada problema encontrado nos dados, com evidência e tratamento |
| [05 Consultas](docs/05-consultas.md) | as oito consultas analíticas, com pergunta, justificativa e resultado |
| [06 Decisões](docs/06-decisoes.md) | 23 decisões de projeto, com alternativa descartada e argumento |
| [07 Como executar](docs/07-como-executar.md) | instalação, comandos, testes e problemas comuns |
| [08 Pendências da entrega](docs/08-pendencias-da-entrega.md) | o que ainda falta a gente fazer antes de entregar e quem apresenta cada parte |
| [09 Verificação da modelagem](docs/09-verificacao-da-modelagem.md) | como a modelagem foi conferida, o que foi corrigido e os pontos de atenção |
| [10 Auditoria do trabalho](docs/10-auditoria-do-trabalho.md) | revisão de ponta a ponta: código, processo, documentos, slides e imagens |
| [12 Ensaio da apresentação](docs/12-ensaio-da-apresentacao.md) | a ideia em um minuto, a mensagem de cada slide, as perguntas prováveis e o checklist do dia 29/10 |

## Estrutura

```
docs/
  relatorio/       relatório do Projeto 1: texto-fonte (.tex), desenhos (esquemas/) e PDF
  apresentacao/    slides (.pptx, .html e .pdf) e o script que gera o .pptx (gerar.js)
  modelagem/       os esquemas em PNG e PDF
  relatorios/      relatório de qualidade da última carga com os dados reais
  01 a 12 (.md)    documentação técnica, guia do grupo e ensaio
src/dw_sme/
  extracao/        cliente do portal CKAN e do diretório do IBGE, manifesto de downloads, pacotes .zip/.rar
  transformacao/   regras de normalização, parser da fila, etapas, idade, datas, escolas, população
  carga/           carga do DuckDB (staging, correspondências, dimensões, fatos)
  qualidade/       catorze verificações e o relatório
  consultas/       executor das consultas
  sql/ddl/         criação das dimensões e dos fatos
  sql/consultas/   as oito consultas, uma por arquivo
  pipeline.py      etapas baixar, preparar, carregar, verificar, consultar
  cli.py           linha de comando dw-sme
tests/             testes, fixtures reais da fila, microdado e Censo sintéticos
.github/workflows/ testes e lint a cada push; compilação do relatório quando ele muda
pyproject.toml     pacote, dependências e configuração de pytest, ruff e pyright
```

## Grupo 7

| Nome | Nº USP |
|---|---|
| Kevenn Laranjeira de Oliveira (líder) | 18046529 |
| Thiago Rodrigues Gouveia da Silva | 18066911 |
| Daniel Afonso Borges dos Santos | 12608581 |
| Luís Antônio Arruda Soares | 12559486 |

Dados: Prefeitura de São Paulo, Secretaria Municipal de Educação, Portal de Dados Abertos, licença Creative Commons; IBGE, Censo Demográfico 2022, Agregados por Setores Censitários.
