"""Etapas do pipeline, na ordem em que o fluxo de dados acontece.

baixar     portal CKAN da prefeitura -> data/raw (com manifesto SHA-256)
preparar   pacotes de microdado -> data/interim/bruto (Parquet, tudo texto)
carregar   bruto + planilhas de fila -> data/dw/dw_sme.duckdb (esquema dw)
verificar  dw -> data/relatorios/qualidade.md
consultar  dw -> data/relatorios/consultas/*.csv
"""
from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable

import duckdb

from .carga.carregar import carregar_tudo
from .config import Configuracao
from .consultas.executar import executar_todas
from .extracao import ckan, fontes
from .preparacao import preparar_microdados
from .qualidade import verificacoes


def baixar(cfg: Configuracao, abrir: Callable = urllib.request.urlopen) -> dict:
    cliente = ckan.ClienteCKAN(cfg.ckan_base, cfg.user_agent, abrir=abrir)
    rec_micro = cliente.recursos(fontes.PACOTE_MICRODADOS)
    rec_fila = cliente.recursos(fontes.PACOTE_FILA)
    planos = [
        (fontes.selecionar_microdados(rec_micro, cfg.anos), cfg.dir_raw_microdados),
        (fontes.selecionar_fila(rec_fila, cfg.anos), cfg.dir_raw_fila),
        (fontes.selecionar_dicionarios(rec_micro + rec_fila), cfg.dir_raw_dicionarios),
    ]
    resumo = {}
    for recursos, destino in planos:
        manifesto = ckan.Manifesto(destino / "manifesto.json")
        for r in recursos:
            cfg.log(f"  {r.nome}")
            ckan.baixar(r, destino, manifesto, cfg.user_agent, abrir=abrir, forcar=cfg.forcar)
        resumo[destino.name] = len(recursos)
    return resumo


def preparar(cfg: Configuracao) -> list[dict]:
    return preparar_microdados(cfg)


def carregar(cfg: Configuracao) -> dict:
    resumo = carregar_tudo(cfg)
    cfg.dir_relatorios.mkdir(parents=True, exist_ok=True)
    meta = resumo.pop("fila_metadados")
    (cfg.dir_relatorios / "fila_metadados.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    (cfg.dir_relatorios / "carga.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return resumo


def verificar(cfg: Configuracao) -> list[verificacoes.Verificacao]:
    meta_arq = cfg.dir_relatorios / "fila_metadados.json"
    carga_arq = cfg.dir_relatorios / "carga.json"
    meta = json.loads(meta_arq.read_text(encoding="utf-8")) if meta_arq.exists() else []
    carga = json.loads(carga_arq.read_text(encoding="utf-8")) if carga_arq.exists() else None
    con = duckdb.connect(str(cfg.banco), read_only=True)
    try:
        resultado = verificacoes.verificar(con, meta)
    finally:
        con.close()
    cfg.dir_relatorios.mkdir(parents=True, exist_ok=True)
    (cfg.dir_relatorios / "qualidade.md").write_text(
        verificacoes.relatorio_markdown(resultado, carga), encoding="utf-8")
    return resultado


def consultar(cfg: Configuracao) -> dict:
    return executar_todas(cfg.banco, cfg.dir_relatorios / "consultas")


def executar_tudo(cfg: Configuracao, abrir: Callable = urllib.request.urlopen) -> dict:
    etapas = {}
    cfg.log("[1/5] baixar")
    etapas["baixar"] = baixar(cfg, abrir)
    cfg.log("[2/5] preparar")
    etapas["preparar"] = len(preparar(cfg))
    cfg.log("[3/5] carregar")
    etapas["carregar"] = carregar(cfg)
    cfg.log("[4/5] verificar")
    etapas["verificar"] = {v.codigo: v.status for v in verificar(cfg)}
    cfg.log("[5/5] consultar")
    etapas["consultar"] = {k: len(v) for k, v in consultar(cfg).items()}
    return etapas
