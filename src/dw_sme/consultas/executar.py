"""Consultas analíticas do trabalho, guardadas em sql/consultas/*.sql.

Cada arquivo tem um cabeçalho de metadados ('-- codigo:', '-- tipo:',
'-- titulo:', '-- pergunta:', '-- justificativa:', '-- fatos:') que é lido
aqui e reaproveitado na documentação e no relatório.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import duckdb
import pandas as pd

TIPOS_EXIGIDOS = {"roll-up", "drill-down", "slice and dice", "pivot", "drill-across"}


@dataclass(frozen=True)
class Consulta:
    codigo: str
    tipo: str
    titulo: str
    pergunta: str
    justificativa: str
    fatos: tuple[str, ...]
    arquivo: str
    sql: str


def _ler(nome: str, texto: str) -> Consulta:
    meta = {}
    for linha in texto.splitlines():
        if not linha.startswith("-- "):
            break
        chave, sep, valor = linha[3:].partition(":")
        if sep:
            meta[chave.strip()] = valor.strip()
    faltando = {"codigo", "tipo", "titulo", "pergunta", "justificativa", "fatos"} - set(meta)
    if faltando:
        raise ValueError(f"{nome}: cabeçalho sem {sorted(faltando)}")
    return Consulta(
        codigo=meta["codigo"], tipo=meta["tipo"], titulo=meta["titulo"], pergunta=meta["pergunta"],
        justificativa=meta["justificativa"], fatos=tuple(f.strip() for f in meta["fatos"].split(",")),
        arquivo=nome, sql=texto,
    )


def listar() -> list[Consulta]:
    pasta = resources.files("dw_sme") / "sql" / "consultas"
    arquivos = sorted(p.name for p in pasta.iterdir() if p.name.endswith(".sql"))
    return [_ler(a, (pasta / a).read_text(encoding="utf-8")) for a in arquivos]


def executar(con: duckdb.DuckDBPyConnection, consulta: Consulta) -> pd.DataFrame:
    return con.execute(consulta.sql).df()


def executar_todas(banco: str | Path, destino: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Roda todas as consultas sobre o banco; se `destino` for dado, grava um CSV por consulta."""
    con = duckdb.connect(str(banco), read_only=True)
    try:
        resultados = {c.codigo: executar(con, c) for c in listar()}
    finally:
        con.close()
    if destino:
        destino = Path(destino)
        destino.mkdir(parents=True, exist_ok=True)
        for c in listar():
            # contagens com nulo viram float no pandas ('55.0'); no CSV voltam a inteiro
            resultados[c.codigo].convert_dtypes().to_csv(destino / f"{Path(c.arquivo).stem}.csv", index=False,
                                                         encoding="utf-8")
    return resultados
