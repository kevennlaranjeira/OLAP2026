"""Texto que entra numa instrução SQL como literal entre aspas simples."""
from __future__ import annotations

from pathlib import Path


def literal(valor: str | Path) -> str:
    """'valor' com as aspas simples dobradas. Caminhos usam barra normal, que o DuckDB aceita em qualquer sistema."""
    texto = valor.as_posix() if isinstance(valor, Path) else str(valor)
    return "'" + texto.replace("'", "''") + "'"
