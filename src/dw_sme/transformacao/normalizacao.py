"""Regras de normalização de valores textuais e numéricos das bases da SME-SP.

Cada função recebe o valor como publicado e devolve a forma canônica usada no
data warehouse. As regras existem porque a mesma informação aparece com
grafias diferentes entre anos e entre bases (ver docs/04-integracao-e-qualidade.md).

As funções são aplicadas sobre os valores *distintos* de cada coluna, nunca
linha a linha: o resultado vira uma tabela de correspondência que o DuckDB
junta com os 15 milhões de linhas do microdado.
"""
from __future__ import annotations

import re
import unicodedata

_ESPACOS = re.compile(r"\s+")
# U+FFFD aparece quando um arquivo latin1 é lido como utf-8 ou vice-versa.
# Nos dados ele ocupa o lugar de 'Ã' ou 'Á' em palavras como NÃO e INTERMEDIÁRIO.
_SUBSTITUICAO = "\ufffd"


def _nulo(valor) -> bool:
    # NaN (float) é como o pandas representa nulo em colunas de texto
    return valor is None or (isinstance(valor, float) and valor != valor)


def texto(valor: str | None) -> str | None:
    """Maiúsculas, sem acento, espaços colapsados. Vazio e NaN viram None."""
    if _nulo(valor):
        return None
    s = str(valor).replace(_SUBSTITUICAO, "A")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = _ESPACOS.sub(" ", s).strip().upper()
    return s or None


def inteiro_br(valor: str | None) -> int | None:
    """Converte números no formato brasileiro publicado pela SME.

    '1.188' -> 1188 (ponto de milhar), '5,00' -> 5 (vírgula decimal).
    Notação científica ('1,32551E+13') é recusada: indica código corrompido.
    """
    if _nulo(valor):
        return None
    s = str(valor).strip()
    if not s or "E" in s.upper():
        return None
    s = s.replace(".", "")
    if "," in s:
        inteiro, _, decimal = s.partition(",")
        if decimal.strip("0"):
            return None
        s = inteiro
    return int(s) if s.lstrip("-").isdigit() else None


def distrito(valor: str | None) -> str | None:
    """Nome do distrito na forma usada como chave natural do território."""
    return texto(valor)


DRES = (
    "BUTANTA", "CAMPO LIMPO", "CAPELA DO SOCORRO", "FREGUESIA/BRASILANDIA",
    "GUAIANASES", "IPIRANGA", "ITAQUERA", "JACANA/TREMEMBE", "PENHA",
    "PIRITUBA/JARAGUA", "SANTO AMARO", "SAO MATEUS", "SAO MIGUEL",
)
_DRE_PREFIXO = "DIRETORIA REGIONAL DE EDUCACAO "
_DRE_APELIDOS = {"PIRITUBA": "PIRITUBA/JARAGUA"}


def dre(valor: str | None) -> str | None:
    """Uma das 13 Diretorias Regionais de Educação, ou None se não reconhecida."""
    s = texto(valor)
    if s is None:
        return None
    if s.startswith(_DRE_PREFIXO):
        s = s[len(_DRE_PREFIXO):]
    s = _DRE_APELIDOS.get(s, s)
    return s if s in DRES else None


_TIPOS = {
    "CEIINDIRET": "CEI INDIR", "CEIINDIR": "CEI INDIR",
    "CEIDIRET": "CEI DIRET", "CEIDIR": "CEI DIRET",
    "CCI-CIPS": "CCI/CIPS", "CCI/CIPS": "CCI/CIPS",
    "CEUATCOMPL": "CEU AT COMPL", "CEUATCOM": "CEU AT COMPL",
    "ETECNICA": "E TECNICA", "ETEC": "E TECNICA", "ET": "E TECNICA",
    "CR.P.CONV": "CR.P.CONV", "ESPCONV": "ESP CONV",
    "CEUEMEF": "CEU EMEF", "CEUEMEI": "CEU EMEI", "CEUCEI": "CEU CEI",
    "CEUCEMEI": "CEU CEMEI", "EMEIPFOM": "EMEI P FOM", "EMEFPFOM": "EMEF P FOM",
    "ESC.PART.": "ESC.PART.",
}


def tipo_escola(valor: str | None) -> str | None:
    """Tipo de unidade. A chave de comparação ignora espaços, que variam por ano."""
    s = texto(valor)
    if s is None:
        return None
    return _TIPOS.get(s.replace(" ", ""), s)


_CONVENIADAS = {"CR.P.CONV", "CEI INDIR", "ESP CONV", "MOVA"}
_OUTRAS_SECRETARIAS = {"CCA", "CCI/CIPS", "E TECNICA"}


def rede(tipo: str | None) -> str:
    """Rede a que a unidade pertence, derivada do tipo já normalizado."""
    if tipo is None:
        return "NAO INFORMADA"
    if tipo in _CONVENIADAS:
        return "CONVENIADA"
    if tipo in _OUTRAS_SECRETARIAS:
        return "OUTRAS SECRETARIAS"
    if tipo == "ESC.PART.":
        return "PARTICULAR"
    return "DIRETA"


TURNOS = ("MANHA", "INTERMEDIARIO", "TARDE", "VESPERTINO", "NOITE", "INTEGRAL")


def turno(valor: str | None) -> str | None:
    s = texto(valor)
    return s if s in TURNOS else None


_TURNO_2021 = {"4": "MANHA", "5": "INTERMEDIARIO", "6": "TARDE",
               "7": "VESPERTINO", "8": "NOITE", "9": "INTEGRAL"}


def turno_codigo_2021(codigo: str | None) -> str | None:
    """Em 2021 a descrição do turno é vazia e o código é o de 2020 somado de 3."""
    if codigo is None:
        return None
    return _TURNO_2021.get(str(codigo).strip().lstrip("0"))


def _minutos(hhmm: str | None) -> int | None:
    if hhmm is None:
        return None
    s = str(hhmm).strip()
    if not s.isdigit() or not 3 <= len(s) <= 4:
        return None
    h, m = int(s[:-2]), int(s[-2:])
    return h * 60 + m if h < 24 and m < 60 else None


def turno_por_horario(inicio: str | None, fim: str | None) -> str | None:
    """Classificação de recurso, usada só quando a descrição e o código faltam.

    Distingue apenas manhã, tarde, noite e integral: intermediário e
    vespertino são categorias administrativas que o horário não revela.
    """
    a, b = _minutos(inicio), _minutos(fim)
    if a is None or b is None or b <= a:
        return None
    if a >= 18 * 60:
        return "NOITE"
    if b - a >= 7 * 60:
        return "INTEGRAL"
    return "MANHA" if a < 12 * 60 else "TARDE"


_JORNADA = {"MANHA": "PARCIAL DIURNO", "INTERMEDIARIO": "PARCIAL DIURNO",
            "TARDE": "PARCIAL DIURNO", "VESPERTINO": "PARCIAL DIURNO",
            "NOITE": "NOTURNO", "INTEGRAL": "INTEGRAL"}


def jornada(turno_normalizado: str | None) -> str:
    return _JORNADA.get(turno_normalizado, "NAO INFORMADA")


_RACAS = {"BRANCA", "PRETA", "PARDA", "AMARELA", "INDIGENA", "NAO DECLARADA"}


def raca_cor(valor: str | None) -> str:
    s = texto(valor)
    if s is None:
        return "NAO INFORMADA"
    if s.startswith("RECUSOU"):
        return "RECUSOU INFORMAR"
    return s if s in _RACAS else "NAO INFORMADA"


def sexo(valor: str | None) -> str:
    return {"F": "FEMININO", "M": "MASCULINO"}.get(texto(valor), "NAO INFORMADO")


def situacao_escola(valor: str | None) -> str:
    s = texto(valor)
    if s is None:
        return "NAO INFORMADA"
    if "PARALI" in s:
        return "PARALISADA"
    for alvo in ("ATIVA", "EXTINTA", "CRIADA"):
        if alvo in s:
            return alvo
    return "NAO INFORMADA"
