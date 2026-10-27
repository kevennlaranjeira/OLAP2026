# Decisões de projeto

Anotamos cada decisão com o contexto, a alternativa que descartamos e o argumento. D19 a D23 vieram quando incluímos o fato de turma e a população do Censo 2022. As que dependem de medição citam o número que medimos.

## D01. Tema: oferta, fila e desfecho na rede municipal de São Paulo

**Contexto.** A primeira ideia era dimensionar a oferta escolar por setor censitário em São Carlos. A verificação das bases mostrou dois problemas: o Censo Escolar não traz o endereço do aluno (só o da escola), e o IBGE publica população por setor em grupos de cinco anos, que não recortam nas idades da educação básica. Sem dado de vaga nem de fila, a demanda teria de ser estimada.

**Decisão.** Mudar para a rede municipal de São Paulo, cuja Secretaria publica a fila por vaga por distrito.

**Argumento.** A demanda não atendida deixa de ser estimativa e passa a ser medida. O volume (13,4 milhões de matrículas em dez anos) atende ao "dados reais e volumosos" do enunciado.

## D02. Duas bases da SME como núcleo, o Censo 2022 como terceira

**Decisão.** Microdados de Matrículas e Demanda Registrada e Matrículas, ambas da SME-SP, sustentam matrícula, fila, desfecho e ocupação. O Censo 2022 do IBGE entra como terceira fonte, para a população em idade escolar, como registramos na nossa planilha.

**Alternativa descartada.** Trocar a fila pelo Censo, para ter instituições diferentes nas duas fontes obrigatórias.

**Argumento.** O enunciado permite fontes da mesma plataforma, e a fila é o diferencial do tema. As duas bases da SME têm grão, formato e vocabulário diferentes, e a reconciliação entre elas (diferença abaixo de 1% de 2015 a 2020) é evidência de integração real. O Censo não substitui a fila, porque mede outra coisa (quantas crianças existem, não quantas pediram vaga); ele a complementa, e por isso entra como fonte adicional e não no lugar de uma delas.

## D03. DuckDB como banco

**Alternativas.** PostgreSQL (instalado na máquina), ou os dois.

**Argumento.** Arquivo único, sem servidor e sem senha: qualquer um de nós roda o projeto só com Python. Tem `ROLLUP`, `CUBE`, `GROUPING SETS` e `PIVOT` nativos. Carrega os 13,4 milhões de linhas em cerca de 3 minutos num notebook.

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

**Medição.** Com as 11 restrições, o banco ocupava 2,08 GB e a carga levava 342 s; sem elas, 289 MB e 189 s, com o mesmo resultado em todas as verificações existentes na época da medição.

**Argumento.** É prática comum em data warehouse desligar a restrição nos fatos grandes e garantir a integridade pela carga. Aqui toda chave vem de junção interna com a dimensão, e a verificação Q01 confere as 27 chaves estrangeiras dos cinco fatos depois de cada carga. Os fatos pequenos mantêm as restrições declaradas.

## D17. Staging em arquivo separado

**Medição.** Com o staging no mesmo arquivo, o banco chegava a 2,85 GB mesmo depois de apagar o staging.

**Argumento.** O DuckDB não devolve ao disco o espaço de tabela apagada. Anexar um arquivo de staging e apagá-lo no fim deixa no banco final só dimensões e fatos.

## D18. Atividades complementares fora do fato de matrícula

**Argumento.** Não são vagas de escolarização, e a planilha de fila só conta escolarização. Misturar inflaria a oferta e quebraria a reconciliação.

## D19. Ocupação medida, capacidade não inventada

**Contexto.** Nossa planilha registra "capacidade e ocupação das turmas". Nenhuma das fontes publica o número de vagas de cada turma.

**Decisão.** Fato de turma com a ocupação efetiva: alunos ativos em 30/06 e turmas com ao menos um aluno ativo. A média de alunos por turma é derivada e não aditiva. A matrícula em processo da planilha de fila (vaga oferecida aguardando documentação) é a informação publicada mais próxima de capacidade ociosa e fica no fato de fila.

**Alternativa descartada.** Estimar a capacidade por um limite normativo de alunos por turma.

**Argumento.** O limite seria um número externo às fontes, aplicado igualmente a turmas que podem ter salas e condições diferentes. A ocupação é medida no dado; a capacidade ficaria estimada, e o enunciado pede dados reais.

## D20. Fato de turma agregado do fato de matrícula

**Alternativas.** Contar alunos por turma em cada consulta, a partir do fato de matrícula.

**Argumento.** A ocupação é uma propriedade da turma, com grão próprio. Guardar o agregado deixa a consulta simples e permite a verificação de conservação (Q11): a soma das matrículas do fato de turma é igual à do fato de matrícula. É o mesmo raciocínio do fato de desfecho.

## D21. População no grão de setor censitário

**Alternativa descartada.** Agregar para distrito já na carga.

**Argumento.** É o grão em que o IBGE publica. Guardar o setor não custa nada às consultas por distrito (a hierarquia `setor ≤ distrito` faz o roll-up) e preserva a informação de onde, dentro do distrito, as crianças moram, que é o que o gestor precisa para escolher o lugar de uma unidade nova.

## D22. Faixa de 0 a 4 anos e data de 31/07/2022 na comparação com a população

**Argumento.** O IBGE só publica grupos de idade por setor; o grupo que contém a creche é 0 a 4. A matrícula é agregada pela mesma faixa (`faixa_ibge` da idade do aluno), não pela etapa. A população é um retrato na noite de 31/07 para 01/08/2022, então a matrícula comparável é a ativa em 31/07/2022, pelos dois papéis da dimensão Data. A fila entra pelo último mês publicado até o Censo (junho de 2022, no calendário trimestral daquele ano).

## D23. Censo 2022 como fonte complementar e opcional

**Argumento.** O IBGE publica num servidor de arquivos, sem API, e a estrutura do diretório pode mudar. Se o download falhar, o pipeline segue sem a população, avisa onde colocar os arquivos e a verificação Q12 fica em ALERTA. Os fatos da SME não dependem do IBGE. A leitura procura as colunas pelo nome e recusa o arquivo se o layout não for o documentado, para que uma mudança no arquivo não vire número com sentido errado; a recusa vale só para a população, e o motivo fica no resumo da carga.
