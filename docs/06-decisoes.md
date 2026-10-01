# Decisões de projeto

Cada decisão traz o contexto, a alternativa descartada e o argumento. As que dependem de medição citam o número.

## D01. Tema: oferta, fila e desfecho na rede municipal de São Paulo

**Contexto.** A primeira ideia era dimensionar a oferta escolar por setor censitário em São Carlos. A verificação das bases mostrou dois problemas: o Censo Escolar não traz o endereço do aluno (só o da escola), e o IBGE publica população por setor em grupos de cinco anos, que não recortam nas idades da educação básica. Sem dado de vaga nem de fila, a demanda teria de ser estimada.

**Decisão.** Mudar para a rede municipal de São Paulo, cuja Secretaria publica a fila por vaga por distrito.

**Argumento.** A demanda não atendida deixa de ser estimativa e passa a ser medida. O volume (13,4 milhões de matrículas em dez anos) atende ao "dados reais e volumosos" do enunciado.

## D02. Duas bases da mesma plataforma

**Decisão.** Microdados de Matrículas e Demanda Registrada e Matrículas, ambas da SME-SP.

**Alternativa descartada.** Trocar a segunda pelo Censo 2022 do IBGE, para ter instituições diferentes.

**Argumento.** O enunciado permite fontes da mesma plataforma, e a fila é o diferencial do tema. As duas bases têm grão, formato e vocabulário diferentes, e a reconciliação entre elas (diferença abaixo de 1% de 2015 a 2020) é evidência de integração real.

## D03. DuckDB como banco

**Alternativas.** PostgreSQL (instalado na máquina), ou os dois.

**Argumento.** Arquivo único, sem servidor e sem senha: qualquer integrante do grupo roda o projeto só com Python. Tem `ROLLUP`, `CUBE`, `GROUPING SETS` e `PIVOT` nativos. Carrega os 13,4 milhões de linhas em cerca de 3 minutos num notebook.

## D04. Grão do fato de matrícula: vínculo aluno-turma

**Alternativas.** Turma, ou escola por etapa e turno.

**Argumento.** É o grão mais fino publicado. Mantém o perfil do aluno (sexo, raça e cor, idade, deficiência) e o desfecho individual, que se perdem em qualquer agregação. Os fatos agregados (desfecho) saem dele.

## D05. Recorte 2015-2024

**Argumento.** Dez anos cobrem antes e depois da pandemia e os dois regimes de publicação da fila (trimestral e bimestral). 2025 existe no portal mas não estava no recorte combinado; o recorte é parâmetro (`--anos`).

## D06. Texto bruto preservado até a carga

**Alternativa descartada.** Converter tipos na leitura do CSV.

**Argumento.** Os defeitos da fonte (código em notação científica, vírgula decimal, serial do Excel) só são detectáveis no texto original. Toda conversão acontece depois, com regra explícita e testada.

## D07. Regras em Python sobre valores distintos, execução em SQL

**Argumento.** As colunas categóricas têm poucos valores distintos (96 distritos, 148 séries, ~39 mil escolas-ano) e as regras são mais legíveis e testáveis em Python. Aplicá-las aos valores distintos e juntar o resultado em SQL evita processar 13 milhões de linhas em Python. Onde a regra é linha a linha (idade, datas, desfecho), ela existe também em SQL, com teste de equivalência.

## D08. Parser da fila guiado por cabeçalho e rodapé

**Alternativa descartada.** Um mapeamento fixo de colunas por formato.

**Argumento.** São sete formatos e o significado das colunas numeradas muda entre eles. Ler o cabeçalho e as notas de rodapé faz o parser se adaptar a um formato novo; nota desconhecida interrompe a leitura em vez de gravar número com sentido errado.

## D09. Nulo para medida não publicada

**Argumento.** A quebra da fila por tempo de espera só existe a partir de setembro de 2020. Gravar zero antes disso faria parecer que a fila com mais de 30 dias desapareceu. Nulo diz "não publicado".

## D10. Identidade da escola: qualidade do código medida no dado, recuperação por nome

**Alternativa descartada.** Lista fixa de anos ruins, ou usar só nome da escola como chave em todos os anos.

**Argumento.** O nome sozinho não identifica (14 a 34 homônimos por ano). O código é confiável até 2021 e recuperável depois casando nome, tipo e distrito com o último ano confiável: 94,8% a 98,6% das matrículas de 2022-2024 ficam ligadas ao código real. A classificação do código por ano sai de duas métricas do próprio dado (notação científica e colisão), então um ano futuro corrompido é detectado sem mudar código.

## D11. Dimensão Escola tipo 2

**Argumento.** 402 escolas mudam de nome, tipo, distrito ou DRE ao longo da série. Com tipo 1, uma matrícula de 2017 apareceria com o nome que a escola tem em 2024. Mudança só de grafia (DRE com e sem prefixo) não abre versão, porque a comparação é feita depois da normalização.

## D12. Rollups encolhidos para conformar grãos diferentes

**Argumento.** A fila é publicada por mês e etapa; a matrícula, por dia e série. Em vez de forçar um grão único, cada fato usa o seu, e as dimensões de grão mais alto (`dim_ano_letivo`, `dim_tempo`, `dim_etapa`) são subconjuntos conformados das de grão mais baixo. O *drill-across* agrega cada fato até o grão comum e une pelos atributos conformados.

## D13. Dimensão Data com dois papéis

**Argumento.** A fila é um retrato numa data. A medida comparável no microdado é "matrículas ativas naquela data", que exige início e fim da matrícula. Modelar as duas como papéis da mesma dimensão segue o exemplo do artigo da disciplina e evita duas dimensões de data idênticas.

## D14. Junho como mês de referência do *drill-across*

**Alternativa descartada.** Último mês publicado de cada ano.

**Argumento.** Em dezembro o ano letivo já terminou e quase nenhuma matrícula está ativa. Junho é publicado em todos os anos de 2015 a 2024 e cai no meio do ano letivo. Foi também o mês em que a reconciliação ficou abaixo de 1%.

## D15. Fração de demanda fora da rede pela matrícula da própria planilha

**Argumento.** De 2022 em diante o microdado superestima as matrículas ativas (vínculos encerrados sem data de fim). A planilha é a mesma fonte e a mesma data da fila. A matrícula do microdado aparece ao lado, com a divergência explícita.

## D16. Fato de matrícula sem restrição FOREIGN KEY declarada

**Medição.** Com as 11 restrições, o banco ocupava 2,08 GB e a carga levava 342 s; sem elas, 289 MB e 189 s, com o mesmo resultado nas 10 verificações.

**Argumento.** É prática comum em data warehouse desligar a restrição nos fatos grandes e garantir a integridade pela carga. Aqui toda chave vem de junção interna com a dimensão, e a verificação Q01 confere as 18 relações depois de cada carga. Os fatos pequenos mantêm as restrições declaradas.

## D17. Staging em arquivo separado

**Medição.** Com o staging no mesmo arquivo, o banco chegava a 2,85 GB mesmo depois de apagar o staging.

**Argumento.** O DuckDB não devolve ao disco o espaço de tabela apagada. Anexar um arquivo de staging e apagá-lo no fim deixa no banco final só dimensões e fatos.

## D18. Atividades complementares fora do fato de matrícula

**Argumento.** Não são vagas de escolarização, e a planilha de fila só conta escolarização. Misturar inflaria a oferta e quebraria a reconciliação.
