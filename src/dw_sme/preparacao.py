"""Preparação: dos arquivos baixados ao formato que a carga consome.

- Microdados: cada CSV de escolarização dentro dos pacotes vira um Parquet
  bruto (todas as colunas como texto, nomes originais), um arquivo por vez,
  apagando o CSV extraído logo depois. Dez anos ocupam ~8 GB em CSV e ~420 MB
  em Parquet.
- Fila: as planilhas de todos os formatos viram um único DataFrame canônico.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

from .config import Configuracao
from .extracao import arquivos, fontes
from .texto_sql import literal
from .transformacao import fila as fila_mod


def preparar_microdados(cfg: Configuracao) -> list[dict]:
    """Converte para Parquet os CSVs de escolarização do recorte. Pula o que já existe."""
    registros = []
    for pacote in sorted(cfg.dir_raw_microdados.glob("*")):
        if pacote.suffix.lower() not in (".zip", ".rar"):
            continue
        for membro in arquivos.listar(pacote, cfg.sete_zip):
            ano = fontes.ano_do_membro_escolarizacao(membro)
            if ano is None or ano not in cfg.anos:
                continue
            destino = cfg.dir_bruto / f"ano={ano}" / (Path(membro).stem + ".parquet")
            if destino.exists() and not cfg.forcar:
                registros.append({"ano": ano, "pacote": pacote.name, "membro": membro, "situacao": "existente"})
                continue
            cfg.log(f"  preparando {Path(membro).name} ({ano})")
            csv = arquivos.extrair(pacote, membro, cfg.dir_temp, cfg.sete_zip)
            try:
                registros.append({"ano": ano, "pacote": pacote.name, "membro": membro,
                                  **_csv_para_parquet(csv, destino)})
            finally:
                csv.unlink(missing_ok=True)
    cfg.dir_bruto.mkdir(parents=True, exist_ok=True)
    (cfg.dir_bruto / "_preparacao.json").write_text(
        json.dumps(registros, ensure_ascii=False, indent=1), encoding="utf-8")
    return registros


def _csv_para_parquet(csv: Path, destino: Path) -> dict:
    enc = arquivos.detectar_encoding(csv)
    sep = arquivos.detectar_separador(csv)
    destino.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        con.execute(f"""
            CREATE TABLE t AS SELECT * FROM read_csv({literal(csv)}, delim={literal(sep)}, header=true,
                all_varchar=true, encoding='{'utf-8' if enc == 'utf-8' else 'latin-1'}', quote='"',
                strict_mode=false, null_padding=true, store_rejects=true)""")
        linhas = con.execute("SELECT count(*) FROM t").fetchall()[0][0]
        rejeitadas = con.execute("SELECT count(*) FROM reject_errors").fetchall()[0][0]
        con.execute(f"COPY t TO {literal(destino)} (FORMAT parquet, COMPRESSION zstd)")
    finally:
        con.close()
    return {"situacao": "convertido", "encoding": enc, "separador": sep,
            "linhas": linhas, "rejeitadas": rejeitadas}


def preparar_fila(cfg: Configuracao) -> tuple[pd.DataFrame, list[dict]]:
    """Lê todas as planilhas de fila e devolve o DataFrame canônico do recorte e os metadados por período."""
    planilhas = []
    for csv in sorted(cfg.dir_raw_fila.glob("*.csv")):
        nome = csv.name.lower()
        if nome.startswith("dic") or "dicionario" in nome:
            continue
        if "evolucao" in nome:
            planilhas += fila_mod.ler_serie_historica(csv)
        else:
            planilhas.append(fila_mod.ler_planilha(csv))
    planilhas = [p for p in planilhas if p.periodo.year in cfg.anos]
    periodos = [p.periodo for p in planilhas]
    duplicados = {d for d in periodos if periodos.count(d) > 1}
    if duplicados:
        raise ValueError(f"mais de uma planilha para os períodos {sorted(duplicados)}")
    metadados = [{
        "periodo": p.periodo.isoformat(), "arquivo": p.arquivo, "formato": p.layout,
        "distritos": len({r["distrito"] for r in p.linhas}),
        "observacoes": p.observacoes, "colunas_ignoradas": p.colunas_ignoradas,
        "inconsistencias": p.inconsistencias,
        "divergencias_total": fila_mod.conferir_totais(p) if p.layout != "H" else [],
    } for p in sorted(planilhas, key=lambda x: x.periodo)]
    return fila_mod.para_dataframe(planilhas), metadados
