"""Leitura da planilha "Demanda Registrada e Matrículas" (SME-SP) em formato canônico.

Entre 2006 e 2026 a planilha foi publicada em sete formatos (A a F, mais a
série histórica H). O significado das colunas numeradas (1), (2) e (3) mudou
junto com o formato. Por isso o parser não usa posição fixa de coluna:

1. lê as duas linhas de cabeçalho e identifica grupo (matrículas, matrícula
   em processo, demanda) e etapa de cada coluna;
2. lê as notas de rodapé para saber o que cada número entre parênteses
   significa naquele arquivo;
3. falha com erro explícito se encontrar coluna numerada sem nota ou nota sem
   significado conhecido, em vez de gravar um número com sentido errado.

Saída: um registro por distrito e etapa, com as medidas abaixo. Medida nula
significa "não publicada naquele período", o que é diferente de zero.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

from .etapas import ETAPA_DA_COLUNA_FILA
from .normalizacao import distrito as normalizar_distrito
from .normalizacao import inteiro_br, texto

MEDIDAS = (
    "matriculas",
    "matriculas_em_processo",
    "demanda_total",
    "demanda_sem_opcao",
    "demanda_sem_opcao_ate_30d",
    "demanda_sem_opcao_mais_30d",
    "demanda_com_opcao",
)

_MESES = {
    "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12,
    "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6,
    "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
}
_REF = re.compile(r"\((\d)\)")
_PARENTESES = re.compile(r"\([^)]*\)")
_NOTA_NUMERADA = re.compile(r"^\((\d)\)\s*-?\s*(.*)$")


@dataclass
class PlanilhaFila:
    periodo: date
    layout: str
    arquivo: str
    linhas: list[dict] = field(default_factory=list)
    totais: dict[str, dict] = field(default_factory=dict)
    observacoes: list[str] = field(default_factory=list)
    colunas_ignoradas: list[str] = field(default_factory=list)
    inconsistencias: list[str] = field(default_factory=list)


# ------------------------------------------------------------------ período

def periodo_do_nome(nome: str) -> date:
    """Mês de referência a partir do nome do arquivo ou do recurso CKAN."""
    tokens = re.split(r"[^A-Z0-9]+", texto(nome) or "")
    mes = next((_MESES[t] for t in tokens if t in _MESES), None)
    anos = [t for t in tokens if t.isdigit() and len(t) in (2, 4)]
    if mes is None or not anos:
        raise ValueError(f"não foi possível identificar mês e ano em {nome!r}")
    ano = int(anos[-1])
    return date(ano + 2000 if ano < 100 else ano, mes, 1)


# ------------------------------------------------------------------ leitura bruta

def _ler_texto(caminho: Path) -> str:
    """Decodifica (utf-8 ou latin-1) e normaliza o fim de linha.

    A série histórica usa retorno de carro sozinho como fim de linha (padrão do
    Mac antigo), que o leitor de CSV recusa.
    """
    bruto = Path(caminho).read_bytes()
    try:
        conteudo = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        conteudo = bruto.decode("latin-1")
    return conteudo.replace("\r\n", "\n").replace("\r", "\n")


def _linhas_csv(caminho: Path) -> list[list[str]]:
    return list(csv.reader(io.StringIO(_ler_texto(caminho)), delimiter=";"))


# ------------------------------------------------------------------ cabeçalho

def _grupo(rotulo: str | None) -> str | None:
    t = texto(rotulo) or ""
    if t.startswith("MATRICULA EM PROCESSO"):
        return "matriculas_em_processo"
    if t.startswith("MATRICULA"):
        return "matriculas"
    if t.startswith("DEMANDA"):
        return "demanda"
    return None


def _sub_rotulo(rotulo: str) -> tuple[str | None, str | None]:
    """'Creche (espera a menos 30 dias) (1) (**)' -> ('CRECHE', '1'); 'Creche Total' -> ('CRECHE', 'TOTAL')."""
    t = texto(rotulo) or ""
    refs = _REF.findall(t)
    total = bool(re.search(r"\bTOTAL\b", t))
    base = _PARENTESES.sub(" ", t)
    base = re.sub(r"\bTOTAL\b", " ", base)
    base = texto(base)
    etapa = ETAPA_DA_COLUNA_FILA.get(base or "")
    if etapa is None:
        return None, None
    return etapa, ("TOTAL" if total else (refs[-1] if refs else None))


@dataclass(frozen=True)
class _Coluna:
    indice: int
    grupo: str
    etapa: str
    ref: str | None  # None = valor simples; 'TOTAL'; ou '1', '2', '3'


def _mapear_colunas(cab1: list[str], cab2: list[str]) -> tuple[list[_Coluna], list[str]]:
    colunas, ignoradas = [], []
    grupo_atual = None
    for i in range(1, max(len(cab1), len(cab2))):
        g = _grupo(cab1[i] if i < len(cab1) else None)
        if g:
            grupo_atual = g
        rotulo = cab2[i] if i < len(cab2) else ""
        etapa, ref = _sub_rotulo(rotulo)
        if grupo_atual is None or etapa is None:
            if (rotulo or "").strip():
                ignoradas.append(rotulo.strip())
            continue
        colunas.append(_Coluna(i, grupo_atual, etapa, ref))
    return colunas, ignoradas


# ------------------------------------------------------------------ rodapé

def _semantica(nota: str) -> str:
    t = texto(nota) or ""
    sem_opcao = "SEM OPCAO" in t or "AGUARDANDO VAGA" in t
    if not sem_opcao and ("COM OPCAO" in t or "UNIDADE ESPECIFICA" in t):
        return "demanda_com_opcao"
    if sem_opcao:
        if "ATE 30" in t or "MENOS DE 30" in t:
            return "demanda_sem_opcao_ate_30d"
        if "MAIS DE 30" in t:
            return "demanda_sem_opcao_mais_30d"
        return "demanda_sem_opcao"
    raise ValueError(f"nota de rodapé sem significado conhecido: {nota!r}")


# Significado das colunas numeradas em cada formato, conforme o rodapé dos
# arquivos que o publicaram completo. Usado só para completar nota ausente.
SEMANTICA_PADRAO = {
    "A": {"1": "demanda_sem_opcao_ate_30d", "2": "demanda_sem_opcao_mais_30d", "3": "demanda_com_opcao"},
    "D": {"1": "demanda_sem_opcao_ate_30d", "2": "demanda_sem_opcao_mais_30d", "3": "demanda_com_opcao"},
    "E": {"1": "demanda_sem_opcao", "2": "demanda_com_opcao"},
    "F": {"1": "demanda_sem_opcao", "2": "demanda_com_opcao"},
}


def _completar_semanticas(colunas: list[_Coluna], semanticas: dict[str, str],
                          layout: str, observacoes: list[str]) -> dict[str, str]:
    """Completa nota ausente com o significado do formato, se houver evidência.

    Só herda quando o arquivo tem ao menos uma nota numerada e todas as notas
    presentes concordam com o formato detectado. Caso real: dez/2024 publicou
    as notas (2) e (3) do formato A, mas não a (1).
    """
    usadas = sorted({c.ref for c in colunas if c.grupo == "demanda" and c.ref not in (None, "TOTAL")})
    faltando = [r for r in usadas if r not in semanticas]
    if not faltando:
        return semanticas
    padrao = SEMANTICA_PADRAO.get(layout)
    if not semanticas or padrao is None:
        raise ValueError(f"colunas de demanda {faltando} sem nota de rodapé que as explique")
    for ref, sem in semanticas.items():
        if padrao.get(ref) != sem:
            raise ValueError(f"nota ({ref}) contradiz o significado conhecido do formato {layout}")
    completas = dict(semanticas)
    for ref in faltando:
        completas[ref] = padrao[ref]
        observacoes.append(
            f"Nota ({ref}) ausente no rodapé; significado herdado do formato {layout}: {padrao[ref]}.")
    return completas


def _ler_rodape(linhas: list[list[str]]) -> tuple[dict[str, str], list[str]]:
    semanticas, observacoes = {}, []
    for linha in linhas:
        conteudo = " ".join(c.strip() for c in linha if c.strip())
        if not conteudo or conteudo.replace("0", "").strip() == "":
            continue
        m = _NOTA_NUMERADA.match(conteudo)
        if m:
            semanticas[m.group(1)] = _semantica(m.group(2))
            continue
        # linha de continuação de nota técnica junta-se à anterior
        if observacoes and not conteudo.startswith(("(", "*")):
            observacoes[-1] = f"{observacoes[-1]} {conteudo}"
        else:
            observacoes.append(conteudo)
    return semanticas, observacoes


# ------------------------------------------------------------------ medidas

def _combinar(valores: dict[tuple[str, str | None], int | None],
              semanticas: dict[str, str], etapa: str, inconsistencias: list[str],
              contexto: str) -> dict:
    """Junta as colunas de uma etapa em um registro canônico."""
    r = {m: None for m in MEDIDAS}
    r["matriculas"] = valores.get(("matriculas", None))
    r["matriculas_em_processo"] = valores.get(("matriculas_em_processo", None))

    for (grupo, ref), v in valores.items():
        if grupo != "demanda" or ref in (None, "TOTAL"):
            continue
        if ref not in semanticas:
            raise ValueError(f"coluna de demanda ({ref}) de {etapa} sem nota de rodapé que a explique")
        r[semanticas[ref]] = v

    ate, mais = r["demanda_sem_opcao_ate_30d"], r["demanda_sem_opcao_mais_30d"]
    if r["demanda_sem_opcao"] is None and ate is not None and mais is not None:
        r["demanda_sem_opcao"] = ate + mais

    explicito = valores.get(("demanda", "TOTAL"), valores.get(("demanda", None)))
    tem_componentes = any(g == "demanda" and ref not in (None, "TOTAL") for g, ref in valores)
    soma = None
    if tem_componentes and r["demanda_sem_opcao"] is not None and r["demanda_com_opcao"] is not None:
        soma = r["demanda_sem_opcao"] + r["demanda_com_opcao"]
    if explicito is not None and soma is not None and explicito != soma:
        inconsistencias.append(f"{contexto} {etapa}: total publicado {explicito} != soma das partes {soma}")
    r["demanda_total"] = explicito if explicito is not None else soma
    return r


def _registro(celulas: list[str], colunas: list[_Coluna], semanticas, inconsistencias, contexto) -> dict[str, dict]:
    por_etapa: dict[str, dict] = {}
    for c in colunas:
        bruto = celulas[c.indice] if c.indice < len(celulas) else None
        por_etapa.setdefault(c.etapa, {})[(c.grupo, c.ref)] = inteiro_br(bruto)
    return {e: _combinar(v, semanticas, e, inconsistencias, contexto) for e, v in por_etapa.items()}


def _codigo_layout(colunas: list[_Coluna]) -> str:
    refs = {(c.etapa, c.ref) for c in colunas if c.grupo == "demanda"}
    em_processo = {c.etapa for c in colunas if c.grupo == "matriculas_em_processo"}
    numeradas = {r for _, r in refs if r not in (None, "TOTAL")}
    if "FUND_I" in em_processo:
        return "C"
    if not numeradas:
        return "B"
    tem_total = any(r == "TOTAL" for _, r in refs)
    if "3" in numeradas:
        return "A" if tem_total else "D"
    if ("PRE", "1") in refs:
        return "E"
    return "F"


# ------------------------------------------------------------------ API

def ler_planilha(caminho: str | Path, periodo: date | None = None) -> PlanilhaFila:
    caminho = Path(caminho)
    linhas = _linhas_csv(caminho)
    if len(linhas) < 3:
        raise ValueError(f"{caminho.name}: arquivo sem cabeçalho de duas linhas")
    colunas, ignoradas = _mapear_colunas(linhas[0], linhas[1])
    if not colunas:
        raise ValueError(f"{caminho.name}: nenhuma coluna reconhecida no cabeçalho")

    corpo, i_total = linhas[2:], None
    for i, l in enumerate(corpo):
        if l and texto(l[0]) == "TOTAL":
            i_total = i
            break
    if i_total is None:
        raise ValueError(f"{caminho.name}: linha TOTAL não encontrada")
    semanticas, observacoes = _ler_rodape(corpo[i_total + 1:])
    layout = _codigo_layout(colunas)
    semanticas = _completar_semanticas(colunas, semanticas, layout, observacoes)

    p = PlanilhaFila(
        periodo=periodo or periodo_do_nome(caminho.name),
        layout=layout,
        arquivo=caminho.name,
        observacoes=observacoes,
        colunas_ignoradas=ignoradas,
    )
    for l in corpo[:i_total]:
        d = normalizar_distrito(l[0]) if l else None
        if not d:
            continue
        contexto = f"{caminho.name} | {d}"
        for etapa, r in _registro(l, colunas, semanticas, p.inconsistencias, contexto).items():
            p.linhas.append({"distrito": d, "etapa": etapa, **r})
    p.totais = _registro(corpo[i_total], colunas, semanticas, p.inconsistencias, f"{caminho.name} | TOTAL")
    return p


_COLUNAS_HISTORICO = {
    "matriculas": {"CRECHE": "MAT_CRECHE", "PRE": "MAT_PRE_ESCOLA", "FUND_I": "MAT_FUND_I",
                   "FUND_II": "MAT_FUND_II", "EJA_I": "MAT_EJA_I", "EJA_II": "MAT_EJA_II",
                   "MEDIO": "MAT_ENS_MED", "ED_PROF": "MAT_ED_PROF"},
    "matriculas_em_processo": {"CRECHE": "MAT_PROC_CRECHE", "PRE": "MAT_PROC_PRE_ESC"},
    "demanda_total": {"CRECHE": "DEM_CRECHE", "PRE": "DEM_PRE", "FUND_I": "DEM_FUND_I",
                      "FUND_II": "DEM_FUND_II", "EJA_I": "DEM_EJA_I", "EJA_II": "DEM_EJA_II"},
}


def ler_serie_historica(caminho: str | Path) -> list[PlanilhaFila]:
    """Série 2006-2017 (formato longo, um mês de referência por linha).

    As colunas DEM_PREF_CRECHE e DEM_PREF_PRE existem no arquivo mas não no
    dicionário oficial; sem definição publicada, não são carregadas.
    """
    caminho = Path(caminho)
    leitor = csv.DictReader(io.StringIO(_ler_texto(caminho)), delimiter=";")
    por_periodo: dict[date, PlanilhaFila] = {}
    for l in leitor:
        periodo = periodo_do_nome(l["MES_ANO_REF"])
        p = por_periodo.setdefault(periodo, PlanilhaFila(periodo=periodo, layout="H", arquivo=caminho.name))
        d = normalizar_distrito(l["DISTRITO"])
        for etapa in _COLUNAS_HISTORICO["matriculas"]:
            r = {m: None for m in MEDIDAS}
            for medida, cols in _COLUNAS_HISTORICO.items():
                if etapa in cols:
                    r[medida] = inteiro_br(l.get(cols[etapa]))
            p.linhas.append({"distrito": d, "etapa": etapa, **r})
    return [por_periodo[k] for k in sorted(por_periodo)]


def conferir_totais(p: PlanilhaFila) -> list[str]:
    """Compara a soma dos distritos com a linha TOTAL publicada, medida a medida."""
    divergencias = []
    for etapa, total in p.totais.items():
        for medida in MEDIDAS:
            publicado = total[medida]
            if publicado is None:
                continue
            valores = [r[medida] for r in p.linhas if r["etapa"] == etapa and r[medida] is not None]
            if sum(valores) != publicado:
                divergencias.append(f"{p.arquivo} {etapa} {medida}: soma {sum(valores)} != TOTAL {publicado}")
    return divergencias


def para_dataframe(planilhas: list[PlanilhaFila]) -> pd.DataFrame:
    registros = [
        {"periodo": p.periodo, **linha, "layout": p.layout, "arquivo": p.arquivo}
        for p in planilhas for linha in p.linhas
    ]
    colunas = ["periodo", "distrito", "etapa", *MEDIDAS, "layout", "arquivo"]
    df = pd.DataFrame(registros, columns=colunas)
    for m in MEDIDAS:
        df[m] = df[m].astype("Int64")
    return df
