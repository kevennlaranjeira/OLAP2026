-- =============================================================================
-- Dimensões do data warehouse da rede municipal de educação de São Paulo
-- Todas as dimensões usam chave primária artificial (inteiro sequencial).
-- As chaves naturais da origem ficam guardadas como atributos.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS dw;

-- Tempo, grão de mês. Usada pelo fato de fila, que é publicado por mês de referência.
-- Hierarquias: mês ⊑ trimestre ⊑ semestre ⊑ ano  e  mês ⊑ bimestre ⊑ ano
CREATE TABLE dw.dim_tempo (
    chave_tempo              INTEGER PRIMARY KEY,
    data_referencia          DATE     NOT NULL UNIQUE,   -- primeiro dia do mês
    ano_mes                  VARCHAR  NOT NULL,          -- 'AAAA-MM', só para leitura
    mes                      SMALLINT NOT NULL,
    nome_mes                 VARCHAR  NOT NULL,
    bimestre                 SMALLINT NOT NULL,
    trimestre                SMALLINT NOT NULL,
    semestre                 SMALLINT NOT NULL,
    ano                      SMALLINT NOT NULL,
    fila_publicada           BOOLEAN  NOT NULL,          -- existe planilha de fila para o mês
    observacao               VARCHAR                     -- notas técnicas da planilha do mês
);

-- Data, grão de dia. Usada com visão para dois papéis no fato de matrícula
-- (data de início e data de fim), como a Dimensão Data do artigo da disciplina.
-- Conformada com dim_tempo por (ano, mes). Hierarquia: dia ⊑ mês ⊑ trimestre ⊑ semestre ⊑ ano
-- A linha com data nula é o membro 'não informada' (2021 não publicou datas).
CREATE TABLE dw.dim_data (
    chave_data               INTEGER PRIMARY KEY,
    data                     DATE UNIQUE,
    dia                      SMALLINT,
    mes                      SMALLINT,
    nome_mes                 VARCHAR,
    trimestre                SMALLINT,
    semestre                 SMALLINT,
    ano                      SMALLINT,
    dia_semana               SMALLINT,                   -- 1 = segunda ... 7 = domingo
    nome_dia_semana          VARCHAR,
    fim_de_semana            BOOLEAN
);

-- Ano letivo, grão de ano. Rollup encolhido de dim_tempo, conformado pelo atributo `ano`.
-- Usada pelos fatos de matrícula e de desfecho, publicados por ano letivo.
CREATE TABLE dw.dim_ano_letivo (
    chave_ano_letivo         INTEGER PRIMARY KEY,
    ano                      SMALLINT NOT NULL UNIQUE,
    qualidade_codigo_escola  VARCHAR  NOT NULL,          -- CONFIAVEL | CONSISTENTE_NO_ANO | CORROMPIDO
    observacao               VARCHAR                     -- limitações do microdado daquele ano
);

-- Território, grão de distrito (os 96 distritos do município).
-- Hierarquia: distrito ⊑ DRE ⊑ município ⊑ UF
CREATE TABLE dw.dim_territorio (
    chave_territorio         INTEGER PRIMARY KEY,
    distrito                 VARCHAR  NOT NULL UNIQUE,
    dre                      VARCHAR,                    -- DRE predominante do distrito
    participacao_dre         DOUBLE,                     -- fração das matrículas do distrito nessa DRE
    municipio                VARCHAR  NOT NULL,
    uf                       VARCHAR  NOT NULL
);

-- Escola, mudança lenta tipo 2: uma linha por versão.
-- Nome, tipo, distrito e DRE abrem versão nova; setor e situação são tipo 1 dentro da versão.
-- Hierarquia: escola ⊑ tipo de unidade ⊑ rede
CREATE TABLE dw.dim_escola (
    chave_escola             INTEGER PRIMARY KEY,
    cod_escola               VARCHAR  NOT NULL,          -- código SME, ou SINT-... quando sintético
    codigo_sintetico         BOOLEAN  NOT NULL,
    versao                   SMALLINT NOT NULL,
    ano_inicio               SMALLINT NOT NULL,
    ano_fim                  SMALLINT NOT NULL,
    versao_atual             BOOLEAN  NOT NULL,
    nome_escola              VARCHAR,
    tipo_escola              VARCHAR,
    rede                     VARCHAR  NOT NULL,          -- DIRETA | CONVENIADA | OUTRAS SECRETARIAS | PARTICULAR
    distrito                 VARCHAR,
    dre                      VARCHAR,
    setor_sme                VARCHAR,                    -- setor administrativo da SME (não é setor censitário)
    situacao                 VARCHAR,
    UNIQUE (cod_escola, versao)
);

-- Etapa de ensino, grão de etapa. Rollup encolhido de dim_serie, conformado por `codigo`.
-- Usada pelo fato de fila, que a prefeitura publica por etapa.
-- Hierarquia: etapa ⊑ nível
CREATE TABLE dw.dim_etapa (
    chave_etapa              INTEGER PRIMARY KEY,
    codigo                   VARCHAR  NOT NULL UNIQUE,
    etapa                    VARCHAR  NOT NULL,
    nivel                    VARCHAR  NOT NULL,
    ordem                    SMALLINT NOT NULL
);

-- Série, grão de série (combinação de modalidade, segmento e série publicada).
-- Hierarquias paralelas: série ⊑ etapa ⊑ nível  e  série ⊑ ciclo
-- (o ciclo interdisciplinar atravessa a fronteira entre anos iniciais e finais)
CREATE TABLE dw.dim_serie (
    chave_serie              INTEGER PRIMARY KEY,
    modalidade               VARCHAR  NOT NULL,
    segmento                 VARCHAR,
    serie                    VARCHAR,
    ciclo                    VARCHAR,
    ordem_serie              SMALLINT,
    educacao_especial        BOOLEAN  NOT NULL,
    codigo_etapa             VARCHAR  NOT NULL,          -- chave natural da dim_etapa (conformidade)
    etapa                    VARCHAR  NOT NULL,
    nivel                    VARCHAR  NOT NULL
);

-- Turno da turma. Hierarquia: turno ⊑ jornada
CREATE TABLE dw.dim_turno (
    chave_turno              INTEGER PRIMARY KEY,
    turno                    VARCHAR  NOT NULL,
    jornada                  VARCHAR  NOT NULL,          -- PARCIAL DIURNO | NOTURNO | INTEGRAL
    origem_turno             VARCHAR  NOT NULL,          -- PUBLICADO | CODIGO_2021 | HORARIO | NAO_INFORMADO
    UNIQUE (turno, origem_turno)
);

-- Idade em 31 de março do ano letivo.
-- Hierarquias paralelas: idade ⊑ faixa escolar ⊑ grupo etário  e  idade ⊑ faixa IBGE
CREATE TABLE dw.dim_idade (
    chave_idade              INTEGER PRIMARY KEY,
    idade                    SMALLINT UNIQUE,            -- nulo = não informada
    faixa_escolar            VARCHAR  NOT NULL,
    faixa_ibge               VARCHAR  NOT NULL,
    grupo_etario             VARCHAR  NOT NULL
);

-- Perfil do aluno (bugiganga de atributos descritivos de baixa cardinalidade).
CREATE TABLE dw.dim_perfil_aluno (
    chave_perfil_aluno       INTEGER PRIMARY KEY,
    codigo_combinacao        VARCHAR  NOT NULL UNIQUE,
    sexo                     VARCHAR  NOT NULL,
    raca_cor                 VARCHAR  NOT NULL,
    altas_habilidades        BOOLEAN,
    idade_estimada           BOOLEAN  NOT NULL
);

-- Deficiência (bugiganga dos 17 indicadores DEF_*).
-- codigo_combinacao: 17 posições, '1' presente, '0' ausente, '-' não coletado naquele ano.
CREATE TABLE dw.dim_deficiencia (
    chave_deficiencia        INTEGER PRIMARY KEY,
    codigo_combinacao        VARCHAR  NOT NULL UNIQUE,
    possui_deficiencia       BOOLEAN  NOT NULL,
    qtd_deficiencias         SMALLINT NOT NULL,
    autismo                  BOOLEAN, surdez_leve BOOLEAN, surdez_severa BOOLEAN,
    surdez_unilateral        BOOLEAN, intelectual BOOLEAN, multipla BOOLEAN,
    cegueira                 BOOLEAN, baixa_visao BOOLEAN, surdocegueira BOOLEAN,
    transtorno_desintegrativo BOOLEAN, sindrome_asperger BOOLEAN, sindrome_rett BOOLEAN,
    fisica_sem_cadeira       BOOLEAN, fisica_cadeirante BOOLEAN, visao_monocular BOOLEAN,
    paralisia_cerebral       BOOLEAN, sindrome_down BOOLEAN
);

-- Situação da matrícula (bugiganga dos 12 indicadores SIT_AL_* mais a situação textual).
-- desfecho: resumo exclusivo com prioridade explícita (ver transformacao/situacao.py).
CREATE TABLE dw.dim_situacao_matricula (
    chave_situacao           INTEGER PRIMARY KEY,
    codigo_combinacao        VARCHAR  NOT NULL UNIQUE,
    situacao_matricula       VARCHAR,
    desfecho                 VARCHAR  NOT NULL,
    aprovado BOOLEAN, reprovado BOOLEAN, abandono BOOLEAN, concluido BOOLEAN,
    transferido BOOLEAN, falecido BOOLEAN, nao_compareceu BOOLEAN, excluido BOOLEAN,
    cessado BOOLEAN, remanejado BOOLEAN, reclassificado BOOLEAN, ativo BOOLEAN
);
