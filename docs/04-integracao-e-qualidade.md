# Integração e qualidade

Cada problema abaixo foi encontrado nos dados reais, medido e tratado por uma regra testada. A coluna "Evidência" traz o número que justificou a decisão. O relatório gerado pela última carga está em [relatorios/qualidade.md](relatorios/qualidade.md).

## Integração entre as bases da SME

### Distrito: mesma entidade, mesma chave

As duas bases usam o nome do distrito como identificador, em maiúsculas e sem acento, com variações de espaço (a planilha de fila deixa um espaço sobrando no fim de cada nome). Normalizados, os 96 nomes de uma base coincidem um a um com os 96 da outra, sem nenhum distrito órfão. O distrito é a chave natural da dimensão Território.

### Hierarquia do território construída cruzando as bases

A planilha de fila só traz o distrito. A DRE vem do microdado: para cada distrito, a DRE com mais matrículas. Entre 2015 e 2021, no máximo dois distritos por ano têm escolas em mais de uma DRE; o atributo `participacao_dre` registra a fração das matrículas que a regra cobre em cada distrito. É essa integração que permite subir a fila de distrito para DRE (consultas C1 e C6).

### Etapa: dois vocabulários, um catálogo

| Planilha de fila | Microdado | Etapa no DW |
|---|---|---|
| Creche | `MODALIDADE = CRECHE` | CRECHE |
| Pré Escola | `MODALIDADE = PRE` | PRE |
| Ens. Fund.I | `FUND` com segmento `Fund1`/`FUN1A4`, ou série do 1º ao 5º ano | FUND_I |
| Ens. Fund.II | `FUND` com segmento `Fund2`/`FUN5A8`, ou série do 6º ao 9º ano | FUND_II |
| EJA I / EJA II | `EJA` com segmento `EJA1A4`/`EJA5A8`, ou módulo da série | EJA_I / EJA_II |
| Ens. Médio | `MEDIO` | MEDIO |
| Ed. Prof. | `EDPROF` | ED_PROF |
| (não há) | `MOVA`, `PROJ` | MOVA, PROJOVEM |

A educação especial (`ESPEC`) é classificada pelo segmento ou pelo texto da série e marcada em `educacao_especial`. As 148 combinações reais de modalidade, segmento e série foram classificadas; só 2.356 linhas ficaram sem etapa, todas de turmas que não são de escolarização (`CONVEE`, `REC`, `ATCOMP`) e que vieram dentro dos arquivos de escolarização de 2023-2024.

### Reconciliação: as duas bases contam a mesma coisa?

A planilha de fila publica também a matrícula por distrito e etapa. O microdado permite contar as matrículas ativas na mesma data. Se as duas bases concordam, a integração está certa e o distrito da planilha é o da escola.

| Ano | Creche (microdado / planilha) | Diferença | Distritos dentro de 2% |
|---|---|---|---|
| 2015 | 240.905 / 240.840 | +0,03% | 94% |
| 2016 | 278.040 / 277.899 | +0,05% | 98% |
| 2017 | 288.366 / 288.294 | +0,02% | 97% |
| 2018 | 313.787 / 313.598 | +0,06% | 95% |
| 2019 | 334.443 / 333.876 | +0,17% | 99% |
| 2020 | 338.927 / 341.966 | −0,89% | 86% |
| 2022 | 378.954 / 348.975 | +8,59% | 6% |
| 2023 | 373.348 / 338.786 | +10,20% | 1% |
| 2024 | 351.906 / 332.464 | +5,85% | 16% |

Até 2020 as bases concordam com diferença abaixo de 1%, o que confirma a integração. De 2022 em diante o microdado conta mais matrículas ativas. A causa foi medida em 2022: 214.815 matrículas de creche ativas em junho não têm data de fim, e contando **alunos distintos** em vez de linhas o microdado dá 340.085 (−2,5% em relação à planilha), contra 378.954 linhas (+8,6%). São vínculos encerrados (transferências, remanejamentos) publicados sem data de fim, que por isso parecem ativos. Em 2023 e 2024 a mesma correção não é possível porque o código do aluno também foi destruído. A consulta C5 usa a matrícula da própria planilha para a fração de demanda fora da rede e mostra a do microdado ao lado. 2021 fica fora porque não publicou datas.

## Integração com o Censo 2022 (IBGE)

O mesmo dado aparece com representações diferentes nas bases da SME e no IBGE. Em cada caso, o data warehouse define uma única representação.

| Dado | SME (microdado e fila) | IBGE (Agregados por Setores) | Representação no DW |
|---|---|---|---|
| Distrito | nome em maiúsculas, sem acento (`AGUA RASA`) | código de 9 dígitos no início do setor e nome com acento e caixa mista (`Água Rasa`) | nome normalizado pela mesma regra (`normalizacao.distrito`), chave natural de `dim_territorio`; o código e a grafia do IBGE ficam em `dim_setor_censitario` |
| Idade | idade simples em 31 de março do ano letivo | grupo de idade (0 a 4, 5 a 9, ...) na data do Censo | faixa do IBGE como atributo `faixa_ibge` de `dim_idade`, conformado com `dim_faixa_etaria` |
| Data | ano letivo e datas de matrícula | noite de 31/07 para 01/08/2022 | mês de julho de 2022 em `dim_tempo`, com a nota na `observacao`; a consulta C7 conta as matrículas ativas em 31/07/2022 |
| Território abaixo do distrito | `CD_SETOR` da SME: setor administrativo de 4 dígitos | `CD_SETOR` do IBGE: setor censitário de 15 dígitos | atributos com nomes distintos (`setor_sme` em Escola, `cd_setor` em Setor Censitário), nunca cruzados |

Duas regras de integração merecem destaque:

- **Ligação setor-distrito.** O nome do distrito vem do tema Básico; se um setor do tema Demografia não aparecer no Básico, herda o nome mais comum entre os setores do mesmo código de distrito. Setor cujo distrito não existe na SME aponta para o membro NAO INFORMADO de `dim_territorio`, e a verificação Q12 mostra quantos são.
- **Faixa comparável.** A creche atende de 0 a 3 anos e a pré-escola de 4 e 5, mas o IBGE agrupa 0 a 4. A comparação entre matrícula e população é feita na faixa 0 a 4, agregando a matrícula pela `faixa_ibge` da idade do aluno, e não pela etapa.

Valor não numérico numa variável do IBGE vira nulo e é contado; se a maior parte dos valores de um arquivo não for número, a leitura para, porque isso indica um layout diferente do documentado.

## Problemas da planilha de fila

| Problema | Evidência | Tratamento |
|---|---|---|
| Sete formatos entre 2006 e 2026 | 30 arquivos no formato A, 5 no B, 3 no E, 1 em C, D e F; série histórica H | parser lê o cabeçalho de duas linhas e identifica cada coluna, sem posição fixa |
| Significado de (1), (2), (3) muda com o formato | quatro definições diferentes nos rodapés | significado lido das notas de rodapé de cada arquivo; coluna numerada sem nota ou nota desconhecida interrompe a leitura |
| Nota (1) ausente em dez/2024 | rodapé só com (2) e (3) | herda do formato A porque as notas presentes coincidem com ele; fica registrado como observação |
| Fim de linha só com retorno de carro | 4.512 `\r` e nenhum `\n` na série histórica | normalização do fim de linha na leitura |
| Número com e sem ponto de milhar | `1.188` em quase todos, `337022` em set/2019 | conversão aceita os dois |
| Quebra da fila não publicada em parte da série | sem opção x com opção só a partir de set/2019; prazo de 30 dias só a partir de set/2020 | medida nula (não publicada), nunca zero |
| Colunas soltas sem cabeçalho de etapa | `mat` e `mat pr` em set/2020 | ignoradas e listadas |
| Soma dos distritos diferente da linha TOTAL | 2 arquivos (jun/2020 e jun/2023) | valor por distrito mantido; alerta Q05 |
| Total diferente da soma das categorias | 24 distrito-etapa no recorte, de 1 a 4 crianças | total publicado prevalece; alerta Q06 |
| Colunas fora do dicionário | `DEM_PREF_CRECHE`, `DEM_PREF_PRE` na série histórica | não carregadas, por falta de definição |

## Problemas do microdado

| Problema | Evidência | Tratamento |
|---|---|---|
| Código da escola corrompido | 2022: embaralhado, mas um para um; 2023: 182 códigos para 3.858 escolas; 2024: 193 para 4.011, em notação científica | qualidade do código medida por ano no próprio dado; código real recuperado por nome, tipo e distrito contra o último ano confiável |
| Recuperação do código | 98,6% das matrículas de 2022, 95,9% de 2023, 94,8% de 2024 ligadas ao código real | o restante recebe chave sintética estável (hash de nome, tipo e distrito) |
| Homônimos | 14 a 34 por ano com mesmo nome, tipo e distrito e códigos diferentes | nos anos ruins, homônimo nunca herda código: recebe chave sintética |
| Escola que muda de nome mantendo o código | 379 de 9.598 códigos entre 2015 e 2021 | dimensão Escola tipo 2: 9.927 versões de 9.513 escolas |
| `CD_SETOR` é homônimo do setor censitário | 4 dígitos, setor administrativo da SME; o censitário do IBGE tem 15 | atributo `setor_sme`, nunca cruzado com dado do IBGE; nulo nos anos de código corrompido |
| Turno sem descrição em 2021 | 100% das linhas; código com numeração própria | código de 2021 = código de 2020 + 3, conferido pelo horário das turmas (9 = 7h às 17h, integral) |
| Turno ausente em parte de 2022 | 19.954 linhas | deduzido do horário de início e fim |
| Tarde e Vespertino | duas categorias publicadas | mantidas como turnos distintos; a jornada (`PARCIAL DIURNO`) as agrupa |
| Idade com vírgula decimal | 2020 inteiro (`5,00`) | conversão aceita vírgula com parte decimal zero |
| Idade ausente | 2021 e 2022 com centenas de milhares de nulos | calculada pelo ano e mês de nascimento |
| Mês de nascimento impossível | 2022, valores como 18 e 26 | idade estimada só pelo ano, com erro de no máximo um ano; marcada em `idade_estimada` |
| Ano de nascimento 1900 | idades de 115 a 124 anos | tratado como não informado |
| Datas em cinco formatos | ISO, `D/M/AAAA H:M:S`, `DD/MM/AAAA HH:MM`, serial do Excel em metade de 2024 | leitura de todos os formatos; datas fora de um ano antes ou depois do ano letivo descartadas |
| Datas ausentes em 2021 | 100% das linhas | membro "não informada" da dimensão Data |
| Código de matrícula destruído | 2023: 100 valores distintos em 1,16 milhão de linhas | `cd_matricula_origem` nulo nos anos de código corrompido; `id_turma` construído |
| `TURMA_ESCOL` com o nome da turma | 2023 | filtro de escolarização pelo tipo do arquivo quando a coluna não é S/N |
| Indicadores com valor `2` | 5 linhas em dez anos | tratado como não informado |
| Indicadores com vírgula | `0,00` e `1,00` em 2020 | lidos como 0 e 1 |
| Desfecho conflitante | 8.491 matrículas aprovadas e reprovadas ao mesmo tempo | resumo exclusivo com prioridade explícita: falecido, transferido, abandono, reprovado, aprovado, concluído, outra saída, em curso |
| Retrato publicado antes do fim do ano | 41% das matrículas de 2020 e 50% das de 2023 ainda em curso no arquivo | registrado na observação do ano letivo; taxas de rendimento de 2020 e 2023 não são comparáveis com os demais anos |
| Raça e cor com grafias diferentes | `NAO DECLARADA`, `NÃO DECLARADA`, `RECUSOU INFORMA` | normalizadas |
| DRE e tipo de escola com grafias diferentes | DRE com e sem prefixo, `PIRITUBA` x `PIRITUBA/JARAGUA`, `CCI/CIPS` x `CCI-CIPS` | normalizadas por regra testada |

## Sinônimos e homônimos

O artigo da disciplina cita os dois problemas como o centro do trabalho de integração. Os casos deste DW:

| Tipo | Caso | Decisão |
|---|---|---|
| Sinônimo | `AGUA RASA ` (fila) e `AGUA RASA` (microdado) | mesma entidade após normalização |
| Sinônimo | `PIRITUBA` e `PIRITUBA/JARAGUA` | mesma DRE |
| Sinônimo | `idade_aluno_31_03`, `IDADE_ALUNO_3103`, `IDADE_ALUNO_MAR` | mesma coluna canônica |
| Sinônimo operacional | Tarde e Vespertino | mantidos distintos no turno, iguais na jornada |
| Homônimo | `CD_SETOR` da SME e setor censitário do IBGE | atributos distintos, com nomes distintos |
| Homônimo | escolas de mesmo nome, tipo e distrito | identidades distintas; nunca recebem o mesmo código recuperado |
| Homônimo | código de 2023-2024 compartilhado por centenas de escolas | código descartado como identificador naqueles anos |

## Verificações automáticas

| Código | Verificação | Situação esperada |
|---|---|---|
| Q01 | Integridade referencial das 18 chaves estrangeiras | OK (falha impede o uso) |
| Q02 | Versões da dimensão Escola sem sobreposição e com uma versão atual | OK |
| Q03 | Soma do fato de desfecho igual à do fato de matrícula | OK |
| Q04 | Cada mês de fila com 96 distritos e 8 etapas | OK |
| Q05 | Soma dos distritos contra a linha TOTAL | ALERTA (defeito da fonte) |
| Q06 | Total da fila contra a soma das categorias | ALERTA (defeito da fonte) |
| Q07 | Reconciliação das duas bases em junho | ALERTA para 2022-2024 |
| Q08 | Fração de matrículas em escola com chave sintética | OK (máximo 5,2%, em 2024) |
| Q09 | Fração de matrículas em membros "não informado" | OK |
| Q10 | Anos letivos com limitação registrada | ALERTA (2020 a 2024) |
| Q11 | Fato de turma conserva as matrículas e tem uma linha por turma; fração de matrículas em turma sem nome | OK (FALHA se não conservar) |
| Q12 | População carregada, setores sem distrito correspondente na SME, valores não publicados | ALERTA enquanto a população não for carregada |
| Q13 | Cada hierarquia `A ≤ B` vale como dependência funcional (todo membro de A pertence a um único B) | OK (FALHA se não valer) |
| Q14 | Conformidade: os rollups encolhidos têm os mesmos valores das dimensões de que derivam | OK (FALHA se não valer; ALERTA para distrito do IBGE sem correspondente) |

Q01 passa a conferir 27 chaves estrangeiras (18 dos três fatos originais, 5 do fato de turma e 4 do fato de população). `dw-sme verificar` sai com código 1 se qualquer verificação ficar em FALHA.
