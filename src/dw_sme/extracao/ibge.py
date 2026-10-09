"""Download dos Agregados por Setores Censitários do Censo 2022 no servidor de arquivos do IBGE.

O IBGE publica os agregados num diretório navegável
(ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/),
não num portal CKAN. O cliente lê a listagem do diretório e das subpastas,
procura os arquivos dos temas Básico e Demografia pelo nome e baixa os dois
com o mesmo manifesto SHA-256 usado para as bases da SME.

Quando há mais de um candidato, prefere o arquivo de dados
(Agregados_por_setores_*) a dicionários e notas, o CSV (ou o ZIP com o CSV)
ao XLSX e, entre os restantes, o de nome maior em ordem alfabética, que é a
versão mais recente quando o nome carrega a data de publicação.

Se o diretório mudar de estrutura, a etapa avisa e o pipeline segue sem a
população; os dois arquivos podem ser colocados à mão em data/raw/ibge.
"""
from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

from ..transformacao.populacao import TEMAS
from . import ckan

URL_AGREGADOS = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/"
_HREF = re.compile(r"""href\s*=\s*["']([^"'#?]+)["']""", re.IGNORECASE)


def _ler(url: str, user_agent: str, abrir: Callable, tentativas: int = 3, pausa: float = 2.0) -> bytes:
    requisicao = urllib.request.Request(url, headers={"User-Agent": user_agent})
    ultimo_erro = None
    for tentativa in range(tentativas):
        try:
            with abrir(requisicao, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as erro:
            if erro.code < 500:
                raise          # 404 e afins não melhoram com nova tentativa
            ultimo_erro = erro
            if tentativa + 1 < tentativas:
                time.sleep(pausa * (tentativa + 1))
        except OSError as erro:
            ultimo_erro = erro
            if tentativa + 1 < tentativas:
                time.sleep(pausa * (tentativa + 1))
    raise ultimo_erro or OSError(f"nenhuma tentativa de leitura de {url}")


def links(html: str, base: str) -> list[str]:
    """Links absolutos de uma listagem de diretório, só os que ficam abaixo de `base`."""
    saida = []
    for href in _HREF.findall(html):
        url = urljoin(base, href)
        if url.startswith(base) and url != base and url not in saida:
            saida.append(url)
    return saida


def _nome(url: str) -> str:
    return unquote(urlparse(url).path.rstrip("/").rsplit("/", 1)[-1])


def escolher(arquivos: list[str]) -> dict[str, str]:
    """URL do arquivo de cada tema entre os arquivos listados."""
    escolhidos = {}
    for tema in TEMAS:
        candidatos = [u for u in arquivos
                      if tema in _nome(u).lower() and _nome(u).lower().endswith((".zip", ".csv"))
                      and "xls" not in _nome(u).lower()]
        # dicionários e notas também podem citar o tema no nome; o arquivo de dados é o "Agregados_por_setores_*"
        dados = [u for u in candidatos if _nome(u).lower().startswith("agregados_por_setores")]
        candidatos = dados or candidatos
        if candidatos:
            escolhidos[tema] = max(candidatos, key=lambda u: ("csv" in u.lower(), _nome(u)))
    return escolhidos


def localizar(base: str, user_agent: str, abrir: Callable, profundidade: int = 2) -> dict[str, str]:
    """Percorre a listagem do diretório (e das subpastas, até `profundidade`) atrás dos dois temas."""
    pendentes, vistos, arquivos = [(base, 0)], set(), []
    while pendentes:
        url, nivel = pendentes.pop(0)
        if url in vistos:
            continue
        vistos.add(url)
        try:
            html = _ler(url, user_agent, abrir).decode("utf-8", "replace")
        except OSError:
            if nivel == 0:
                raise          # sem a listagem principal não há o que procurar
            continue           # subpasta inacessível: segue com as outras
        for link in links(html, url):
            if link.endswith("/"):
                if nivel + 1 <= profundidade:
                    pendentes.append((link, nivel + 1))
            else:
                arquivos.append(link)
    return escolher(arquivos)


def baixar(destino: str | Path, user_agent: str, abrir: Callable = urllib.request.urlopen,
           base: str = URL_AGREGADOS, forcar: bool = False) -> dict[str, Path]:
    """Baixa os temas Básico e Demografia para `destino`. Erro se algum dos dois não for encontrado."""
    urls = localizar(base, user_agent, abrir)
    faltando = set(TEMAS) - set(urls)
    if faltando:
        raise FileNotFoundError(f"listagem do IBGE sem arquivo dos temas {sorted(faltando)} em {base}")
    destino = Path(destino)
    manifesto = ckan.Manifesto(destino / "manifesto.json")
    baixados = {}
    for tema, url in sorted(urls.items()):
        nome = _nome(url)
        recurso = ckan.Recurso(id=url, nome=nome, formato=nome.rsplit(".", 1)[-1].upper(), url=url, tamanho=None)
        baixados[tema] = ckan.baixar(recurso, destino, manifesto, user_agent, abrir=abrir, forcar=forcar)
    return baixados
