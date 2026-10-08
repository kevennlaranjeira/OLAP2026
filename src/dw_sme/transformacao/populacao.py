"""População residente do Censo Demográfico 2022 (IBGE) por setor censitário e faixa etária.

Fonte: Agregados por Setores Censitários, Resultados do Universo. Dois temas:

- Básico (arquivo Agregados_por_setores_basico_BR): identifica o setor e o
  nome do distrito a que ele pertence (CD_SETOR, NM_DIST);
- Demografia (arquivo Agregados_por_setores_demografia_BR): pessoas por grupo
  de idade, variáveis V01031 a V01041 (0 a 4, 5 a 9, ..., 70 anos ou mais).

Os arquivos cobrem o país; só os setores do município entram (código IBGE
3550308, São Paulo). A leitura procura as colunas pelo nome, sem posição
fixa, e para com erro se alguma das esperadas faltar ou se a maior parte dos
valores não for número: um layout diferente do documentado não vira número
com sentido errado.

O código do setor tem 15 dígitos: UF (2), município (5), distrito (2),
subdistrito (2) e setor (4). O distrito do IBGE sai dos 9 primeiros. O nome
do distrito vem do tema Básico e é normalizado com a mesma regra usada para
os distritos da SME (maiúsculas, sem acento), o que liga o setor à dimensão
Território.

Valor não numérico numa variável vira nulo (não publicado), nunca zero; a
quantidade de valores assim fica registrada nos metadados.
"""
from __future__ import annotations

import io
import re
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .idade import FAIXAS_IBGE
from .normalizacao import distrito as normalizar_distrito

MUNICIPIO_SAO_PAULO = "3550308"
TEMAS = ("basico", "demografia")
# V01031 a V01041, na ordem das faixas quinquenais da dimensão Idade.
VARIAVEIS_FAIXA = tuple(
    (f"V{1031 + i:05d}", rotulo, inicio, None if fim >= 999 else fim)
    for i, (inicio, fim, rotulo) in enumerate(FAIXAS_IBGE)
)
_DIGITOS = re.compile(r"\D")
FRACAO_MAXIMA_NAO_NUMERICA = 0.5


@dataclass
class Populacao:
    setores: pd.DataFrame          # cd_setor, cd_distrito_ibge, nome_distrito_ibge, distrito
    pessoas: pd.DataFrame          # cd_setor, faixa_ibge, qtd_pessoas
    meta: dict = field(default_factory=dict)


def localizar(diretorio: str | Path) -> dict[str, Path]:
    """Arquivo de cada tema na pasta (CSV ou ZIP com o CSV dentro). Tema ausente fica fora do dicionário."""
    achados: dict[str, Path] = {}
    pasta = Path(diretorio)
    if not pasta.exists():
        return achados
    for caminho in sorted(pasta.iterdir()):
        nome = caminho.name.lower()
        if caminho.suffix.lower() not in (".csv", ".zip"):
            continue
        for tema in TEMAS:
            if tema in nome:
                achados[tema] = caminho   # em ordem alfabética, a versão mais recente fica por último
    return achados


def _decodificar(bruto: bytes) -> str:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return bruto.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("codificação não reconhecida")   # pragma: no cover - latin-1 decodifica qualquer byte


def _bytes_do_csv(caminho: Path) -> bytes:
    if caminho.suffix.lower() != ".zip":
        return caminho.read_bytes()
    with zipfile.ZipFile(caminho) as z:
        membros = [m for m in z.namelist() if m.lower().endswith(".csv")]
        if not membros:
            raise ValueError(f"{caminho.name}: nenhum CSV dentro do pacote")
        return z.read(sorted(membros)[0])


def ler_csv(caminho: Path, colunas: set[str]) -> pd.DataFrame:
    """Lê só as colunas pedidas (comparação sem caixa), tudo como texto; nomes devolvidos em maiúsculas."""
    texto = _decodificar(_bytes_do_csv(caminho))
    cabecalho = texto.split("\n", 1)[0]
    separador = ";" if cabecalho.count(";") >= cabecalho.count(",") else ","
    df = pd.read_csv(io.StringIO(texto), sep=separador, dtype=str, na_filter=False,
                     usecols=lambda c: c.strip().upper() in colunas)
    df.columns = [c.strip().upper() for c in df.columns]
    faltando = colunas - set(df.columns)
    if faltando:
        raise ValueError(f"{caminho.name}: colunas esperadas ausentes {sorted(faltando)}")
    return df


def codigo_setor(valor: str | None) -> str | None:
    """Os 15 dígitos do código do setor, ou None se o valor não tiver 15 dígitos."""
    if valor is None:
        return None
    digitos = _DIGITOS.sub("", str(valor))
    return digitos[:15] if len(digitos) >= 15 else None


def contagem(valor: str | None) -> int | None:
    """Contagem de pessoas publicada; qualquer coisa que não seja só dígitos é 'não publicada'."""
    if valor is None:
        return None
    s = str(valor).strip()
    return int(s) if s.isdigit() else None


def ler(diretorio: str | Path, municipio: str = MUNICIPIO_SAO_PAULO) -> Populacao | None:
    """População do município por setor e faixa etária; None se os dois temas não estiverem na pasta."""
    arquivos = localizar(diretorio)
    if set(arquivos) != set(TEMAS):
        return None

    basico = ler_csv(arquivos["basico"], {"CD_SETOR", "NM_DIST"})
    basico["cd_setor"] = basico["CD_SETOR"].map(codigo_setor)
    basico = basico[basico["cd_setor"].fillna("").str.startswith(municipio)]
    nome_por_setor = {cd: str(nome).strip() for cd, nome in zip(basico["cd_setor"], basico["NM_DIST"], strict=True)
                      if isinstance(nome, str) and nome.strip()}

    variaveis = {v for v, *_ in VARIAVEIS_FAIXA}
    demografia = ler_csv(arquivos["demografia"], {"CD_SETOR"} | variaveis)
    demografia["cd_setor"] = demografia["CD_SETOR"].map(codigo_setor)
    sem_codigo = int(demografia["cd_setor"].isna().to_numpy().sum())
    demografia = demografia[demografia["cd_setor"].fillna("").str.startswith(municipio)]
    repetidos = sorted(demografia.loc[demografia["cd_setor"].duplicated(), "cd_setor"].unique())
    if repetidos:
        raise ValueError(f"{arquivos['demografia'].name}: setor censitário repetido {repetidos[:5]}; "
                         "cada setor deve aparecer uma vez no tema Demografia")

    # nome do distrito: o do próprio setor; se faltar, o mais comum entre os setores do mesmo distrito IBGE.
    # Calculado em listas Python: no pandas 3 a coluna de texto troca None por NaN, que é verdadeiro.
    codigos = sorted(set(demografia["cd_setor"]))
    distritos_ibge = [cd[:9] for cd in codigos]
    proprios = [nome_por_setor.get(cd) or None for cd in codigos]
    nomes_por_distrito: dict[str, Counter] = {}
    for cd, nome in zip(distritos_ibge, proprios, strict=True):
        if nome:
            nomes_por_distrito.setdefault(cd, Counter())[nome] += 1
    nomes = [nome or (nomes_por_distrito[cd].most_common(1)[0][0] if cd in nomes_por_distrito else None)
             for cd, nome in zip(distritos_ibge, proprios, strict=True)]
    setores = pd.DataFrame({
        "cd_setor": codigos, "cd_distrito_ibge": distritos_ibge, "nome_distrito_ibge": nomes,
        "distrito": [normalizar_distrito(n) or "NAO INFORMADO" for n in nomes],
    })

    longo = demografia.melt(id_vars="cd_setor", value_vars=sorted(variaveis), var_name="variavel", value_name="bruto")
    rotulo = {v: r for v, r, *_ in VARIAVEIS_FAIXA}
    contagens = [contagem(v) for v in longo["bruto"]]
    pessoas = pd.DataFrame({
        "cd_setor": longo["cd_setor"],
        "faixa_ibge": [rotulo[v] for v in longo["variavel"]],
        "qtd_pessoas": pd.array(contagens, dtype="Int64"),
    })
    nao_numericos = contagens.count(None)
    if len(pessoas) and nao_numericos / len(pessoas) > FRACAO_MAXIMA_NAO_NUMERICA:
        raise ValueError(f"{arquivos['demografia'].name}: {nao_numericos} de {len(pessoas)} valores não numéricos; "
                         "o layout não é o documentado")
    meta = {
        "arquivos": {t: p.name for t, p in arquivos.items()},
        "municipio": municipio,
        "setores": len(setores),
        "distritos_ibge": len(set(distritos_ibge)),
        "setores_sem_nome_de_distrito": sum(n is None for n in nomes),
        "linhas_sem_codigo_de_setor": sem_codigo,
        "valores_nao_numericos": nao_numericos,
        "pessoas": sum(v for v in contagens if v is not None),
    }
    return Populacao(setores=setores, pessoas=pessoas, meta=meta)
