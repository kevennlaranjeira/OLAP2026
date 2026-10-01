"""Configuração do pipeline: onde ficam os dados, qual recorte, qual banco."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .extracao.arquivos import AUTO
from .extracao.fontes import CKAN_BASE

ANOS_PADRAO = range(2015, 2025)


@dataclass
class Configuracao:
    dir_dados: Path = Path("data")
    anos: range = ANOS_PADRAO
    banco: Path = None  # type: ignore[assignment]  # preenchido em __post_init__
    user_agent: str = "dw-sme/0.1 (trabalho academico SCC0245 ICMC-USP; dados abertos SME-SP)"
    ckan_base: str = CKAN_BASE
    sete_zip: str | Path | None = AUTO
    manter_staging: bool = False
    forcar: bool = False
    log: Callable[..., None] = field(default=print, repr=False)

    def __post_init__(self):
        self.dir_dados = Path(self.dir_dados)
        self.banco = Path(self.banco) if self.banco else self.dir_dados / "dw" / "dw_sme.duckdb"
        if self.banco.stem.lower() in ("dw", "stg"):
            # o DuckDB usa o nome do arquivo como catálogo, que colidiria com os esquemas dw e stg
            raise ValueError(f"o arquivo do banco não pode se chamar '{self.banco.name}'; use outro nome")

    @property
    def dir_raw_microdados(self) -> Path:
        return self.dir_dados / "raw" / "microdados"

    @property
    def dir_raw_fila(self) -> Path:
        return self.dir_dados / "raw" / "demanda"

    @property
    def dir_raw_dicionarios(self) -> Path:
        return self.dir_dados / "raw" / "dicionarios"

    @property
    def dir_bruto(self) -> Path:
        return self.dir_dados / "interim" / "bruto"

    @property
    def dir_temp(self) -> Path:
        return self.dir_dados / "interim" / "tmp"

    @property
    def dir_relatorios(self) -> Path:
        return self.dir_dados / "relatorios"


def intervalo_de_anos(texto: str) -> range:
    """'2015-2024' -> range(2015, 2025); '2019' -> range(2019, 2020)."""
    inicio, _, fim = texto.partition("-")
    inicio, fim = int(inicio), int(fim or inicio)
    if fim < inicio:
        raise ValueError(f"intervalo invertido: {texto}")
    return range(inicio, fim + 1)
