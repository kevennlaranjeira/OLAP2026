# Fontes de dados

O modelo usa três fontes, as mesmas registradas na planilha do grupo. As duas principais vêm do [Portal de Dados Abertos da Prefeitura de São Paulo](https://dados.prefeitura.sp.gov.br/organization/educacao1), publicadas pela Secretaria Municipal de Educação (SME) sob licença Creative Commons. O enunciado permite que as fontes venham da mesma plataforma; aqui elas têm grãos, formatos e vocabulários diferentes, e a integração entre elas é trabalho de verdade. A terceira é o Censo Demográfico 2022 do IBGE, que traz a população residente por idade, ou seja, a demanda potencial que nenhuma das bases da prefeitura mede.

| | Fonte | Instituição | Assunto de interesse que sustenta |
|---|---|---|---|
| 1 | Microdados da Rede Municipal de Educação, Matrículas | SME-SP | matrículas; capacidade e ocupação das turmas; oferta escolar |
| 2 | Demanda Registrada e Matrículas | SME-SP | fila (demanda registrada) |
| 3 | Censo Demográfico 2022, Agregados por Setores Censitários | IBGE | população em idade escolar |

| | Microdados da Rede Municipal de Educação, Matrículas | Demanda Registrada e Matrículas |
|---|---|---|
| Identificador no portal | `microdados-matriculas` | `demanda-e-matriculas` |
| Grão publicado | uma matrícula (vínculo aluno-turma) | distrito, com uma coluna por etapa |
| Periodicidade | anual | trimestral até 2022, bimestral desde 2023; série histórica 2006-2017 |
| Volume no recorte 2015-2024 | 15,7 milhões de linhas nos arquivos lidos, 13,4 milhões de escolarização | 44 planilhas, 96 distritos cada |
| Formato | CSV dentro de .zip (e um .rar), até ~900 MB por ano descompactado | CSV de duas linhas de cabeçalho, ~8 KB |
| Usada para | fato de matrícula, fato de desfecho, dimensões Escola, Série, Turno, Idade, Data, bugigangas, DRE do território | fato de fila, dimensão Tempo, distritos do território |

## Microdados de Matrículas

Cada linha é a matrícula de um aluno numa turma, com 94 a 97 colunas: escola, turma, turno, série, modalidade, idade, sexo, raça e cor, 13 a 17 indicadores de deficiência, datas da matrícula e 12 indicadores de desfecho. Não há endereço nem distrito de residência do aluno: o distrito publicado é o da escola.

### Pacotes usados

| Recurso no portal | Arquivos de escolarização dentro do pacote | Linhas brutas |
|---|---|---|
| Microdados de Matrículas - 2015-2018 (.zip) | um CSV por ano | 1,59 a 1,76 milhão por ano |
| Microdados de Matrículas - 2019-2021 (.rar) | um CSV por ano (2021 em .txt) | 1,50 a 1,81 milhão por ano |
| Microdados de Matrículas - 2022 (.zip) | escolarização separada das atividades complementares | 1,56 milhão |
| Microdados de Matrícula - 2023 (.zip) | educação infantil e demais etapas em arquivos separados | 1,16 milhão |
| Microdados de Matrícula - 2024 (.zip) | idem | 1,42 milhão |

### O que muda de um ano para outro

| Aspecto | Variação encontrada |
|---|---|
| Separador | barra vertical `\|` de 2015 a 2018; ponto e vírgula depois |
| Codificação | latin-1, exceto educação infantil de 2023 (UTF-8 com BOM) |
| Nome da coluna de idade | `idade_aluno_31_03` (2015-17), `IDADE_ALUNO_3103` (2018-19), `IDADE_ALUNO_MAR` (2020 em diante) |
| Indicadores de deficiência | `DEF_X` (2015-17), `DEF__X` (2018 em diante); 4 indicadores novos em 2024 |
| Atividades complementares | no mesmo arquivo até 2021 (filtrar `TURMA_ESCOL = 'S'`); em arquivo próprio depois |
| Descrição do turno | ausente em todas as linhas de 2021; códigos de 2021 com numeração própria (4 a 9) |
| Datas de matrícula | cinco formatos; ausentes em 2021; metade de 2024 em número serial do Excel |
| Idade | vírgula decimal em 2020 (`5,00`); nulos em 2021-2022; 1900 usado como ano de nascimento padrão |
| Códigos | íntegros até 2021; embaralhados em 2022; destruídos em notação científica em 2023-2024 |

O documento [Integração e qualidade](04-integracao-e-qualidade.md) descreve o tratamento de cada item e o efeito medido.

## Demanda Registrada e Matrículas

Para cada um dos 96 distritos, a planilha publica matrículas por etapa (creche, pré-escola, fundamental I e II, EJA I e II, ensino médio, educação profissional), matrículas em processo e a demanda registrada, que é a fila de quem pediu vaga e ainda não foi atendido.

### Sete formatos

| Formato | Período | Colunas | Como a fila de creche aparece |
|---|---|---|---|
| H | 2006 a 2017 (série histórica) | 20, formato longo | só o total |
| C | mar/2018 | 21 | só o total; matrícula em processo para 6 etapas |
| B | jun/2018 a jun/2019 | 17 | só o total |
| F | set/2019 | 18 | (1) sem opção; (2) recusou vaga e preferiu esperar unidade específica |
| E | dez/2019 a jun/2020 | 21 | (1) sem opção; (2) com opção por unidade |
| D | set/2020 | 27 | (1) até 30 dias; (2) mais de 30 dias; (3) com opção; sem total; colunas soltas no fim |
| A | dez/2020 a jun/2026 | 23 | (1) sem opção até 30 dias; (2) sem opção mais de 30 dias; (3) com opção; total |

O significado das colunas numeradas mudou junto com o formato e só é dado pelas notas de rodapé de cada arquivo. A série histórica usa retorno de carro sozinho como fim de linha e traz duas colunas (`DEM_PREF_CRECHE`, `DEM_PREF_PRE`) que não constam do dicionário oficial; sem definição publicada, elas não são carregadas.

### Observações publicadas nos rodapés

| Mês | Nota |
|---|---|
| mar/2018 | matrículas não efetivadas de 8 a 28 de março pelas unidades em greve |
| set/2020 | matrícula em processo = vaga disponibilizada aguardando documentação; 30 dias de análise para atendimento com transporte escolar |
| dez/2024 | a nota (1) não foi publicada; o significado é herdado do formato A, já que as notas (2) e (3) coincidem com ele |

As notas ficam na coluna `observacao` da dimensão Tempo.

## Censo Demográfico 2022: Agregados por Setores Censitários

O IBGE publica os resultados do universo do Censo 2022 por setor censitário, a menor unidade territorial do Censo, em arquivos CSV e XLSX no diretório [Agregados_por_Setores_Censitarios](https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/). O modelo usa dois temas:

| Tema | Arquivo | Colunas usadas | Para quê |
|---|---|---|---|
| Demografia | `Agregados_por_setores_demografia_BR` | `CD_SETOR`, `V01031` a `V01041` | pessoas residentes por grupo de idade: 0 a 4, 5 a 9, 10 a 14, 15 a 19, 20 a 24, 25 a 29, 30 a 39, 40 a 49, 50 a 59, 60 a 69, 70 anos ou mais |
| Básico | `Agregados_por_setores_basico_BR` | `CD_SETOR`, `NM_DIST` | nome do distrito a que o setor pertence |

| Aspecto | Valor |
|---|---|
| Grão publicado | setor censitário x grupo de idade |
| Data de referência | noite de 31 de julho para 1º de agosto de 2022 |
| Cobertura | o país inteiro; entram só os setores do município de São Paulo (código IBGE 3550308) |
| Código do setor | 15 dígitos: UF (2), município (5), distrito (2), subdistrito (2), setor (4) |
| Idade | grupos quinquenais até 29 anos e decenais depois; não há idade simples por setor |

Duas limitações orientam o uso:

- **Os grupos de idade não recortam nas etapas.** A creche atende de 0 a 3 anos e a pré-escola de 4 e 5; o grupo do IBGE é 0 a 4. A faixa comparável entre as bases é, portanto, 0 a 4 anos, e a dimensão Idade carrega o mesmo corte (`faixa_ibge`) para que a matrícula possa ser agregada nele.
- **A população é contada onde a criança mora; a matrícula, onde a escola fica.** O microdado não traz endereço do aluno. A razão entre matrícula e população por distrito é oferta por criança residente, não taxa de atendimento dos moradores.

**Situação no repositório.** A leitura, a carga e as verificações estão implementadas e testadas com arquivos sintéticos no layout descrito acima. A leitura procura as colunas pelo nome e para com erro se alguma faltar, de modo que a primeira carga com os arquivos reais confirma o layout. Os números da população ainda não aparecem na documentação porque os arquivos reais não foram carregados no ambiente em que esta parte foi escrita; nada foi estimado no lugar deles.

## Dicionários de dados

A etapa `baixar` também guarda os dicionários publicados pela SME em `data/raw/dicionarios/`, como documentação da origem: dicionário de variáveis dos microdados, dicionário da planilha de demanda e dicionário da série histórica.

## Proveniência

Cada arquivo baixado fica registrado num `manifesto.json` com URL, identificador do recurso no portal, tamanho, SHA-256 e data do download. Rodar o pipeline de novo confere o hash e só baixa o que mudou ou está corrompido. Os arquivos do IBGE seguem a mesma regra, com manifesto próprio em `data/raw/ibge/`.
