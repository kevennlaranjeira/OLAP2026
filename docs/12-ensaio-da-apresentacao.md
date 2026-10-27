# Ensaio da apresentação

A apresentação é no dia 29 de outubro e deve durar 20 minutos: quatro blocos de 5 minutos, um por integrante. Este documento serve para alinhar o grupo antes do dia: a ideia do trabalho em um minuto, como conduzir a reunião de ensaio, o que dizer em cada slide e as perguntas que a professora pode fazer. A divisão dos blocos e o que ainda falta para a entrega estão em [08 Pendências da entrega](08-pendencias-da-entrega.md).

## A ideia em um minuto

A prefeitura de São Paulo publica quem espera vaga na educação infantil, por distrito, e cada matrícula da rede municipal. Separadas, essas bases não dizem onde abrir vagas. O data warehouse junta fila, matrícula, ocupação das turmas, desfecho da matrícula e a população do Censo 2022 numa constelação de cinco fatos e catorze dimensões, e responde perguntas de gestor com oito consultas OLAP sobre os dados reais de 2015 a 2024.

| Número | O que mostra |
|---|---|
| -97% | fila de creche em junho, de 124.741 crianças (2015) para 3.633 (2024) |
| 85% | da creche é rede conveniada, quase toda em jornada integral |
| 86 por 100 | matrículas por 100 crianças de 0 a 4 anos; 25 distritos abaixo de 50 e 25 acima de 100 |
| 13,4 milhões | matrículas carregadas, com 551 mil turmas e 26.889 setores censitários |

Uma frase para abrir a conversa: o modelo diz onde falta vaga, se a vaga que existe está cheia e quantas crianças moram em cada lugar.

## Reunião de ensaio

Uns 40 minutos, com todos de computador aberto na [versão em HTML](apresentacao/apresentacao-projeto1.html).

| Tempo | O que fazer |
|---|---|
| 5 min | Contar a ideia em um minuto e mostrar os slides 3 a 6, que dão o problema e os cinco assuntos. |
| 10 min | Mostrar o projeto funcionando: rodar os testes, abrir o relatório e um CSV de consulta. |
| 15 min | Cada integrante percorre o próprio bloco com as notas abertas (tecla N) e diz em voz alta a mensagem de cada slide. |
| 10 min | Ensaio corrido, cronometrando 5 minutos por pessoa, e uma rodada das perguntas prováveis. |

No fim dos slides 6, 11 e 16, quem está falando passa a palavra.

## A mensagem de cada slide

| Slide | Título | Diga isto |
|---|---|---|
| 1 | Capa | Grupo, disciplina e a pergunta do trabalho: onde falta vaga e onde a oferta já está cheia. |
| 2 | Roteiro | Quatro integrantes, quatro blocos, na ordem do enunciado. |
| 3 | O problema | A fila de creche em junho caiu de 124.741 para 3.633, mas o gestor ainda precisa cruzar bases diferentes. |
| 4 | Perguntas do gestor | Quatro decisões de política pública, cada uma ligada às consultas que a respondem. |
| 5 | Por que São Paulo | Fila e matrícula publicadas em dado aberto; o modelo vale para São Carlos assim que a fila for publicada. |
| 6 | Cinco assuntos | Quatro viram tabelas de fatos, a oferta por setor sai das dimensões e o desfecho é o quinto processo. |
| 7 | Três fontes | 13,4 milhões de matrículas, 44 meses de fila e 26.889 setores do Censo 2022. |
| 8 | Integração | O mesmo dado em formas diferentes; a reconciliação entre as bases da SME fica abaixo de 1%. |
| 9 | Problemas nos dados | Código da escola recuperado em 94,8% a 98,6% das matrículas; medida não publicada fica nula, nunca zero. |
| 10 | Grão e aditividade | Fila e população são estoques: somam no território, não no tempo; taxas saem sempre das somas. |
| 11 | Estrela Matrícula | Data com dois papéis, campo artificial igual a 1, três bugigangas, duas degeneradas e Escola tipo 2. |
| 12 | Estrela Fila | Distrito × mês × etapa; estoque com duas hierarquias de tempo. |
| 13 | Estrela Desfecho | Agregado da matrícula; taxas recalculadas pelas contagens, nunca média de taxas. |
| 14 | Estrela Ocupação de Turma | Ninguém publica a capacidade, então medimos a ocupação: soma de alunos dividida por soma de turmas. |
| 15 | Estrela População | Setor censitário, 11,4 milhões de moradores; Faixa Etária é o rollup encolhido de Idade. |
| 16 | Constelação | Cinco fatos, catorze dimensões, Território nos cinco, rollups encolhidos tracejados. |
| 17 | Oito consultas | Três roll-up ou drill-down, uma slice and dice, uma pivot e três drill-across, cada uma com o resultado real. |
| 18 | Fila e oferta | Queda de 97% na fila; fração fora da rede de 34% para 1%; 85% da creche conveniada. |
| 19 | População e ocupação | 86 matrículas por 100 crianças, com distritos muito longe da média; creche com cerca de 11 por turma. |
| 20 | Decisões | Destacar as duas mais perguntadas: rollups encolhidos e nulo não é zero. |
| 21 | Encerramento | Relatório, repositório e carga real sem nenhuma FALHA; abrir para perguntas. |

## Perguntas prováveis

Durante a apresentação há perguntas sobre o trabalho. Entre parênteses, quem responde primeiro. As decisões completas, com a alternativa descartada, estão em [06 Decisões](06-decisoes.md).

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
- Combinar quem controla os slides e o sinal de passagem de bloco no fim dos slides 6, 11 e 16.
- Cada integrante sabe responder as perguntas do próprio bloco.
- Entregar o PDF do relatório no local definido no critério de avaliação da disciplina.
