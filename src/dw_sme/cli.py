"""Linha de comando: `dw-sme <etapa>` ou `python -m dw_sme <etapa>`."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import __version__, pipeline
from .config import ANOS_PADRAO, Configuracao, intervalo_de_anos
from .qualidade.verificacoes import FALHA

ETAPAS = ("baixar", "preparar", "carregar", "verificar", "consultar", "tudo")


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dw-sme",
        description="Data warehouse da oferta escolar e da demanda não atendida na rede municipal de São Paulo.",
    )
    p.add_argument("etapa", choices=ETAPAS, help="etapa do pipeline a executar")
    p.add_argument("--dados", type=Path, default=Path("data"), help="pasta de dados (padrão: data)")
    p.add_argument("--anos", type=intervalo_de_anos,
                   default=ANOS_PADRAO, help="recorte, como 2015-2024 (padrão) ou 2019")
    p.add_argument("--banco", type=Path, default=None, help="arquivo DuckDB (padrão: <dados>/dw/dw_sme.duckdb)")
    p.add_argument("--sete-zip", type=Path, default=None, help="caminho do 7z.exe, se não for encontrado sozinho")
    p.add_argument("--forcar", action="store_true", help="baixa e converte de novo mesmo o que já existe")
    p.add_argument("--manter-staging", action="store_true", help="não apaga o esquema stg ao fim da carga")
    p.add_argument("--sem-ibge", action="store_true", help="não baixa a população do Censo 2022 (IBGE)")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def configuracao(args: argparse.Namespace) -> Configuracao:
    extras: dict = {"sete_zip": args.sete_zip} if args.sete_zip else {}
    if args.sem_ibge:
        extras["ibge_base"] = None
    return Configuracao(dir_dados=args.dados, anos=args.anos, banco=args.banco, forcar=args.forcar,
                        manter_staging=args.manter_staging, **extras)


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    cfg = configuracao(args)
    inicio = time.time()
    cfg.log(f"dw-sme {args.etapa} | anos {cfg.anos.start}-{cfg.anos.stop - 1} | banco {cfg.banco}")
    if args.etapa == "baixar":
        cfg.log(f"baixados: {pipeline.baixar(cfg)}")
    elif args.etapa == "preparar":
        cfg.log(f"arquivos preparados: {len(pipeline.preparar(cfg))}")
    elif args.etapa == "carregar":
        r = pipeline.carregar(cfg)
        cfg.log(f"fato_matricula {r['fato_matricula']:,} | fato_fila {r['fato_fila']:,} | "
                f"fato_desfecho {r['fato_desfecho']:,} | fato_turma {r['fato_turma']:,} | "
                f"fato_populacao {r['fato_populacao']:,} | {r['segundos']} s")
    elif args.etapa == "verificar":
        resultado = pipeline.verificar(cfg)
        for v in resultado:
            cfg.log(f"  {v.codigo} {v.status:6} {v.titulo}")
        cfg.log(f"relatório: {cfg.dir_relatorios / 'qualidade.md'}")
        if any(v.status == FALHA for v in resultado):
            return 1
    elif args.etapa == "consultar":
        for codigo, df in pipeline.consultar(cfg).items():
            cfg.log(f"  {codigo}: {len(df)} linhas")
        cfg.log(f"resultados: {cfg.dir_relatorios / 'consultas'}")
    else:
        r = pipeline.executar_tudo(cfg)
        if FALHA in r["verificar"].values():
            return 1
    cfg.log(f"concluído em {time.time() - inicio:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
