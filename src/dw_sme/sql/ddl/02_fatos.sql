-- =============================================================================
-- Tabelas de fatos. Constelação: as cinco compartilham dim_territorio, e se
-- conformam por rollup encolhido em tempo (dia x mês x ano letivo), em etapa
-- (etapa x série), em idade (faixa IBGE x idade) e em território (setor
-- censitário x distrito).
-- =============================================================================

-- Matrícula. Grão: um vínculo aluno-turma em um ano letivo (uma linha do microdado
-- de escolarização). O fato principal é a ocorrência do vínculo: qtd_matricula é um
-- campo artificial sempre igual a 1, que existe para somar e agrupar.
--
-- Sem restrição FOREIGN KEY declarada, por decisão de projeto: com 13,4 milhões de
-- linhas, os índices que o DuckDB cria para conferir as 11 chaves ocupavam ~1,6 GB
-- (o fato em si ocupa ~260 MB). A integridade é garantida pela carga, em que toda
-- chave vem de junção interna com a dimensão, e conferida depois pela verificação
-- Q01 (dw_sme.qualidade). Os demais fatos, pequenos, mantêm as restrições.
CREATE TABLE dw.fato_matricula (
    chave_ano_letivo     INTEGER  NOT NULL,
    chave_data_inicio    INTEGER  NOT NULL,   -- papel 1: início da matrícula
    chave_data_fim       INTEGER  NOT NULL,   -- papel 2: fim da matrícula
    chave_escola         INTEGER  NOT NULL,
    chave_territorio     INTEGER  NOT NULL,
    chave_serie          INTEGER  NOT NULL,
    chave_turno          INTEGER  NOT NULL,
    chave_idade          INTEGER  NOT NULL,
    chave_perfil_aluno   INTEGER  NOT NULL,
    chave_deficiencia    INTEGER  NOT NULL,
    chave_situacao       INTEGER  NOT NULL,
    id_turma             VARCHAR  NOT NULL,   -- dimensão degenerada (construída: ano, escola, turma, série, turno)
    cd_matricula_origem  VARCHAR,             -- dimensão degenerada (nula nos anos em que o código foi corrompido)
    qtd_matricula        SMALLINT NOT NULL,   -- aditivo; sempre 1
    qtd_dias_matricula   INTEGER              -- aditivo; nulo em 2021, que não publicou datas
);

-- Fila por vaga. Grão: distrito x mês de referência x etapa.
-- Todas as medidas são estoques na data de referência, portanto semiaditivas:
-- somam entre distritos e etapas, mas não ao longo do tempo.
-- Medida nula = não publicada naquele período (diferente de zero).
CREATE TABLE dw.fato_fila (
    chave_tempo                     INTEGER NOT NULL REFERENCES dw.dim_tempo (chave_tempo),
    chave_territorio                INTEGER NOT NULL REFERENCES dw.dim_territorio (chave_territorio),
    chave_etapa                     INTEGER NOT NULL REFERENCES dw.dim_etapa (chave_etapa),
    formato_planilha                VARCHAR NOT NULL,   -- dimensão degenerada: formato A-F ou H (série histórica)
    qtd_matriculas                  INTEGER,
    qtd_matriculas_em_processo      INTEGER,
    qtd_demanda_total               INTEGER,
    qtd_demanda_sem_opcao           INTEGER,
    qtd_demanda_sem_opcao_ate_30d   INTEGER,
    qtd_demanda_sem_opcao_mais_30d  INTEGER,
    qtd_demanda_com_opcao           INTEGER,
    PRIMARY KEY (chave_tempo, chave_territorio, chave_etapa)
);

-- Desfecho da matrícula. Grão: escola (versão) x ano letivo x série.
-- Fato agregado a partir do microdado. As contagens por desfecho são exclusivas
-- e somam qtd_matriculas; todas são aditivas. As taxas ficam na visão abaixo.
CREATE TABLE dw.fato_desfecho (
    chave_ano_letivo     INTEGER NOT NULL REFERENCES dw.dim_ano_letivo (chave_ano_letivo),
    chave_escola         INTEGER NOT NULL REFERENCES dw.dim_escola (chave_escola),
    chave_territorio     INTEGER NOT NULL REFERENCES dw.dim_territorio (chave_territorio),
    chave_serie          INTEGER NOT NULL REFERENCES dw.dim_serie (chave_serie),
    qtd_matriculas       INTEGER NOT NULL,
    qtd_aprovados        INTEGER NOT NULL,
    qtd_reprovados       INTEGER NOT NULL,
    qtd_abandonos        INTEGER NOT NULL,
    qtd_transferidos     INTEGER NOT NULL,
    qtd_concluintes      INTEGER NOT NULL,
    qtd_falecidos        INTEGER NOT NULL,
    qtd_outras_saidas    INTEGER NOT NULL,
    qtd_em_curso         INTEGER NOT NULL,
    qtd_sem_desfecho     INTEGER NOT NULL,
    PRIMARY KEY (chave_ano_letivo, chave_escola, chave_serie)
);

-- Fatos derivados não aditivos. Taxas são recalculadas a partir das contagens em
-- qualquer nível de agregação; média de taxas daria resultado errado.
-- Denominador: matrículas que chegaram a um desfecho de rendimento
-- (aprovado + reprovado + abandono), como no indicador de rendimento do INEP.
-- Na educação infantil não há aprovação nem reprovação: a saída antes do fim do
-- ano é desistência e fica em qtd_abandonos, mas a taxa de rendimento é nula.
CREATE VIEW dw.vw_desfecho_taxas AS
SELECT
    f.*,
    s.nivel,
    s.nivel <> 'EDUCACAO INFANTIL' AS aplica_rendimento,
    f.qtd_aprovados + f.qtd_reprovados + f.qtd_abandonos AS base_rendimento,
    CASE WHEN s.nivel <> 'EDUCACAO INFANTIL'
         THEN f.qtd_aprovados / NULLIF(f.qtd_aprovados + f.qtd_reprovados + f.qtd_abandonos, 0) END AS taxa_aprovacao,
    CASE WHEN s.nivel <> 'EDUCACAO INFANTIL'
         THEN f.qtd_reprovados / NULLIF(f.qtd_aprovados + f.qtd_reprovados + f.qtd_abandonos, 0) END AS taxa_reprovacao,
    CASE WHEN s.nivel <> 'EDUCACAO INFANTIL'
         THEN f.qtd_abandonos / NULLIF(f.qtd_aprovados + f.qtd_reprovados + f.qtd_abandonos, 0) END AS taxa_abandono
FROM dw.fato_desfecho f
JOIN dw.dim_serie s USING (chave_serie);

-- Ocupação de turma. Grão: uma turma em um ano letivo (id_turma do fato de matrícula).
-- Fato agregado a partir de fato_matricula. A capacidade (vagas por turma) não é
-- publicada por nenhuma das fontes; a ocupação é medida pelos alunos da turma.
--
-- Como o fato de matrícula, não declara FOREIGN KEY: as chaves vêm do próprio
-- fato de matrícula, e a verificação Q01 confere as cinco relações.
CREATE TABLE dw.fato_turma (
    chave_ano_letivo             INTEGER NOT NULL,
    chave_escola                 INTEGER NOT NULL,
    chave_territorio             INTEGER NOT NULL,
    chave_serie                  INTEGER NOT NULL,
    chave_turno                  INTEGER NOT NULL,
    id_turma                     VARCHAR NOT NULL,   -- dimensão degenerada (mesma de fato_matricula)
    qtd_turmas                   SMALLINT NOT NULL,  -- campo artificial = 1; aditivo
    qtd_matriculas               INTEGER NOT NULL,   -- vínculos aluno-turma no ano; aditivo
    qtd_matriculas_ativas_junho  INTEGER,            -- ativas em 30/06; aditivo; nulo sem datas publicadas
    qtd_turmas_ativas_junho      SMALLINT            -- 1 se havia aluno ativo em 30/06; aditivo; nulo sem datas
);

-- Fato derivado não aditivo: média de alunos por turma em funcionamento em 30/06,
-- sempre recalculada como soma de alunos ativos dividida pela soma de turmas ativas.
CREATE VIEW dw.vw_ocupacao_turma AS
SELECT
    f.*,
    f.qtd_matriculas_ativas_junho / NULLIF(f.qtd_turmas_ativas_junho, 0) AS alunos_por_turma_junho
FROM dw.fato_turma f;

-- População residente. Grão: setor censitário x faixa etária x data de referência
-- do Censo (dim_tempo, mês de julho de 2022). Estoque: semiaditivo, soma entre
-- setores, distritos e faixas, mas não ao longo do tempo.
-- Valor nulo = não publicado para o setor (valor não numérico na origem).
CREATE TABLE dw.fato_populacao (
    chave_tempo              INTEGER NOT NULL REFERENCES dw.dim_tempo (chave_tempo),
    chave_setor_censitario   INTEGER NOT NULL REFERENCES dw.dim_setor_censitario (chave_setor_censitario),
    chave_territorio         INTEGER NOT NULL REFERENCES dw.dim_territorio (chave_territorio),
    chave_faixa_etaria       INTEGER NOT NULL REFERENCES dw.dim_faixa_etaria (chave_faixa_etaria),
    qtd_pessoas              INTEGER,
    PRIMARY KEY (chave_tempo, chave_setor_censitario, chave_faixa_etaria)
);
