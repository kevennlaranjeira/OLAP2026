"""Verificação da modelagem: desenhos, DDL, relatório e dados contam a mesma história.

- cada caixa dos esquemas estrela (docs/relatorio/esquemas/*.tex) corresponde a uma tabela do DDL,
  com os mesmos atributos e as mesmas chaves estrangeiras;
- a constelação e a matriz de barramento do relatório ligam cada fato às mesmas dimensões que o DDL;
- as hierarquias escritas no relatório, no DDL e em docs/03 são as mesmas, e valem nos dados como
  dependência funcional (cada membro de um nível pertence a um único membro do nível acima);
- os rollups encolhidos carregam os mesmos valores das dimensões de que derivam (conformidade).
"""
from __future__ import annotations

import re
import shutil
import unicodedata
from collections import Counter
from pathlib import Path

import duckdb
import pytest

from dw_sme.carga import carregar
from dw_sme.config import Configuracao
from dw_sme.qualidade import verificacoes as q

RAIZ = Path(__file__).resolve().parents[1]
ESQUEMAS = RAIZ / "docs" / "relatorio" / "esquemas"
RELATORIO = RAIZ / "docs" / "relatorio" / "relatorio-projeto1.tex"
DDL = RAIZ / "src" / "dw_sme" / "sql" / "ddl" / "01_dimensoes.sql"
DOC_MODELO = RAIZ / "docs" / "03-modelo-dimensional.md"

FATOS = {"fato_matricula", "fato_fila", "fato_desfecho", "fato_turma", "fato_populacao"}
VISOES = {"fato_desfecho": "vw_desfecho_taxas", "fato_turma": "vw_ocupacao_turma"}


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    from conftest import FIXTURES, _gravar, gravar_ibge, microdado_2019, microdado_2021, microdado_2023
    raiz = tmp_path_factory.mktemp("modelo")
    dados = raiz / "data"
    bruto = dados / "interim" / "bruto"
    _gravar(microdado_2019(), bruto / "ano=2019" / "Microdados_EOL_Matriculas_Ano_2019.parquet")
    _gravar(microdado_2021(), bruto / "ano=2021" / "Microdados_EOL_Matriculas_Ano_2021.parquet")
    infantil, _ = microdado_2023()
    _gravar(infantil, bruto / "ano=2023" / "Microdados_Matricula_EOL_Escolarizacao_Educacao_Infantil_2023.parquet")
    (dados / "raw" / "demanda").mkdir(parents=True)
    for f in (FIXTURES / "fila").glob("*.csv"):
        shutil.copy(f, dados / "raw" / "demanda" / f.name)
    gravar_ibge(dados / "raw" / "ibge")
    cfg = Configuracao(dir_dados=dados, banco=raiz / "dw_modelo.duckdb", log=lambda *_: None)
    carregar.carregar_tudo(cfg)
    c = duckdb.connect(str(cfg.banco), read_only=True)
    yield c
    c.close()


def colunas(con, tabela: str) -> list[str]:
    return [r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = 'dw' AND table_name = ? "
        "ORDER BY ordinal_position", [tabela]).fetchall()]


def tabelas(con, prefixo: str) -> set[str]:
    return {r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'dw' AND table_type = 'BASE TABLE' "
        "AND table_name LIKE ?", [prefixo + "%"]).fetchall()}


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def nome_tabela(titulo: str) -> str:
    """'Dimensão Ano Letivo' -> dim_ano_letivo; 'Tabela de Fatos Ocupação de Turma' -> fato_turma."""
    t = _sem_acento(re.sub(r"\s+", " ", titulo.replace("\\\\", " ")).strip()).lower()
    t = re.sub(r"\(.*?\)", "", t).strip()
    especiais = {"tabela de fatos ocupacao de turma": "fato_turma"}
    if t in especiais:
        return especiais[t]
    if t.startswith("dimensao "):
        return "dim_" + t[len("dimensao "):].replace(" ", "_")
    return "fato_" + t[len("tabela de fatos "):].replace(" ", "_")


# ----------------------------------------------------------------------------- esquemas estrela

_NO = re.compile(r"\\node\[(dim|fato)[^\]]*\]\s*\((\w+)\)(?:\s*at\s*\([^)]*\))?\s*\{\\textbf\{([^}]*)\}(.*?)\};",
                 re.DOTALL)
SINONIMOS = {
    "*": {"dia_da_semana": "dia_semana", "codigo_escola": "cod_escola", "raca_e_cor": "raca_cor",
          "codigo_setor": "cd_setor", "codigo_distrito_ibge": "cd_distrito_ibge",
          "codigo_matricula": "cd_matricula_origem", "dias_de_matricula": "qtd_dias_matricula",
          "quantidade_turmas": "qtd_turmas", "quantidade_de_pessoas": "qtd_pessoas", "nome_do_dia": "nome_dia_semana"},
    "fato_matricula": {"quantidade_matriculas": "qtd_matricula"},
    "fato_fila": {"demanda_sem_opcao_ate_30_dias": "qtd_demanda_sem_opcao_ate_30d",
                  "demanda_sem_opcao_mais_de_30_dias": "qtd_demanda_sem_opcao_mais_30d",
                  "demanda_com_opcao_por_unidade": "qtd_demanda_com_opcao"},
    "fato_turma": {"matriculas_no_ano": "qtd_matriculas", "matriculas_ativas_em_junho": "qtd_matriculas_ativas_junho",
                   "turmas_ativas_em_junho": "qtd_turmas_ativas_junho", "alunos_por_turma": "alunos_por_turma_junho"},
    "dim_serie": {"ordem": "ordem_serie"},
    "dim_deficiencia": {"quantidade": "qtd_deficiencias"},
}


def caixas(arquivo: Path) -> list[dict]:
    """Caixas de um esquema: id do nó, tabela, rótulos dos atributos e se a lista é parcial ('...')."""
    saida = []
    for tipo, ident, titulo, corpo in _NO.findall(arquivo.read_text(encoding="utf-8")):
        corpo = corpo.split("\\nodepart{two}", 1)[1]
        corpo = re.sub(r"\\hfill\\textit\{[^}]*\}", "", corpo)
        corpo = re.sub(r"\\textit\{([^}]*)\}", r"\1", corpo)
        corpo = re.sub(r"\d+ indicadores \([^)]*\)", "INDICADORES", corpo)
        corpo = re.sub(r"\s*\((?:derivad[ao]|degenerada|artificial)\)", "", corpo)
        rotulos, parcial = [], False
        for linha in corpo.split("\\\\"):
            linha = linha.replace("(PK)", "").replace("(FK)", "").strip()
            for r in (x.strip() for x in linha.split(",")):
                if r == "...":
                    parcial = True
                elif r:
                    rotulos.append(r)
        saida.append({"id": ident, "tipo": tipo, "tabela": nome_tabela(titulo), "rotulos": rotulos,
                      "parcial": parcial, "fk": [r for r in rotulos if r.startswith("chave ")] if tipo == "fato" else []})
    return saida


def resolver(rotulo: str, tabela: str, disponiveis: list[str]) -> str | None:
    n = _sem_acento(rotulo).lower().replace(" ", "_")
    candidatos = [SINONIMOS.get(tabela, {}).get(n), SINONIMOS["*"].get(n), n, "qtd_" + n]
    return next((c for c in candidatos if c and c in disponiveis), None)


def ligacoes_estrela(arquivo: Path) -> Counter:
    """Quantas linhas saem de cada caixa de dimensão para a tabela de fatos."""
    cont: Counter = Counter()
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        if "\\draw[liga]" not in linha:
            continue
        if linha.lstrip().startswith("\\foreach"):
            lista = re.search(r"\{([\w/,]+)\}", linha).group(1)
            cont.update(item.split("/")[0] for item in lista.split(","))
        else:
            cont[re.search(r"\((?:\[[^\]]*\])?(\w+)\.(?:east|west|north|south)\)", linha).group(1)] += 1
    return cont


ESTRELAS = sorted(ESQUEMAS.glob("estrela-*.tex"))


def test_cinco_estrelas_e_cinco_fatos(con):
    fatos = {c["tabela"] for a in ESTRELAS for c in caixas(a) if c["tipo"] == "fato"}
    assert fatos == FATOS == tabelas(con, "fato_")
    dims = {c["tabela"] for a in ESTRELAS for c in caixas(a) if c["tipo"] == "dim"}
    assert dims == tabelas(con, "dim_") and len(dims) == 14


@pytest.mark.parametrize("arquivo", ESTRELAS, ids=lambda p: p.stem)
def test_caixas_do_desenho_batem_com_o_ddl(con, arquivo):
    for caixa in caixas(arquivo):
        tabela = caixa["tabela"]
        disponiveis = colunas(con, tabela) + (colunas(con, VISOES[tabela]) if tabela in VISOES else [])
        mostradas = set()
        for rotulo in caixa["rotulos"]:
            if rotulo == "INDICADORES":
                tipos = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                                         "WHERE table_schema = 'dw' AND table_name = ?", [tabela]).fetchall())
                mostradas |= {c for c, t in tipos.items() if t == "BOOLEAN"}
                continue
            coluna = resolver(rotulo, tabela, disponiveis)
            assert coluna, f"{arquivo.name}: '{rotulo}' da caixa {tabela} não existe no DDL"
            mostradas.add(coluna)
        if not caixa["parcial"]:
            faltando = set(colunas(con, tabela)) - mostradas
            assert not faltando, f"{arquivo.name}: caixa {tabela} sem {sorted(faltando)} (complete ou use '...')"


@pytest.mark.parametrize("arquivo", ESTRELAS, ids=lambda p: p.stem)
def test_chaves_estrangeiras_e_ligacoes_da_estrela(con, arquivo):
    todas = caixas(arquivo)
    fato = next(c for c in todas if c["tipo"] == "fato")
    fks = q.CHAVES_ESTRANGEIRAS[fato["tabela"]]
    disponiveis = colunas(con, fato["tabela"])
    assert sorted(resolver(r, fato["tabela"], disponiveis) for r in fato["fk"]) == sorted(c for c, _, _ in fks)
    esperado = Counter(dim for _, dim, _ in fks)
    desenhado = Counter({c["tabela"]: ligacoes_estrela(arquivo)[c["id"]] for c in todas if c["tipo"] == "dim"})
    assert desenhado == esperado      # inclusive as duas linhas da Data com dois papéis


def test_chaves_estrangeiras_declaradas_cobrem_todas_as_chaves_dos_fatos(con):
    for fato in FATOS:
        chaves = {c for c in colunas(con, fato) if c.startswith("chave_")}
        assert chaves == {c for c, _, _ in q.CHAVES_ESTRANGEIRAS[fato]}, fato


def test_toda_dimensao_tem_chave_artificial_inteira(con):
    for dim in tabelas(con, "dim_"):
        pk = con.execute("""SELECT constraint_column_names FROM duckdb_constraints()
                            WHERE schema_name = 'dw' AND table_name = ? AND constraint_type = 'PRIMARY KEY'""",
                         [dim]).fetchone()
        assert pk and len(pk[0]) == 1 and pk[0][0].startswith("chave_"), dim
        tipo = con.execute("SELECT data_type FROM information_schema.columns WHERE table_schema = 'dw' "
                           "AND table_name = ? AND column_name = ?", [dim, pk[0][0]]).fetchone()[0]
        assert tipo == "INTEGER", dim


# ----------------------------------------------------------------------------- constelação e barramento

ROLLUPS = {("dim_data", "dim_ano_letivo"), ("dim_data", "dim_tempo"), ("dim_serie", "dim_etapa"),
           ("dim_setor_censitario", "dim_territorio"), ("dim_idade", "dim_faixa_etaria")}


def ligacoes_por_fato() -> Counter:
    return Counter((fato, dim) for fato, fks in q.CHAVES_ESTRANGEIRAS.items() for _, dim, _ in fks)


def test_constelacao_liga_os_mesmos_fatos_e_dimensoes_do_ddl():
    texto = (ESQUEMAS / "constelacao.tex").read_text(encoding="utf-8")
    nos = {i: nome_tabela(t) for i, t in re.findall(r"\\node\[nome(?:fato)?\]\s*\((\w+)\)\s*at\s*\([^)]*\)\s*\{([^}]*)\}",
                                                     texto)}
    linhas, rollups = Counter(), set()
    for linha in texto.splitlines():
        ids = re.findall(r"\((?:\[[^\]]*\])?([A-Z]{2})(?:\.\w+)?\)", linha)
        if "\\draw[liga]" in linha:
            if linha.lstrip().startswith("\\foreach"):
                lista = re.search(r"\{([A-Z,]+)\}", linha).group(1).split(",")
                linhas.update((nos[ids[0]], nos[d]) for d in lista)
            else:
                linhas[(nos[ids[0]], nos[ids[1]])] += 1
        elif "\\draw[rollup]" in linha:
            rollups.add((nos[ids[0]], nos[ids[1]]))
    assert linhas == ligacoes_por_fato()
    assert rollups == ROLLUPS


@pytest.mark.parametrize("arquivo", [RELATORIO, RAIZ / "docs" / "modelagem" / "modelagem.tex"], ids=lambda p: p.stem)
def test_matriz_de_barramento_bate_com_o_ddl(arquivo):
    texto = arquivo.read_text(encoding="utf-8")
    bloco = texto[texto.index(r"\textbf{Dimensão} & \textbf{Matrícula}"):]
    bloco = bloco[:bloco.index(r"\bottomrule")]
    cabecalho, *linhas = [x for x in bloco.split("\\\\") if "&" in x]
    fatos = {"Matrícula": "fato_matricula", "Fila": "fato_fila", "Desfecho": "fato_desfecho", "Turma": "fato_turma",
             "População": "fato_populacao"}
    ordem = [fatos[re.sub(r"\\textbf\{|\}", "", c).strip()] for c in cabecalho.split("&")[1:]]
    nomes = {"Território": "dim_territorio", "Ano Letivo": "dim_ano_letivo", "Tempo": "dim_tempo", "Data": "dim_data",
             "Escola": "dim_escola", "Série": "dim_serie", "Etapa": "dim_etapa", "Turno": "dim_turno",
             "Idade": "dim_idade", "Faixa Etária": "dim_faixa_etaria", "Setor Censitário": "dim_setor_censitario",
             "Perfil do Aluno": "dim_perfil_aluno", "Deficiência": "dim_deficiencia",
             "Situação": "dim_situacao_matricula"}
    matriz = set()
    for linha in linhas:
        celulas = linha.replace(r"\midrule", "").split("&")
        rotulo = re.sub(r"\(.*?\)", "", celulas[0]).strip()
        for dim in (nomes[r.strip()] for r in rotulo.split(",")):
            matriz |= {(fato, dim) for fato, c in zip(ordem, celulas[1:], strict=True) if "times" in c}
    assert matriz == set(ligacoes_por_fato())
    assert len({d for _, d in matriz}) == 14


# ----------------------------------------------------------------------------- hierarquias

PALAVRAS = {
    "dim_data": {"dia": ("data",), "mês": ("ano", "mes"), "trimestre": ("ano", "trimestre"),
                 "semestre": ("ano", "semestre"), "ano": ("ano",)},
    "dim_tempo": {"mês": ("ano", "mes"), "trimestre": ("ano", "trimestre"), "semestre": ("ano", "semestre"),
                  "bimestre": ("ano", "bimestre"), "ano": ("ano",)},
    "dim_territorio": {"distrito": ("distrito",), "DRE": ("dre",), "município": ("municipio",), "UF": ("uf",)},
    "dim_escola": {"escola": ("chave_escola",), "tipo de unidade": ("tipo_escola",), "rede": ("rede",)},
    "dim_serie": {"série": ("chave_serie",), "etapa": ("codigo_etapa",), "nível": ("nivel",), "ciclo": ("ciclo",)},
    "dim_etapa": {"etapa": ("codigo",), "nível": ("nivel",)},
    "dim_turno": {"turno": ("turno",), "jornada": ("jornada",)},
    "dim_idade": {"idade": ("idade",), "faixa escolar": ("faixa_escolar",), "grupo etário": ("grupo_etario",),
                  "faixa IBGE": ("faixa_ibge",)},
    # do setor até o distrito na própria dimensão; do distrito para cima, a hierarquia de Território
    "dim_setor_censitario": {"setor censitário": ("cd_setor",), "distrito": ("distrito",), "DRE": ("dre",),
                             "município": ("municipio",), "UF": ("uf",)},
}


def pares(dim: str, cadeia: list[str]) -> set[tuple]:
    niveis = [PALAVRAS[dim][p] for p in cadeia]
    saida = set()
    for filho, pai in zip(niveis, niveis[1:], strict=False):
        alvo = "dim_territorio" if dim == "dim_setor_censitario" and filho != ("cd_setor",) else dim
        saida.add((alvo, filho, pai))
    return saida


def pares_declarados() -> set[tuple]:
    return {(d, f, p) for d, lista in q.HIERARQUIAS.items() for niveis in lista
            for f, p in zip(niveis, niveis[1:], strict=False)}


def _cadeia(texto: str) -> list[str]:
    return [re.sub(r"\\text\{|\}|\$", "", x).strip() for x in re.split(r"\\leq|≤", texto)]


def hierarquias_do_relatorio() -> set[tuple]:
    texto = RELATORIO.read_text(encoding="utf-8")
    secao = texto[texto.index(r"\section{Esquemas}"):texto.index(r"\section{Consultas}")]
    item = {"Data": "dim_data", "Tempo": "dim_tempo", "Território": "dim_territorio", "Escola": "dim_escola",
            "Série": "dim_serie", "Turno": "dim_turno", "Idade": "dim_idade", "Etapa": "dim_etapa",
            "Setor Censitário": "dim_setor_censitario", "Faixa Etária": "dim_idade"}
    saida = set()
    for rotulo, resto in re.findall(r"\\item ([^:]+): (.*)", secao):
        for h in argumentos(resto, "\\hier"):
            saida |= pares(item[rotulo.strip()], _cadeia(h))
    return saida


def argumentos(texto: str, comando: str) -> list[str]:
    """Conteúdo de cada comando{...} do texto, respeitando chaves aninhadas."""
    saida, inicio = [], 0
    while (i := texto.find(comando + "{", inicio)) >= 0:
        j, nivel = i + len(comando) + 1, 1
        while nivel:
            nivel += {"{": 1, "}": -1}.get(texto[j], 0)
            j += 1
        saida.append(texto[i + len(comando) + 1:j - 1])
        inicio = j
    return saida


def hierarquias_do_ddl() -> set[tuple]:
    saida = set()
    for comentario, tabela in re.findall(r"((?:--[^\n]*\n)+)CREATE TABLE dw\.(\w+)", DDL.read_text(encoding="utf-8")):
        for linha in comentario.splitlines():
            if "≤" not in linha:
                continue
            linha = re.sub(r"\(.*?\)", "", linha.split(":", 1)[1] if ":" in linha else linha)
            for parte in re.split(r"\s+e\s+", linha.strip()):
                saida |= pares(tabela, _cadeia(parte))
    return saida


def hierarquias_da_documentacao() -> set[tuple]:
    saida = set()
    for cabecalho, corpo in re.findall(r"^### (.+?)\n(.*?)(?=^### |^## |\Z)", DOC_MODELO.read_text(encoding="utf-8"),
                                       re.MULTILINE | re.DOTALL):
        dim = re.match(r"(dim_\w+)", cabecalho).group(1) if cabecalho.startswith("dim_") else None
        for paragrafo in corpo.split("\n\n"):
            if not paragrafo.startswith(("Hierarquia", "Hierarquias")):
                continue
            alvo = re.search(r"Hierarquias? de `(dim_\w+)`", paragrafo)
            for trecho in re.findall(r"`([^`]*≤[^`]*)`", paragrafo):
                saida |= pares(alvo.group(1) if alvo else dim, _cadeia(trecho))
    return saida


def test_hierarquias_iguais_no_relatorio_no_ddl_e_na_documentacao():
    declaradas = pares_declarados()
    assert hierarquias_do_relatorio() == declaradas
    assert hierarquias_do_ddl() == declaradas
    assert hierarquias_da_documentacao() == declaradas


def test_hierarquias_valem_nos_dados(con):
    v = q.hierarquias(con)
    assert v.status == q.OK, v.detalhe[v.detalhe.violacoes > 0]
    assert len(v.detalhe) == len(pares_declarados())


def test_faixa_escolar_nao_cabe_em_grupo_etario(con):
    # por isso a dimensão Idade tem três hierarquias paralelas e não idade ≤ faixa escolar ≤ grupo etário:
    # 11 a 14 anos tem criança (11) e adolescente; 30 ou mais tem adulto e idoso
    assert q.violacoes_hierarquia(con, "dim_idade", ("faixa_escolar",), ("grupo_etario",)) == 2


def test_violacao_de_hierarquia_e_detectada():
    c = duckdb.connect()
    c.execute("CREATE SCHEMA dw")
    c.execute("CREATE TABLE dw.dim_x (filho VARCHAR, pai VARCHAR)")
    c.execute("INSERT INTO dw.dim_x VALUES ('a', 'P'), ('a', 'Q'), ('b', 'P'), (NULL, 'R')")
    v = q.hierarquias(c, {"dim_x": [[("filho",), ("pai",)]]})
    assert v.status == q.FALHA and v.detalhe.violacoes.sum() == 1


# ----------------------------------------------------------------------------- conformidade

def test_rollups_encolhidos_compartilham_o_atributo_conformado(con):
    comum = {("dim_data", "dim_ano_letivo"): {"ano"}, ("dim_data", "dim_tempo"): {"ano", "mes"},
             ("dim_serie", "dim_etapa"): {"etapa", "nivel"}, ("dim_setor_censitario", "dim_territorio"): {"distrito"},
             ("dim_idade", "dim_faixa_etaria"): {"faixa_ibge"}}
    assert set(comum) == ROLLUPS
    for (fina, agregada), atributos in comum.items():
        assert atributos <= set(colunas(con, fina)) & set(colunas(con, agregada)), (fina, agregada)


def test_conformidade_nos_dados(con):
    v = q.conformidade(con)
    assert v.detalhe.loc[v.detalhe.falha_do_modelo, "violacoes"].sum() == 0
    assert v.status == q.ALERTA            # o 'Distrito Sintético' do Censo de teste não existe na SME
