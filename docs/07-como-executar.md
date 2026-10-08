# Como executar

## Requisitos

| Item | Versão usada | Para quê |
|---|---|---|
| Python | 3.11 ou mais novo (testado no 3.13) | todo o pipeline |
| 7-Zip | qualquer | abrir o pacote `.rar` de microdados de 2019 a 2021 |
| Espaço em disco | cerca de 3 GB livres | 0,9 GB de pacotes, 0,4 GB de Parquet, 0,3 GB de banco e ~1,5 GB de staging temporário durante a carga, mais os arquivos do Censo 2022 |
| Memória | 8 GB recomendados | a carga usa de 2 a 4 GB |

Sem o 7-Zip o pipeline roda todos os anos exceto 2019, 2020 e 2021, e avisa com uma mensagem clara.

## Instalação

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python -m pip install -e ".[dev]"
```

No Linux ou macOS o executável fica em `.venv/bin/python`.

## Execução completa

```bash
.venv/Scripts/python -m dw_sme tudo
```

Isso roda as cinco etapas em sequência. Na primeira vez o download leva alguns minutos; nas seguintes o manifesto evita baixar de novo o que está íntegro.

## Etapa por etapa

| Comando | Entrada | Saída | Tempo aproximado |
|---|---|---|---|
| `python -m dw_sme baixar` | portal de dados abertos da prefeitura e diretório do IBGE | `data/raw/` e `manifesto.json` | depende da rede (~900 MB da SME, mais o Censo) |
| `python -m dw_sme preparar` | pacotes em `data/raw/microdados` | `data/interim/bruto/ano=AAAA/*.parquet` | 3 minutos |
| `python -m dw_sme carregar` | Parquet bruto, planilhas de fila e Censo 2022 | `data/dw/dw_sme.duckdb` | 3 minutos ou pouco mais |
| `python -m dw_sme verificar` | banco | `data/relatorios/qualidade.md` | segundos |
| `python -m dw_sme consultar` | banco | `data/relatorios/consultas/*.csv` | segundos |

Opções comuns a todas as etapas:

| Opção | Efeito |
|---|---|
| `--anos 2019-2024` | muda o recorte (padrão: 2015-2024) |
| `--dados OUTRA_PASTA` | usa outra pasta de dados |
| `--banco arquivo.duckdb` | grava o banco em outro arquivo |
| `--sete-zip CAMINHO` | caminho do `7z.exe`, se ele não for encontrado sozinho |
| `--forcar` | baixa e converte de novo mesmo o que já existe |
| `--manter-staging` | preserva o esquema `stg` no banco, útil para depurar |
| `--sem-ibge` | não baixa o Censo 2022; a carga usa os arquivos que já estiverem em `data/raw/ibge/` |

A etapa `verificar` termina com código de saída 1 se alguma verificação de qualidade tiver situação FALHA.

## População do Censo 2022

`baixar` procura os temas Básico e Demografia dos Agregados por Setores Censitários no diretório do IBGE e os grava em `data/raw/ibge/`. Se o diretório não responder ou tiver mudado de estrutura, a etapa avisa e o resto do pipeline segue. Nesse caso, baixe os dois arquivos à mão em [ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios](https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/) (os nomes contêm `basico` e `demografia`; serve o CSV ou o ZIP com o CSV dentro) e coloque-os em `data/raw/ibge/`. Depois rode `carregar`, `verificar` e `consultar`.

A verificação Q12 diz se a população entrou, quantos setores ficaram sem distrito correspondente na SME e quantos valores não foram publicados.

## Testes

```bash
.venv/Scripts/python -m pytest
```

```bash
.venv/Scripts/python -m pytest --cov=dw_sme --cov-report=term-missing
```

Lint e checagem de tipos:

```bash
.venv/Scripts/python -m ruff check src tests
```

```bash
.venv/Scripts/python -m pip install pyright
```

```bash
.venv/Scripts/pyright
```

O ruff passa limpo e roda no CI. O pyright aponta avisos que vêm dos stubs do pandas e do DuckDB (atributos de `itertuples`, retorno opcional de `fetchone`), não de erro de tipo no código; por isso fica fora do CI.

Os testes não precisam de internet nem dos dados reais. Eles usam:

- trechos reais das planilhas de fila em `tests/fixtures/fila/`, um por formato, com cabeçalho e rodapé originais;
- microdado sintético montado em `tests/conftest.py` com as colunas e os defeitos de cada época (2019 íntegro, 2021 sem turno e sem datas, 2023 com código destruído);
- Censo 2022 sintético no layout dos Agregados por Setores (um tema em ZIP latin-1, outro em CSV UTF-8);
- um servidor falso em memória no lugar do portal da prefeitura e do diretório do IBGE.

Dois arquivos de teste conferem o trabalho como um todo, e não só o código:

- `tests/test_modelo.py`: os esquemas desenhados batem com o banco (atributos, chaves, ligações), as hierarquias são as mesmas no relatório, no DDL e na documentação e valem nos dados (ver [09 Verificação da modelagem](09-verificacao-da-modelagem.md));
- `tests/test_coerencia.py`: contagens, consultas, integrantes e hierarquias citadas são as mesmas no README, em docs/, no relatório e nos slides; os links internos funcionam; os slides usam as imagens atuais de `docs/modelagem/` (ver [10 Auditoria do trabalho](10-auditoria-do-trabalho.md)).

## Consultando o banco

O banco é um arquivo DuckDB comum. Qualquer cliente DuckDB abre, inclusive a própria biblioteca Python:

```bash
.venv/Scripts/python -c "import duckdb; print(duckdb.connect('data/dw/dw_sme.duckdb', read_only=True).sql('select ano, count(*) from dw.fato_matricula join dw.dim_ano_letivo using (chave_ano_letivo) group by 1 order by 1'))"
```

As consultas do trabalho estão em `src/dw_sme/sql/consultas/`, uma por arquivo, prontas para colar em qualquer cliente SQL.

## Problemas comuns

| Sintoma | Causa | Solução |
|---|---|---|
| página HTML de "Requisição Bloqueada" no lugar do JSON | o portal recusa requisição sem User-Agent | o cliente já envia; se mudar `user_agent` na configuração, mantenha um valor descritivo |
| `requer o 7-Zip instalado` | pacote `.rar` de 2019-2021 | instale o 7-Zip ou rode com `--anos 2022-2024` |
| `o arquivo do banco não pode se chamar 'dw.duckdb'` | o DuckDB usa o nome do arquivo como catálogo, que colidiria com o esquema `dw` | use outro nome em `--banco` |
| erro de memória na carga | menos de 8 GB livres | rode com um recorte menor, por exemplo `--anos 2019-2024` |
| `aviso: Censo 2022 não baixado` | diretório do IBGE fora do ar ou com outra estrutura | baixe os temas Básico e Demografia à mão para `data/raw/ibge/` |
| `população do Censo 2022 não carregada: ... colunas esperadas ausentes` | o arquivo do IBGE não tem `CD_SETOR`, `NM_DIST` ou `V01031` a `V01041`; os fatos da SME carregam normalmente e Q12 fica em ALERTA | confira se o arquivo é do tema certo (Básico ou Demografia) e do Censo 2022 e carregue de novo |
