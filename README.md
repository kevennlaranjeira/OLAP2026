# Rede Municipal Paulistana: oferta escolar e demanda não atendida

[![testes](https://github.com/kevennlaranjeira/OLAP2026/actions/workflows/testes.yml/badge.svg)](https://github.com/kevennlaranjeira/OLAP2026/actions/workflows/testes.yml)

Data warehouse sobre a rede municipal de educação de São Paulo, construído para os trabalhos práticos da disciplina **SCC0245 Processamento Analítico de Dados** (ICMC-USP, profa. Cristina Dutra de Aguiar).

A pergunta que organiza o modelo: **onde existe fila por vaga, onde existe oferta, e o que acontece com quem consegue a vaga**. Ela só é respondível porque a Secretaria Municipal de Educação publica, ao mesmo tempo, o microdado de cada matrícula e a fila de espera por distrito. O Censo 2022 do IBGE acrescenta quantas crianças moram em cada lugar.

Tema da disciplina: política pública municipal. O data warehouse serve para o gestor decidir onde abrir vagas de educação infantil, acompanhar a ocupação das turmas e monitorar o abandono escolar por região.

## O que tem aqui

| | |
|---|---|
| Fontes | Microdados da Rede Municipal de Educação (Matrículas) e Demanda Registrada e Matrículas, ambas da SME-SP; Censo Demográfico 2022, Agregados por Setores Censitários, do IBGE |
| Assuntos de interesse | matrículas; fila (demanda registrada); capacidade e ocupação das turmas; população em idade escolar; oferta escolar por setor |
| Recorte | 2015 a 2024 (configurável); população na data do Censo 2022 |
| Volume | 13,4 milhões de matrículas, 44 meses de fila × 96 distritos × 8 etapas |
| Modelo | constelação com 5 tabelas de fatos e 14 dimensões |
| Banco | DuckDB, um arquivo de ~290 MB na última carga medida (antes dos fatos de turma e população), carregado em ~3 minutos |
| Testes | 372 testes unitários e de integração, cobertura de 94%, sem depender de internet nem dos dados reais |
| Consultas | dois drill-down, um roll-up, slice and dice, pivot e três drill-across |

## O que os dados mostram

- A fila de creche em junho caiu de **124.741 crianças em 2015 para 3.633 em 2024**. A fração da demanda que ficava fora da rede passou de 34% para 1%. A pré-escola zerou a fila em 2018.
- No mesmo período as matrículas de creche passaram de 320 mil para 474 mil, e **85% delas estão na rede conveniada**, quase todas em jornada integral.
- As duas bases da prefeitura concordam com diferença abaixo de 1% de 2015 a 2020, quando se contam as matrículas ativas em junho. De 2022 em diante o microdado publicado passa a ter códigos corrompidos e vínculos encerrados sem data de fim, e a concordância cai; o pipeline mede e registra isso em vez de esconder.
- Os resultados das consultas C7 (população × matrícula × fila) e C8 (ocupação das turmas) ainda não foram medidos com os dados reais: os fatos de turma e de população entraram depois da última carga, e nenhum número deles é apresentado antes da próxima.

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

O GitHub Actions roda as duas a cada push, em Python 3.11 e 3.13, e falha se a cobertura cair abaixo de 85%. Com os dados reais, `dw-sme verificar` acrescenta doze verificações sobre o banco carregado (integridade referencial, conservação entre fatos, reconciliação entre as bases, ligação da população ao território); o resultado da última carga medida, ainda com dez verificações, está em [docs/relatorios/qualidade.md](docs/relatorios/qualidade.md).

## Documentação

| Documento | Conteúdo |
|---|---|
| [01 Fontes de dados](docs/01-fontes-de-dados.md) | as três bases, os sete formatos da planilha de fila, as variações do microdado ano a ano, o layout do Censo 2022 |
| [02 Fluxo de dados](docs/02-fluxo-de-dados.md) | do portal ao banco, etapa por etapa, com o argumento de cada escolha |
| [03 Modelo dimensional](docs/03-modelo-dimensional.md) | grãos, dimensões, hierarquias, fatos, aditividade e a constelação |
| [04 Integração e qualidade](docs/04-integracao-e-qualidade.md) | cada problema encontrado nos dados, com evidência e tratamento |
| [05 Consultas](docs/05-consultas.md) | as oito consultas analíticas, com pergunta, justificativa e resultado |
| [06 Decisões](docs/06-decisoes.md) | 23 decisões de projeto, com alternativa descartada e argumento |
| [07 Como executar](docs/07-como-executar.md) | instalação, comandos, testes e problemas comuns |
| [Relatório de qualidade](docs/relatorios/qualidade.md) | gerado pela última carga com os dados reais |
| [Relatório do Projeto 1 (PDF)](docs/relatorio/relatorio-projeto1.pdf) | o documento de entrega, no formato do enunciado |
| [Apresentação (PPTX)](docs/apresentacao/apresentacao-projeto1.pptx) | slides da apresentação, com a divisão de tempo entre os integrantes |
| [Pendências da entrega](docs/08-pendencias-da-entrega.md) | o que só o grupo pode fazer antes de entregar |

## Estrutura

```
src/dw_sme/
  extracao/        cliente do portal CKAN e do diretório do IBGE, manifesto de downloads, pacotes .zip/.rar
  transformacao/   regras de normalização, parser da fila, etapas, idade, datas, escolas, população
  carga/           carga do DuckDB (staging, correspondências, dimensões, fatos)
  qualidade/       doze verificações e o relatório
  consultas/       executor das consultas
  sql/ddl/         criação das dimensões e dos fatos
  sql/consultas/   as oito consultas, uma por arquivo
  pipeline.py      etapas baixar, preparar, carregar, verificar, consultar
  cli.py           linha de comando dw-sme
tests/             testes, fixtures reais da fila, microdado e Censo sintéticos
docs/              documentação, relatório e apresentação
.github/workflows/ testes e lint a cada push
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
