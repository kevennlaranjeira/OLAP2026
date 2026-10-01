# Consultas

Seis consultas cobrem as operações exigidas pelo enunciado. Cada uma está num arquivo em [`src/dw_sme/sql/consultas/`](../src/dw_sme/sql/consultas/), com um cabeçalho que traz código, tipo, pergunta, justificativa e fatos usados. `dw-sme consultar` roda todas e grava um CSV por consulta em `data/relatorios/consultas/`.

| Consulta | Operação | Fatos | Linhas no resultado real |
|---|---|---|---|
| C1 | drill-down | fila | 110 |
| C2 | roll-up | matrícula | 151 |
| C3 | slice and dice | matrícula | 6 |
| C4 | pivot | matrícula | 13 |
| C5 | drill-across | fila, matrícula | 1.920 |
| C6 | drill-across | fila, matrícula, desfecho | 131 |

Os números abaixo vêm da carga com os dados reais de 2015 a 2024.

## C1 · Drill-down: fila de creche da DRE ao distrito

**Pergunta.** No último mês publicado, quantas crianças esperavam vaga em creche no município, em cada DRE e, dentro de cada DRE, em cada distrito?

**Como.** `GROUP BY ROLLUP (dre, distrito)` sobre `fato_fila`, com etapa fixada em creche e um único mês (a fila é estoque). A linha do município é a soma das DREs, que é a soma dos distritos.

**Por quê.** A DRE administra a rede; o distrito é a menor unidade em que a fila é publicada. A hierarquia distrito ≤ DRE não existe na planilha de fila: vem da integração com o microdado.

**Resultado (dezembro de 2024).** 528 crianças no município. A DRE Ipiranga concentra a maior fila (103), puxada pelos distritos Saúde (22), São Lucas (17) e Cursino (16).

## C2 · Roll-up: matrículas da etapa ao nível

**Pergunta.** Quantas matrículas a rede teve em cada ano, por etapa, subindo para nível de ensino e total?

**Como.** `GROUP BY ano, ROLLUP (nivel, etapa)` sobre `fato_matricula`.

**Resultado.**

| Etapa | 2015 | 2019 | 2024 |
|---|---|---|---|
| Creche | 320.691 | 459.093 | 474.472 |
| Pré-escola | 249.747 | 300.942 | 331.147 |
| Fundamental, anos iniciais | 297.110 | 277.140 | 316.946 |
| Fundamental, anos finais | 214.502 | 236.754 | 230.829 |
| EJA, anos finais | 109.751 | 93.459 | 44.442 |
| Total do ano | 1.235.613 | 1.408.911 | 1.424.039 |

A creche cresceu 48% em dez anos; a EJA dos anos finais caiu para 40% do que era. Os totais de 2020 e 2023 são menores; nesses dois anos o arquivo publicado é um retrato anterior ao fim do ano letivo (ver a dimensão Ano Letivo), o que pode explicar parte da diferença.

## C3 · Slice and dice: creche por rede e jornada

**Pergunta.** Na creche, quanto da oferta é da rede direta e quanto da conveniada, e em que jornada, em 2019 e no ano mais recente?

**Como.** Slice em etapa = creche; dice em rede (direta, conveniada) e ano (2019 e o último); cruzamento rede × jornada.

**Resultado.**

| Ano | Rede | Jornada | Matrículas | Participação |
|---|---|---|---|---|
| 2019 | conveniada | integral | 388.750 | 84,7% |
| 2019 | direta | integral | 68.857 | 15,0% |
| 2019 | direta | parcial diurno | 1.389 | 0,3% |
| 2024 | conveniada | integral | 401.524 | 84,6% |
| 2024 | direta | integral | 72.690 | 15,3% |
| 2024 | direta | parcial diurno | 172 | 0,04% |

A creche paulistana é 85% conveniada e praticamente toda integral, com proporções estáveis entre 2019 e 2024.

## C4 · Pivot: jornada nas colunas, DRE nas linhas

**Pergunta.** No ano mais recente, como as matrículas de cada DRE se dividem entre jornada integral, parcial diurna e noturna?

**Como.** `PIVOT ... ON jornada USING sum(qtd_matricula) GROUP BY dre`.

**Resultado (2024).** A fração em jornada integral vai de 35,5% (São Mateus) a 47,2% (Ipiranga). Todas as DREs têm mais matrículas em jornada parcial diurna que em integral; em Ipiranga a diferença é mínima (47.979 contra 47.620).

## C5 · Drill-across: fila contra matrículas em junho

**Pergunta.** Em cada distrito e ano, quantas crianças esperavam vaga em creche e pré-escola em junho, quantas estavam matriculadas, e qual fração da demanda ficou fora?

**Como.** `fato_fila` agregado em junho por distrito e etapa; `fato_matricula` agregado no mesmo grão, contando as matrículas ativas no fim de junho pelos dois papéis da dimensão Data. União pelas dimensões conformadas (Território; Etapa como rollup de Série; Tempo como rollup de Data), com `FULL OUTER JOIN` para preservar distritos que só aparecem num dos lados. A fração fora usa a matrícula da própria planilha; a do microdado fica ao lado, com a divergência explícita.

**Resultado no município (creche).**

| Ano | Fila em junho | Matrículas (planilha) | Fração fora | Matrículas ativas (microdado) |
|---|---|---|---|---|
| 2015 | 124.741 | 240.840 | 34,1% | 240.905 |
| 2017 | 104.268 | 288.294 | 26,6% | 288.366 |
| 2019 | 48.910 | 333.876 | 12,8% | 334.443 |
| 2020 | 22.732 | 341.966 | 6,2% | 338.927 |
| 2021 | 8.767 | 360.946 | 2,4% | (sem datas) |
| 2022 | 4.761 | 348.975 | 1,3% | 378.954 |
| 2024 | 3.633 | 332.464 | 1,1% | 351.906 |

A fila de creche caiu 97% em dez anos e a pré-escola zerou a fila em 2018. No nível de distrito, em 2019 a maior fração fora estava na Sé (46%), em Marsilac (31%) e no Itaim Bibi (27%); em 2024, no Brás (11%).

## C6 · Drill-across: fila de creche e abandono no fundamental por DRE

**Pergunta.** As DREs com mais crianças esperando creche em junho são as mesmas em que mais alunos abandonam o fundamental?

**Como.** Três fatos agregados até DRE e ano: fila de creche em junho (`fato_fila`, subindo de distrito para DRE pela hierarquia integrada), matrículas de creche (`fato_matricula`, para pôr a fila em escala) e desfecho do fundamental (`fato_desfecho`). A taxa de abandono é recalculada pelas contagens e restrita ao fundamental, porque na educação infantil não há aprovação.

**Resultado.** Em 2019, Santo Amaro tinha a maior fila relativa (173 crianças por mil matrículas de creche) e taxa de abandono no fundamental de 1,3%; Freguesia/Brasilândia e Ipiranga tinham as maiores taxas de abandono (2,0%) com filas relativas menores (87 e 67 por mil). A correlação entre as duas medidas nas 13 DREs muda de sinal de um ano para outro (de −0,27 a 0,56). O cruzamento não sustenta a hipótese de que as duas vulnerabilidades andam juntas no nível de DRE.
