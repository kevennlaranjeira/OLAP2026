# Ensaio da apresentação

A apresentação é no dia 29 de outubro. A professora pediu 20 minutos; combinamos 7 minutos para o bloco 1, que abre a apresentação e vende a proposta, e 5 para cada um dos outros, 22 no total. Aqui juntamos o que precisamos alinhar antes do dia: a ideia do trabalho em um minuto, como conduzir a reunião de ensaio, o que dizer em cada slide e as perguntas que a professora pode fazer. A divisão dos blocos e o que ainda falta para a entrega estão em [08 Pendências da entrega](08-pendencias-da-entrega.md).

## A ideia em um minuto

A prefeitura de São Paulo publica quem espera vaga na educação infantil, por distrito, e cada matrícula da rede municipal. Separadas, essas bases não dizem onde abrir vagas. O data warehouse junta fila, matrícula, ocupação das turmas, desfecho da matrícula e a população do Censo 2022 numa constelação de cinco fatos e catorze dimensões, e responde perguntas de gestor com oito consultas OLAP sobre os dados reais de 2015 a 2024.

A apresentação vende isso como uma proposta. Começa pelos números: a fila de creche caiu 97% de 2015 a 2024, mas 3.633 crianças ainda esperavam, e a plateia ouve a pergunta "e se fosse o seu filho?". Depois vêm o problema (quase sete em cada dez esperam uma unidade específica, então falta vaga no lugar certo), os dados de hoje, que se repetem e não conversam, e o que o data warehouse melhora: consultas em 0,42 s, catorze verificações a cada carga e uma linguagem só. Cada bloco seguinte é um passo da proposta, e o fim volta à pergunta do começo.

| Número | O que mostra |
|---|---|
| -97% | fila de creche em junho, de 124.741 crianças (2015) para 3.633 (2024) |
| 2.502 de 3.633 | crianças da fila de creche de junho de 2024 que esperavam uma unidade específica; as outras 1.131 aceitavam qualquer unidade |
| 38.869 | matrículas de creche que, em junho de 2022, pareciam ativas no microdado sem ser: transferências sem data de fim |
| 0,42 s | tempo das oito consultas, somadas, sobre a carga real |
| 85% | da creche é rede conveniada, quase toda em jornada integral |
| 86 por 100 | matrículas por 100 crianças de 0 a 4 anos; 25 distritos abaixo de 50 e 25 acima de 100 |
| 13,4 milhões | matrículas carregadas, com 551 mil turmas e 26.889 setores censitários |

Uma frase para abrir a conversa: o modelo diz onde falta vaga, se a vaga que existe está cheia e quantas crianças moram em cada lugar.

## Reunião de ensaio

Uns 40 minutos, com todos de computador aberto na [versão em HTML](apresentacao/apresentacao-projeto1.html) ou no [PDF](apresentacao/apresentacao-projeto1.pdf), que abre no próprio GitHub.

| Tempo | O que fazer |
|---|---|
| 5 min | Contar a ideia em um minuto e mostrar os slides 2 a 11, da queda da fila aos passos da proposta. |
| 10 min | Mostrar o projeto funcionando: rodar os testes, abrir o relatório e um CSV de consulta. |
| 15 min | Cada integrante percorre o próprio bloco com as notas abertas (tecla N) e diz em voz alta a mensagem de cada slide. |
| 10 min | Ensaio corrido, cronometrando 7 minutos para o Kevenn e 5 para cada um dos outros, e uma rodada das perguntas prováveis. |

No fim dos slides 11, 16 e 21, quem está falando passa a palavra.

## A mensagem de cada slide

| Slide | Título | Diga isto |
|---|---|---|
| 1 | Capa | Abrir com a pergunta: quantas crianças esperavam vaga em creche em 2015? Foram 124.741. Depois, grupo e tema. |
| 2 | A queda da fila | Em dez anos, a fila de creche de junho caiu 97%, de 124.741 para 3.633, e a demanda fora da rede foi de 34% para 1%. |
| 3 | E se fosse o seu filho? | 3.633 crianças ainda esperavam em 2024, nos 96 distritos. Perguntar à plateia: seu filho fora da creche, o seu trabalho, a sua casa. |
| 4 | O problema | Quem aceita qualquer unidade não espera mais de 30 dias; 2.502 das 3.633 esperam uma unidade específica. A pergunta é onde abrir vaga. |
| 5 | Dados que se repetem | Matrícula em dobro (38.869 a mais em 2022), um código para muitas escolas, totais que não fecham e zero que não é zero. |
| 6 | Nossa solução | Hoje são três bases que não conversam; o data warehouse junta fila, matrícula, ocupação e população num lugar só. |
| 7 | Mais confiáveis e mais rápidas | 0,42 s para as oito consultas, 3,5 min de carga, 14 verificações sem FALHA, bases da SME com menos de 1% de diferença. |
| 8 | Do dado à vaga | Medir, localizar, decidir e acompanhar: um ciclo que procura vaga no lugar certo. |
| 9 | Por que São Paulo | Fila e matrícula publicadas em dado aberto; o modelo vale para São Carlos assim que a fila for publicada. |
| 10 | Cinco assuntos | Cada assunto responde a uma parte da decisão de onde abrir vagas; quatro viram tabelas de fatos. |
| 11 | Imagine | A prefeitura adota a proposta: o passo 1 é do Thiago, o passo 2 do Daniel e o passo 3 do Luís. Passar a palavra. |
| 12 | Três fontes, três perguntas | Passo 1: quem já tem vaga (13,4 milhões de matrículas), quem espera (44 meses de fila) e quantas crianças moram ali (26.889 setores). O Tremembé é o exemplo que segue até o slide 16. |
| 13 | Integração | Como chega, regra, resultado: TREMEMBE e Tremembé viram a mesma linha; idade exata vira faixa do IBGE; CD_SETOR é homônimo. Prova: 240.905 contra 240.840, abaixo de 1%. |
| 14 | Problemas nos dados | Tabela problema, como chegou, o que fizemos, por que importa. Metade do minuto no código da escola (9,20961E+15, recuperado em 94,8% a 98,6%); uma frase para cada uma das outras linhas. Nulo não é zero. |
| 15 | Grão e aditividade | Grão: uma linha da fila é Tremembé, jun/2024, creche, 153; a criança é uma das 153. Aditividade: soma distritos (153 + 88), não meses. |
| 16 | Estrela Matrícula | Cada recurso resolve um problema: duas datas dizem quem estava ativo em 30/06; campo = 1 vira soma; bugigangas, degeneradas e Escola tipo 2. Passar ao Daniel. |
| 17 | Estrela Fila | Passo 2: distrito × mês × etapa, com duas hierarquias de tempo. |
| 18 | Estrela Desfecho | O que vem depois do acesso; taxas recalculadas pelas contagens, nunca média de taxas. |
| 19 | Estrela Ocupação de Turma | Ninguém publica a capacidade, então medimos a ocupação; no Tremembé, 10,7 crianças por turma de creche em 2024. |
| 20 | Estrela População | Setores censitários somados por distrito; Faixa Etária é o rollup encolhido de Idade. |
| 21 | Constelação | Território está nos cinco fatos e liga fila, matrícula, ocupação, desfecho e população. Passar ao Luís. |
| 22 | Oito consultas | Passo 3: três roll-up ou drill-down, uma slice and dice, uma pivot e três drill-across, cada uma com o resultado real. |
| 23 | Fila e oferta | Queda de 97% na fila; fração fora da rede de 34% para 1%; 85% da creche conveniada. |
| 24 | População e ocupação | 86 matrículas por 100 crianças, com distritos muito longe da média; o Tremembé tem 71,6. |
| 25 | Decisões | Por que confiar nos números: rollups encolhidos e nulo não é zero. |
| 26 | Um exemplo | Pelo tamanho, a escolha seria o Grajaú; com as bases cruzadas, a próxima vaga vai para o Tremembé. |
| 27 | De volta à pergunta | Cenário hipotético: a prefeitura abre vagas onde a fila resiste e a família volta a trabalhar; o que a proposta entrega. |
| 28 | Encerramento | A proposta está pronta: relatório, repositório e carga real sem nenhuma FALHA. Abrir para perguntas. |

## Perguntas prováveis

Durante a apresentação há perguntas sobre o trabalho. Entre parênteses, quem responde primeiro. As decisões completas, com a alternativa descartada, estão em [06 Decisões](06-decisoes.md).

**O que é a fila com opção por unidade específica?** (Kevenn) É a criança cuja família escolheu esperar vaga numa unidade específica. A planilha da SME separa esse grupo de quem aceita qualquer unidade: em junho de 2024 eram 2.502 das 3.633 crianças na fila de creche, e nenhuma das que aceitavam qualquer unidade esperava havia mais de 30 dias. Por isso a pergunta é onde abrir vaga.

**De onde vêm as 38.869 matrículas a mais?** (Kevenn ou Thiago) Em junho de 2022, o microdado tinha 378.954 matrículas de creche ativas, mas 340.085 alunos distintos: transferências e remanejamentos saem sem data de fim e parecem ativos. Por isso a consulta 5 usa a matrícula da própria planilha da fila e mostra a do microdado ao lado, com a diferença à vista.

**Os 0,42 segundo valem para qualquer computador?** (Kevenn) Medimos no notebook do Kevenn, com o banco da carga real: as oito consultas somam 0,42 s (melhor de três execuções). Em outra máquina o valor muda, mas continua em fração de segundo para este volume.

**Por que o Tremembé?** (Luís) É um exemplo do que o cruzamento mostra: em junho de 2024 o Tremembé tinha a segunda maior fila de creche da cidade (153) e 71,6 matrículas por 100 crianças de 0 a 4 anos, abaixo da média de 86, enquanto o Grajaú, o distrito com mais crianças, tinha 88 na fila. A consulta 7 traz os 96 distritos.

**A prefeitura usa o data warehouse?** (Luís) Não. O fim da história é um cenário hipotético: mostra o que a prefeitura poderia decidir com ele. Os números do cenário saem da nossa carga com os dados reais.

**Por que São Paulo e não São Carlos?** (Kevenn) São Paulo publica o microdado de cada matrícula e a fila por distrito, então a demanda é medida e não estimada. O modelo vale para São Carlos: matrícula, turma e desfecho vêm do registro de qualquer sistema escolar, e o Censo 2022 tem a população por setor de todos os municípios.

**Qual é o grão do fato Matrícula e por quê?** (Thiago) Um vínculo aluno-turma em um ano letivo, o grão mais fino publicado. Ele preserva o perfil e o desfecho de cada aluno, que se perdem em qualquer agregação, e os fatos Desfecho e Ocupação de Turma saem dele.

**Matrícula é uma tabela de fatos sem fato?** (Thiago) Ela usa a técnica das tabelas sem fato, com a ocorrência contada por um campo artificial igual a 1, mas tem uma medida, os dias de matrícula. Dias negativos publicados pela SME ficam nulos.

**Por que rollups encolhidos e não um grão único?** (Daniel) A fila é publicada por mês e etapa; a matrícula, por dia e série. Cada fato fica no seu grão, e Tempo, Ano Letivo, Etapa, Faixa Etária e Território são subconjuntos conformados das dimensões de grão mais fino. O drill-across agrega cada fato até o grão comum e une pelos atributos conformados.

**Por que fila e população são semiaditivas?** (Daniel) São estoques numa data. Somam entre distritos e etapas, mas somar a fila de fevereiro com a de abril conta a mesma criança duas vezes; no tempo se escolhe um mês.

**Onde está a capacidade das turmas?** (Daniel) Nenhuma fonte publica vagas por turma. Medimos a ocupação: alunos ativos em 30 de junho por turma em funcionamento. Estimar a capacidade por um limite normativo seria inventar um número fora das fontes.

**Por que nulo e não zero?** (Luís) A quebra da fila por tempo de espera só existe a partir de setembro de 2020. Gravar zero antes disso faria a fila com mais de 30 dias desaparecer. Nulo quer dizer "não publicado".

**Por que junho nas comparações?** (Luís) Junho é publicado em todos os anos de 2015 a 2024 e cai no meio do ano letivo; em dezembro quase nenhuma matrícula está ativa. Foi também o mês em que a reconciliação entre as bases ficou abaixo de 1%.

**Como garantem a integridade sem FOREIGN KEY no fato Matrícula?** (Thiago ou Luís) Toda chave vem de junção interna com a dimensão na carga, e a verificação Q01 confere as 27 chaves estrangeiras dos cinco fatos depois de cada carga. Declarar as 11 restrições do fato grande levava o banco a cerca de 2 GB.

**Como um distrito passa de 100 matrículas por 100 crianças?** (Luís) A matrícula conta onde a escola fica e a população conta onde a criança mora. Escolas de alguns distritos recebem crianças dos vizinhos, como em Lajeado (169,7) e Cidade Tiradentes (157,3).

**A Consulta 6 deu resultado negativo. Ela vale?** (Luís) Vale. O drill-across mostra que a correlação entre fila de creche e abandono no fundamental, nas 13 DREs, muda de sinal de um ano para outro, de -0,27 a 0,56. A hipótese de que as duas andam juntas não se sustenta no nível de DRE.

**Como sabem que os números estão certos?** (qualquer um) Catorze verificações rodam depois de cada carga, sem nenhuma FALHA nos dados reais. A reconciliação entre as bases da SME fica abaixo de 1%, os testes automáticos passam e o projeto foi replicado do zero a partir do GitHub em 27/10, com as oito consultas idênticas.

## Como cada um testa

O passo a passo completo está no [Guia do grupo](11-guia-do-grupo.md): preparar o computador (parte 6), rodar os testes (parte 7) e rodar o pipeline com os dados reais (parte 8). Quem clonou o repositório antes de 22/10 precisa apagar a pasta e clonar de novo, porque o histórico mudou nesse dia.

Para a apresentação basta abrir [apresentacao-projeto1.html](apresentacao/apresentacao-projeto1.html) com dois cliques: setas ou espaço avançam, F põe em tela cheia e N mostra as notas. O relatório de entrega é [relatorio-projeto1.pdf](relatorio/relatorio-projeto1.pdf).

## Checklist do dia

- Abrir o HTML no computador da sala antes da aula e testar setas, F e N.
- Levar o `.pptx` e o PDF do relatório num pendrive, para o caso de não haver internet. Sem internet, o HTML abre com a fonte Arial e continua legível.
- Combinar quem controla os slides e o sinal de passagem de bloco no fim dos slides 11, 16 e 21.
- Cada integrante sabe responder as perguntas do próprio bloco.
- Entregar o PDF do relatório no local definido no critério de avaliação da disciplina.
