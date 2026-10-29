"""Coerência entre código, documentação, relatório, apresentação e figuras.

O trabalho existe em várias formas (código, README, docs/, relatório LaTeX, slides, imagens). Estes
testes falham quando uma delas muda e as outras ficam para trás: contagens, consultas, integrantes,
links, textos pendentes, hierarquias citadas e imagens embutidas nos slides.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import zipfile
from pathlib import Path

import duckdb
import pytest

from dw_sme.consultas import executar as ex
from dw_sme.qualidade import verificacoes as q

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
README = RAIZ / "README.md"
RELATORIO = DOCS / "relatorio" / "relatorio-projeto1.tex"
GERADOR = DOCS / "apresentacao" / "gerar.js"
SLIDES = DOCS / "apresentacao" / "apresentacao-projeto1.pptx"
HTML = DOCS / "apresentacao" / "apresentacao-projeto1.html"
PDF_SLIDES = DOCS / "apresentacao" / "apresentacao-projeto1.pdf"
MODELAGEM = DOCS / "modelagem"

INTEGRANTES = [
    ("Kevenn Laranjeira de Oliveira", "18046529"),
    ("Thiago Rodrigues Gouveia da Silva", "18066911"),
    ("Daniel Afonso Borges dos Santos", "12608581"),
    ("Luís Antônio Arruda Soares", "12559486"),
]


def ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8")


def markdowns() -> list[Path]:
    return [README, *sorted(DOCS.glob("*.md"))]


# ----------------------------------------------------------------------------- integrantes

@pytest.mark.parametrize("arquivo", [README, RELATORIO, GERADOR, HTML], ids=lambda p: p.name)
def test_integrantes_e_numeros_usp_iguais_em_todo_lugar(arquivo):
    texto = ler(arquivo)
    for nome, nusp in INTEGRANTES:
        assert nome in texto, f"{arquivo.name} sem {nome}"
        assert nusp in texto, f"{arquivo.name} sem o Nº USP {nusp}"


# ----------------------------------------------------------------------------- consultas

def consultas_sql() -> dict[str, str]:
    return {c.codigo: c.tipo for c in ex.listar()}


def test_oito_consultas_cobrindo_o_enunciado():
    tipos = consultas_sql()
    assert list(tipos) == [f"C{i}" for i in range(1, 9)]
    assert set(tipos.values()) == ex.TIPOS_EXIGIDOS


def test_consultas_iguais_na_documentacao_no_relatorio_e_nos_slides():
    esperado = consultas_sql()
    doc = dict(re.findall(r"^\| (C\d) \| ([a-z\- ]+?) \|", ler(DOCS / "05-consultas.md"), re.MULTILINE))
    relatorio = {f"C{n}": t for n, t in re.findall(r"\\subsection\{Consulta (\d): ([a-z\- ]+)\}", ler(RELATORIO))}
    slides = dict(re.findall(r'\["(C\d)", "([a-z\- ]+)"', ler(GERADOR)))
    html = dict(re.findall(r'>(C\d)</p><p style="[^"]*">([a-z\- ]+)</p>', ler(HTML)))
    assert doc == esperado
    assert relatorio == esperado
    assert slides == esperado
    assert html == esperado


# ----------------------------------------------------------------------------- contagens

def test_quatorze_verificacoes_documentadas():
    con = duckdb.connect()
    codigos = [f"Q{i:02d}" for i in range(1, 15)]
    assert re.findall(r"^\| (Q\d\d) \|", ler(DOCS / "04-integracao-e-qualidade.md"), re.MULTILINE) == codigos
    assert "def hierarquias" in ler(RAIZ / "src" / "dw_sme" / "qualidade" / "verificacoes.py")
    con.close()
    for arquivo, trecho in [(README, "catorze verificações"), (DOCS / "02-fluxo-de-dados.md", "Catorze verificações"),
                            (GERADOR, "14 verificações"), (HTML, "14 verificações")]:
        assert trecho in ler(arquivo), f"{arquivo.name} não fala em {trecho}"


def test_verificar_devolve_as_quatorze_na_ordem(tmp_path):
    import inspect
    fonte = inspect.getsource(q.verificar)
    corpo = fonte.split("return", 1)[1]
    chamadas = re.findall(r"(\w+)\((?:con|fila_meta)\)", corpo)
    assert len(chamadas) == 14 and len(set(chamadas)) == 14


def test_decisoes_numeradas_em_sequencia():
    numeros = [int(n) for n in re.findall(r"^## D(\d\d)\.", ler(DOCS / "06-decisoes.md"), re.MULTILINE)]
    assert numeros == list(range(1, len(numeros) + 1))
    assert f"{len(numeros)} decisões de projeto" in ler(README)


def test_cinco_fatos_quatorze_dimensoes_vinte_e_sete_chaves_em_todo_lugar():
    assert len(q.CHAVES_ESTRANGEIRAS) == 5
    assert sum(len(v) for v in q.CHAVES_ESTRANGEIRAS.values()) == 27
    assert "constelação com 5 tabelas de fatos e 14 dimensões" in ler(README)
    assert "todas as 14 dimensões" in ler(DOCS / "03-modelo-dimensional.md")
    assert "todas as 14 dimensões" in ler(RELATORIO)
    assert "27 chaves estrangeiras" in ler(DOCS / "04-integracao-e-qualidade.md")


def notas_dos_slides() -> list[str]:
    with zipfile.ZipFile(SLIDES) as z:
        nomes = [n for n in z.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)]
        return [z.read(n).decode("utf-8") for n in sorted(nomes, key=lambda n: int(re.findall(r"\d+", n)[0]))]


def test_vinte_e_nove_slides_em_quatro_blocos():
    with zipfile.ZipFile(SLIDES) as z:
        slides = [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
    assert len(slides) == 29
    assert "29 slides" in ler(DOCS / "08-pendencias-da-entrega.md")
    notas = " ".join(notas_dos_slides())
    for bloco in range(1, 5):
        assert f"(bloco {bloco} de 4)" in notas


def test_slides_com_numero_de_pagina_transicao_e_animacao():
    with zipfile.ZipFile(SLIDES) as z:
        slides = [z.read(n).decode("utf-8") for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
        layouts = " ".join(z.read(n).decode("utf-8") for n in z.namelist()
                           if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n))
    assert 'type="sldNum"' in layouts, "layout sem o campo de número de página"
    assert all("<p:transition" in s for s in slides), "slide sem transição"
    animados = sum('presetClass="entr"' in s for s in slides)
    assert animados >= 15, f"só {animados} slides com animação de entrada"


TEMPO_COMBINADO = {1: 7.0, 2: 5.0, 3: 5.0, 4: 5.0}


def test_cada_integrante_apresenta_no_tempo_combinado():
    """Enunciado: todos apresentam, com tempo homogêneo. Os blocos 2 a 4 têm 5 minutos; o bloco 1 tem 2 a mais porque
    abre a apresentação e vende a proposta, escolha registrada em docs/08 com o que fazer se a professora segurar os 20."""
    tempos = {}
    for nota in notas_dos_slides():
        achado = re.search(r"Apresenta: ([^(]+) \(bloco (\d) de 4\)\. Tempo previsto: ([\d,]+) min", nota)
        assert achado, "slide sem apresentador ou sem tempo previsto nas notas"
        nome, bloco, minutos = achado.group(1).strip(), int(achado.group(2)), float(achado.group(3).replace(",", "."))
        assert nome == INTEGRANTES[bloco - 1][0]
        tempos[bloco] = tempos.get(bloco, 0) + minutos
    assert tempos == TEMPO_COMBINADO, f"tempos por integrante: {tempos}"
    assert "7 minutos" in ler(DOCS / "08-pendencias-da-entrega.md")


# ----------------------------------------------------------------------------- versão em HTML

APRESENTADOR = re.compile(r"Apresenta: ([^(]+) \(bloco (\d) de 4\)\. Tempo previsto: ([\d,]+) min")


def secoes_html() -> list[str]:
    return re.findall(r'<section id="[\w-]+".*?</section>', ler(HTML), re.S)


def lista(texto: str, padrao: str) -> list[float]:
    return [float(v) for v in re.search(padrao, texto, re.S).group(1).split(",")]


def test_versao_html_tem_os_mesmos_slides_apresentadores_e_tempos():
    secoes = secoes_html()
    assert len(secoes) == 29
    for numero, secao in enumerate(secoes[1:], start=2):
        assert f"<b>{numero}</b></span> / 29" in secao, f"slide {numero} sem o número da página"
    notas_html = [re.search(r"<aside>(.*?)</aside>", s, re.S).group(1) for s in secoes]
    assert [APRESENTADOR.search(n).groups() for n in notas_html] == \
        [APRESENTADOR.search(n).groups() for n in notas_dos_slides()]


def test_graficos_da_versao_html_usam_os_numeros_dos_slides():
    js, html = ler(GERADOR), ler(HTML)
    fila_html = [float(v) for v in re.findall(r'\["20\d\d",(\d+)\]', re.search(r"var D=(\[.*?\]);", html).group(1))]
    assert fila_html == lista(js, r'name: "Fila de creche em junho".*?values: \[([^\]]+)\]')
    assert lista(html, r"var V=\[([\d.,]+)\],X0") == lista(js, r'name: "Fração fora da rede".*?values: \[([^\]]+)\]')
    turmas = re.findall(r'\["[^"]+",([\d.]+),([\d.]+)\]', re.search(r"var G=(\[.*?\]);", html).group(1))
    assert [float(a) for a, _ in turmas] == lista(js, r'name: "2019", labels: \[[^\]]+\], values: \[([^\]]+)\]')
    assert [float(b) for _, b in turmas] == lista(js, r'name: "2024", labels: \[[^\]]+\], values: \[([^\]]+)\]')
    for numero in ["124.741", "3.633", "13,4 mi", "26.889", "551 mil", "514.131", "598.406", "94,8% a 98,6%",
                   "6.543", "402 escolas", "24.398", "8.018", "11.498", "82,7", "71,6", "2.502", "1.131", "38.869", "0,42 s", "CENÁRIO HIPOTÉTICO"]:
        assert numero in js and numero in html, f"{numero} não está nas duas versões"


def test_distritos_do_grafico_da_c7_batem_com_a_documentacao():
    distritos = lista(ler(HTML), r"var V=\[([\d.,]+)\];")
    consultas = ler(DOCS / "05-consultas.md")
    assert len(distritos) == 96 and distritos == sorted(distritos)
    assert sum(v < 50 for v in distritos) == 25 and "Em 25 deles" in consultas
    assert sum(v > 100 for v in distritos) == 25 and "Em outros 25" in consultas
    assert distritos[0] == 4.7 and "Jardim Paulista (4,7)" in consultas
    assert distritos[-1] == 169.7 and "Lajeado (169,7)" in consultas


def test_versao_html_abre_sozinha():
    """Um arquivo só: sem scripts nem imagens de fora; da internet, só a fonte (com fonte do sistema de reserva)."""
    html = ler(HTML)
    assert "<script src" not in html and 'src="' not in html
    assert set(re.findall(r'href="([^"]+)"', html)) <= {
        "https://fonts.googleapis.com", "https://fonts.gstatic.com",
        "https://fonts.googleapis.com/css2?family=Public+Sans:wght@400..800&family=Space+Grotesk:wght@400..700&display=swap",
    }


def test_pdf_da_apresentacao_tem_uma_pagina_por_slide():
    """O PDF é a apresentação que o GitHub mostra no navegador. Sai do HTML (?imprimir); slide novo pede PDF novo."""
    paginas = len(re.findall(rb"/Type\s*/Page(?![s\w])", PDF_SLIDES.read_bytes()))
    with zipfile.ZipFile(SLIDES) as z:
        slides = [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
    assert paginas == len(slides) == len(secoes_html())


# ----------------------------------------------------------------------------- links e pendências

@pytest.mark.parametrize("arquivo", markdowns(), ids=lambda p: p.name)
def test_links_internos_apontam_para_arquivos_que_existem(arquivo):
    for alvo in re.findall(r"\]\(([^)]+)\)", ler(arquivo)):
        if alvo.startswith(("http://", "https://", "#", "mailto:")):
            continue
        caminho = (arquivo.parent / alvo.split("#")[0]).resolve()
        assert caminho.exists(), f"{arquivo.name}: link quebrado para {alvo}"


# TODO e FIXME só em maiúsculas: "todo" é palavra comum em português
PENDENTES = re.compile(r"\[NOME COMPLETO\]|\[Nº USP\]|\bTODO\b|\bFIXME\b|\bXXX\b|(?i:lorem ipsum)")


@pytest.mark.parametrize("arquivo", [*markdowns(), RELATORIO, GERADOR, HTML, MODELAGEM / "modelagem.tex"],
                         ids=lambda p: p.name)
def test_nenhum_texto_pendente_esquecido(arquivo):
    # as figuras embutidas no HTML são base64, não texto: "XXX" aparece nelas por acaso
    texto = re.sub(r'<script id="figuras".*?</script>', "", ler(arquivo), flags=re.S)
    assert not PENDENTES.findall(texto)


def test_capa_completa_e_sem_marcador_para_preencher():
    """A capa tem os itens do enunciado, com os cursos e a data de entrega; nenhum marcador entre colchetes sobra."""
    texto = ler(RELATORIO)
    assert not re.findall(r"\[[A-ZÇÃÕÉÍ ]{6,}\]", texto)
    capa = re.search(r"\\begin\{titlepage\}(.*?)\\end\{titlepage\}", texto, re.S).group(1)
    for trecho in ["Universidade de São Paulo", "SCC0245 Processamento Analítico de Dados",
                   "Profa. Dra. Cristina Dutra de Aguiar", "Primeiro Trabalho Prático", "Grupo 7",
                   "Ciência de Dados", "Mestrado em Ciência da Computação",
                   "São Carlos, 29 de outubro de 2026"]:
        assert trecho in capa, f"capa sem {trecho}"


# ----------------------------------------------------------------------------- figuras

def hash_arquivo(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def test_slides_usam_as_imagens_atuais_da_modelagem():
    atuais = {hash_arquivo(p.read_bytes()) for p in MODELAGEM.glob("*.png")}
    with zipfile.ZipFile(SLIDES) as z:
        embutidas = {hash_arquivo(z.read(n)) for n in z.namelist() if n.startswith("ppt/media/") and n.endswith(".png")}
    assert embutidas and embutidas == atuais


def test_versao_html_embute_as_imagens_atuais_da_modelagem():
    html = ler(HTML)
    bloco = re.search(r'<script id="figuras" type="application/json">(.*?)</script>', html, re.S).group(1)
    embutidas = {nome: hash_arquivo(base64.b64decode(dado.split(",", 1)[1])) for nome, dado in json.loads(bloco).items()}
    atuais = {p.stem: hash_arquivo(p.read_bytes()) for p in MODELAGEM.glob("*.png")}
    assert embutidas == atuais, "figuras do HTML desatualizadas: rode docs/apresentacao/embutir_figuras.py"
    assert set(re.findall(r'data-figura="([\w-]+)"', html)) == set(atuais)


def test_uma_imagem_por_esquema_do_relatorio():
    fontes = {p.stem for p in (DOCS / "relatorio" / "esquemas").glob("*.tex")} - {"estilo"}
    assert {p.stem for p in MODELAGEM.glob("*.png")} == fontes
    for fonte in fontes:
        assert f"esquemas/{fonte}" in ler(MODELAGEM / "figuras.tex")


# ----------------------------------------------------------------------------- hierarquias citadas

def cadeias(texto: str) -> list[list[str]]:
    """Cada 'a ≤ b ≤ c' do texto como lista de palavras (aceita ≤ e \\leq)."""
    texto = texto.replace("$\\leq$", "≤").replace("\\leq", "≤").replace(" e ", "; ")
    saida = []
    for trecho in re.findall(r"[\wçãõéíóúâêô ]+(?:\s*≤\s*[\wçãõéíóúâêôIBGEDRUF ]+)+", texto):
        partes = [p.strip() for p in trecho.split("≤")]
        partes[0] = partes[0].split(";")[-1].split(":")[-1].strip()
        saida.append([re.sub(r"^(e|com|Hierarquias|Hierarquia)\s+", "", p).strip() for p in partes])
    return saida


def pares_permitidos() -> set[tuple[str, str]]:
    """Pares (filho, pai) das hierarquias escritas no relatório, comparando sem caixa."""
    import test_modelo
    texto = ler(RELATORIO)
    secao = texto[texto.index(r"\section{Esquemas}"):texto.index(r"\section{Consultas}")]
    pares = set()
    for h in test_modelo.argumentos(secao, "\\hier"):
        cadeia = [p.lower() for p in test_modelo._cadeia(h)]
        pares |= set(zip(cadeia, cadeia[1:], strict=False))
    return pares


@pytest.mark.parametrize("arquivo", [GERADOR, MODELAGEM / "modelagem.tex"], ids=lambda p: p.name)
def test_hierarquias_citadas_sao_as_declaradas(arquivo):
    permitidos = pares_permitidos()
    citadas = [c for c in cadeias(ler(arquivo)) if len(c) > 1]
    assert citadas
    niveis = {n for par in permitidos for n in par}
    for cadeia in citadas:
        # numa frase, o primeiro nível vem depois de texto livre: fica o maior final que é um nível
        palavras = cadeia[0].lower().split()
        cadeia[0] = next((" ".join(palavras[i:]) for i in range(len(palavras)) if " ".join(palavras[i:]) in niveis),
                         cadeia[0])
        for filho, pai in zip(cadeia, cadeia[1:], strict=False):
            assert (filho.lower(), pai.lower()) in permitidos, f"{arquivo.name}: '{filho} ≤ {pai}' não é declarada"
