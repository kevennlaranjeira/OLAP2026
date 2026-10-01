# Como executar

## Requisitos

| Item | Versão usada | Para quê |
|---|---|---|
| Python | 3.11 ou mais novo (testado no 3.13) | todo o pipeline |
| 7-Zip | qualquer | abrir o pacote `.rar` de microdados de 2019 a 2021 |
| Espaço em disco | cerca de 2 GB livres | 0,9 GB de pacotes baixados, 0,4 GB de Parquet, 1 a 2 GB de banco |
| Memória | 8 GB recomendados | a gravação do fato de matrícula chega a 4,5 GB |

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
| `python -m dw_sme baixar` | portal de dados abertos da prefeitura | `data/raw/` e `manifesto.json` | depende da rede (~900 MB) |
| `python -m dw_sme preparar` | pacotes em `data/raw/microdados` | `data/interim/bruto/ano=AAAA/*.parquet` | 3 minutos |
| `python -m dw_sme carregar` | Parquet bruto e planilhas de fila | `data/dw/dw_sme.duckdb` | ver relatório de carga |
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

A etapa `verificar` termina com código de saída 1 se alguma verificação de qualidade tiver situação FALHA.

## Testes

```bash
.venv/Scripts/python -m pytest
```

```bash
.venv/Scripts/python -m pytest --cov=dw_sme --cov-report=term-missing
```

Os testes não precisam de internet nem dos dados reais. Eles usam:

- trechos reais das planilhas de fila em `tests/fixtures/fila/`, um por formato, com cabeçalho e rodapé originais;
- microdado sintético montado em `tests/conftest.py` com as colunas e os defeitos de cada época (2019 íntegro, 2021 sem turno e sem datas, 2023 com código destruído);
- um servidor falso em memória no lugar do portal da prefeitura.

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
