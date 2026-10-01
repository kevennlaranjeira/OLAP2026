"""Cliente do portal de dados abertos (CKAN) da Prefeitura de São Paulo e manifesto de downloads.

Duas particularidades do portal:
- requisições sem cabeçalho User-Agent são bloqueadas pela PRODAM com uma
  página HTML de "Requisição Bloqueada", não com código de erro;
- os pacotes de microdados chegam a 350 MB, então o download é feito em
  blocos, com hash calculado durante a escrita.

O manifesto (JSON) registra URL, tamanho e SHA-256 de cada arquivo. Rodar o
pipeline de novo não baixa o que já está íntegro em disco e detecta arquivo
alterado ou corrompido.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_BLOCO = 1 << 20


@dataclass(frozen=True)
class Recurso:
    id: str
    nome: str
    formato: str
    url: str
    tamanho: int | None

    @classmethod
    def de_ckan(cls, r: dict) -> Recurso:
        return cls(id=r["id"], nome=(r.get("name") or "").strip(),
                   formato=(r.get("format") or "").strip().upper().lstrip("."),
                   url=r["url"], tamanho=r.get("size"))

    @property
    def arquivo(self) -> str:
        return self.url.rstrip("/").rsplit("/", 1)[-1]


class ClienteCKAN:
    def __init__(self, base_url: str, user_agent: str, abrir: Callable = urllib.request.urlopen,
                 tentativas: int = 3, pausa: float = 2.0, timeout: float = 120):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self._abrir, self.tentativas, self.pausa, self.timeout = abrir, tentativas, pausa, timeout

    def _requisicao(self, url: str) -> urllib.request.Request:
        return urllib.request.Request(url, headers={"User-Agent": self.user_agent})

    def _ler(self, url: str) -> bytes:
        ultimo_erro = None
        for tentativa in range(self.tentativas):
            try:
                with self._abrir(self._requisicao(url), timeout=self.timeout) as resp:
                    return resp.read()
            except OSError as erro:
                ultimo_erro = erro
                if tentativa + 1 < self.tentativas:
                    time.sleep(self.pausa * (tentativa + 1))
        raise ultimo_erro or OSError(f"nenhuma tentativa de leitura de {url}")

    def pacote(self, identificador: str) -> dict:
        corpo = self._ler(f"{self.base_url}/package_show?id={identificador}")
        try:
            dados = json.loads(corpo)
        except json.JSONDecodeError as erro:
            raise RuntimeError(f"resposta não é JSON (bloqueio da PRODAM?): {corpo[:120]!r}") from erro
        if not dados.get("success"):
            raise RuntimeError(f"CKAN recusou package_show?id={identificador}")
        return dados["result"]

    def recursos(self, identificador: str) -> list[Recurso]:
        return [Recurso.de_ckan(r) for r in self.pacote(identificador)["resources"]]


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while bloco := f.read(_BLOCO):
            h.update(bloco)
    return h.hexdigest()


class Manifesto:
    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho)
        self.entradas: dict[str, dict] = (
            json.loads(self.caminho.read_text(encoding="utf-8")) if self.caminho.exists() else {}
        )

    def entrada(self, arquivo: str) -> dict | None:
        return self.entradas.get(arquivo)

    def registrar(self, arquivo: str, recurso: Recurso, sha256: str, tamanho: int) -> None:
        self.entradas[arquivo] = {
            "url": recurso.url, "recurso_id": recurso.id, "nome": recurso.nome,
            "sha256": sha256, "bytes": tamanho, "baixado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(json.dumps(self.entradas, ensure_ascii=False, indent=1, sort_keys=True),
                                encoding="utf-8")

    def verificar(self, diretorio: str | Path) -> list[str]:
        """Arquivos do manifesto ausentes do diretório ou com hash diferente do registrado."""
        problemas = []
        for arquivo, e in sorted(self.entradas.items()):
            caminho = Path(diretorio) / arquivo
            if not caminho.exists() or sha256_arquivo(caminho) != e["sha256"]:
                problemas.append(arquivo)
        return problemas


def baixar(recurso: Recurso, destino_dir: str | Path, manifesto: Manifesto, user_agent: str,
           abrir: Callable = urllib.request.urlopen, tentativas: int = 3, pausa: float = 2.0,
           forcar: bool = False) -> Path:
    """Baixa o recurso se não houver cópia íntegra registrada no manifesto."""
    destino_dir = Path(destino_dir)
    destino = destino_dir / recurso.arquivo
    registrado = manifesto.entrada(recurso.arquivo)
    if (not forcar and destino.exists() and registrado and registrado["url"] == recurso.url
            and sha256_arquivo(destino) == registrado["sha256"]):
        return destino

    destino_dir.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_name(destino.name + ".parcial")
    requisicao = urllib.request.Request(recurso.url, headers={"User-Agent": user_agent})
    ultimo_erro = None
    for tentativa in range(tentativas):
        try:
            h, total = hashlib.sha256(), 0
            with abrir(requisicao, timeout=600) as resp, open(parcial, "wb") as f:
                while bloco := resp.read(_BLOCO):
                    f.write(bloco)
                    h.update(bloco)
                    total += len(bloco)
            parcial.replace(destino)
            manifesto.registrar(recurso.arquivo, recurso, h.hexdigest(), total)
            return destino
        except OSError as erro:
            ultimo_erro = erro
            if tentativa + 1 < tentativas:
                time.sleep(pausa * (tentativa + 1))
    raise ultimo_erro or OSError(f"nenhuma tentativa de download de {recurso.url}")
