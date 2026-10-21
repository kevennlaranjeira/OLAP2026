# Guia do grupo: acessar, usar, modificar e testar o projeto

Este guia é para quem entrou agora no trabalho e quer ler o relatório, sugerir mudanças, mexer no código ou rodar os testes. Dá para seguir do começo ao fim ou pular direto para a parte que interessa. As partes 1 a 4 não exigem instalar nada.

| Quero... | Vá para |
|---|---|
| achar o texto-fonte do relatório | [Resposta rápida](#resposta-rápida-onde-está-o-bruto-do-relatório) |
| entrar no repositório | [1. Acesso](#1-acesso-ao-repositório) |
| entender onde fica cada coisa | [2. Mapa do repositório](#2-mapa-do-repositório) |
| sugerir uma mudança sem instalar nada | [3. Sugerir mudanças pelo navegador](#3-sugerir-mudanças-pelo-navegador) |
| editar o relatório e ver o PDF | [4. Editar o relatório](#4-editar-o-relatório-latex) |
| mexer nos slides | [5. Editar a apresentação](#5-editar-a-apresentação) |
| rodar o projeto no meu computador | [6. Preparar o computador](#6-preparar-o-computador) e [8. Rodar o pipeline](#8-rodar-o-pipeline-com-os-dados-reais) |
| conferir se não quebrei nada | [7. Testes](#7-rodar-os-testes) |
| mandar minhas mudanças | [9. Fluxo de trabalho em equipe](#9-fluxo-de-trabalho-em-equipe) |
| resolver um erro | [10. Problemas comuns](#10-problemas-comuns) |

## Resposta rápida: onde está o "bruto" do relatório

O relatório é escrito em LaTeX. O texto-fonte é o arquivo [`docs/relatorio/relatorio-projeto1.tex`](relatorio/relatorio-projeto1.tex). Os desenhos dos esquemas estrela e da constelação ficam separados, em [`docs/relatorio/esquemas/`](relatorio/esquemas/), um arquivo `.tex` por desenho. O PDF pronto é o [`docs/relatorio/relatorio-projeto1.pdf`](relatorio/relatorio-projeto1.pdf).

No GitHub, o caminho é: repositório > pasta `docs` > pasta `relatorio` > `relatorio-projeto1.tex`. O botão **Raw** mostra o texto puro, e o ícone de download baixa o arquivo.

Para indicar alterações, há três jeitos, do mais simples ao mais completo:

1. abrir uma **Issue** dizendo o que mudar e onde (seção, página ou trecho);
2. editar o `.tex` direto no navegador e propor a mudança como **pull request**;
3. editar no computador ou no Overleaf, compilar o PDF e mandar os dois arquivos.

As três estão explicadas nas partes 3 e 4.

## 1. Acesso ao repositório

O repositório é privado: https://github.com/kevennlaranjeira/OLAP2026. Só entra quem foi convidado.

### Quem ainda não tem acesso

1. Crie uma conta em https://github.com, se ainda não tiver.
2. Mande ao Kevenn o seu nome de usuário do GitHub (aparece no canto superior direito, ao clicar na foto) ou o e-mail da conta.
3. O convite chega por e-mail. Também dá para aceitar em https://github.com/kevennlaranjeira/OLAP2026/invitations, já logado.
4. Depois de aceitar, o repositório aparece em https://github.com/kevennlaranjeira/OLAP2026. Se a página der erro 404, o convite ainda não foi aceito ou foi feito para outra conta.

### Para o Kevenn convidar alguém

No repositório, vá em **Settings > Collaborators > Add people**, digite o usuário ou o e-mail e confirme. O convite vale por 7 dias; se expirar, é só mandar de novo. Num repositório de conta pessoal todo colaborador tem a mesma permissão: lê tudo, cria branches e pull requests e também consegue enviar direto para a `main` (a parte 9 explica por que é melhor não fazer isso).

## 2. Mapa do repositório

```
OLAP2026/
  README.md                      visão geral, resultados e índice da documentação
  docs/
    relatorio/
      relatorio-projeto1.tex     texto-fonte do relatório (LaTeX)
      relatorio-projeto1.pdf     relatório compilado, o arquivo de entrega
      esquemas/*.tex             desenhos das estrelas e da constelação (TikZ)
    apresentacao/
      gerar.js                   script que gera os slides
      apresentacao-projeto1.pptx slides gerados (21 slides)
    modelagem/                   os mesmos esquemas em PNG e num PDF separado
    01 a 11 *.md                 documentação técnica (fontes, fluxo, modelo, consultas, decisões...)
    relatorios/qualidade.md      resultado das 14 verificações na última carga real
  src/dw_sme/                    código do pipeline (Python)
    sql/ddl/                     criação das tabelas do data warehouse
    sql/consultas/               as 8 consultas OLAP, uma por arquivo
  tests/                         testes automáticos
  .github/workflows/testes.yml   o que o GitHub roda a cada envio (CI)
  pyproject.toml                 dependências e configuração do Python
```

A pasta `data/`, onde ficam os dados baixados e o banco, nunca vai para o GitHub: cada um gera a sua (parte 8).

Os documentos que mais ajudam quem chega agora:

- [08 Pendências da entrega](08-pendencias-da-entrega.md): o que falta e quem apresenta cada bloco;
- [03 Modelo dimensional](03-modelo-dimensional.md): grãos, dimensões, fatos e hierarquias, em texto corrido;
- [05 Consultas](05-consultas.md): as oito consultas com pergunta, justificativa e resultado real;
- [06 Decisões](06-decisoes.md): cada decisão de projeto com a alternativa descartada.

## 3. Sugerir mudanças pelo navegador

### Abrir uma Issue

Serve para apontar um problema ou pedir uma mudança sem mexer no arquivo.

1. No repositório, aba **Issues > New issue**.
2. No título, resuma a mudança: "Relatório 1.3: trocar a ordem das fontes".
3. Na descrição, diga onde (seção, página do PDF ou o trecho copiado) e o que deve ficar no lugar.
4. Clique em **Create**. Quem for fazer a mudança fecha a Issue depois.

### Editar o arquivo direto no GitHub

É o caminho mais curto para correções de texto: o próprio GitHub cria a branch e o pull request.

1. Abra o arquivo, por exemplo `docs/relatorio/relatorio-projeto1.tex`.
2. Clique no lápis (**Edit this file**), no canto superior direito do arquivo.
3. Faça a alteração. `Ctrl+F` ajuda a achar o trecho.
4. Clique em **Commit changes...**.
5. Escreva uma mensagem curta, como `docs(relatorio): corrigir grafia na seção 1.3`.
6. Marque **Create a new branch for this commit and start a pull request** e clique em **Propose changes**.
7. Na tela seguinte, revise e clique em **Create pull request**.

O GitHub roda os testes sozinho (ver [parte 9](#9-fluxo-de-trabalho-em-equipe)). Enquanto o PDF não for recompilado, ele continua com o texto antigo. Avise no pull request ou recompile você mesmo (parte 4).

### Comentar uma linha num pull request

Em qualquer pull request, aba **Files changed**: passe o mouse sobre a linha, clique no **+** azul e escreva o comentário. Para propor o texto exato, clique no ícone de sugestão (o de "±") e reescreva a linha. Quem abriu o pull request aceita com um clique.

## 4. Editar o relatório (LaTeX)

### Onde fica cada parte do `.tex`

Os números de linha são aproximados e mudam conforme o texto cresce. Use `Ctrl+F` com o título da seção.

| Parte do relatório | Procure por | Linha aproximada |
|---|---|---|
| curso e data da capa | `\newcommand{\curso}` e `\newcommand{\dataentrega}` | 25 |
| capa (instituição, integrantes) | `\begin{titlepage}` | 59 |
| 1.1 Tema geral | `\subsection{Tema geral}` | 97 |
| 1.2 Assuntos de interesse | `\subsection{Assuntos de interesse` | 107 |
| 1.3 Fontes de dados | `\subsection{Fontes de dados}` | 138 |
| 1.4 Grão, dimensões e fatos | `\subsection{Grão, dimensões` | 157 |
| 1.5 Dimensões e atributos (uma tabela por dimensão) | `\subsection{Dimensões e atributos}` | 177 |
| 1.6 Fatos e aditividade | `\subsection{Fatos}` | 330 |
| 1.7 Povoamento e integração | `\subsection{Povoamento e integração}` | 361 |
| 2 Esquemas estrela e constelação | `\section{Esquemas}` | 431 |
| 3 Consultas (C1 a C8) | `\section{Consultas}` | 572 |
| Apêndice: dados reais | `\section{Viabilidade` | 650 |

Os desenhos não estão no `.tex` principal: cada esquema é puxado de `esquemas/` com `\input{esquemas/estrela-fila}` e similares. Para mudar uma caixa ou uma ligação, edite o arquivo da pasta `esquemas/`. O estilo comum (fonte, bordas, espessura) está em `esquemas/estilo.tex`.

### Cuidados com o LaTeX

- `%` começa um comentário: o resto da linha some do PDF. Para escrever o símbolo, use `\%` (como em `34\%`).
- `&` separa colunas de tabela, e `\\` termina a linha da tabela. Num texto comum, escreva `\&`.
- Acentos podem ser digitados direto (é, ç, ã); o arquivo é UTF-8.
- Hierarquias usam a macro `\hier{...}` com `\leq`, por exemplo `\hier{\text{distrito} \leq \text{DRE}}`. Os testes leem essas macros (parte 7).

### Compilar no Overleaf (sem instalar nada)

1. Entre em https://www.overleaf.com e crie um projeto em branco (**New Project > Blank Project**).
2. Apague o `main.tex` que ele cria.
3. Em **Upload**, envie `relatorio-projeto1.tex`. Depois crie uma pasta chamada exatamente `esquemas` e envie para ela os 7 arquivos de `docs/relatorio/esquemas/`.
4. No **Menu** (canto superior esquerdo), troque **Compiler** para **XeLaTeX** e **Main document** para `relatorio-projeto1.tex`. Com pdfLaTeX não compila, porque o relatório usa o pacote `fontspec`.
5. Clique em **Recompile**.

O Overleaf gratuito não sincroniza com o GitHub. Quando terminar, baixe o `.tex` alterado (e o PDF, em **Download PDF**) e envie para o repositório pelo navegador (**Add file > Upload files** na pasta `docs/relatorio`, marcando a opção de criar branch e pull request) ou pelo fluxo da parte 9.

### Compilar no computador

Instale o MiKTeX (Windows, https://miktex.org) ou o TeX Live (Linux e macOS). Na primeira compilação o MiKTeX pede para baixar pacotes que faltam; aceite. Depois, dentro de `docs/relatorio`:

```bash
xelatex relatorio-projeto1.tex
```

Rode o comando **duas vezes**: a segunda passada acerta o índice e as referências. Os arquivos auxiliares (`.aux`, `.log`, `.toc`, `.out`) ficam fora do Git pelo `.gitignore`.

### Antes de mandar

Mande sempre o `.tex` e o `.pdf` juntos, no mesmo commit. O PDF é o arquivo de entrega; se só o `.tex` mudar, o PDF do repositório fica desatualizado.

## 5. Editar a apresentação

Os slides são gerados pelo script [`docs/apresentacao/gerar.js`](apresentacao/gerar.js). As figuras dos esquemas vêm de `docs/modelagem/`. Cada slide tem, nas notas, quem apresenta e o tempo previsto, e o slide 2 (roteiro) é montado a partir dessas notas.

### Pelo script (recomendado)

Exige o Node.js (https://nodejs.org). Na pasta do projeto:

```bash
npm install pptxgenjs
```

```bash
node docs/apresentacao/gerar.js
```

O texto de cada slide está no `gerar.js`, em blocos marcados com comentários como `// 7. fontes`. Em `novoSlide(titulo, bloco, minutos, notas)`, o terceiro argumento é o tempo previsto do slide e o quarto são as notas de fala. O `npm install` cria `node_modules/`, `package.json` e `package-lock.json` na pasta do projeto; os três já estão no `.gitignore` e não vão para o GitHub.

### Direto no PowerPoint

Também funciona, com duas ressalvas:

- se alguém rodar o `gerar.js` depois, as edições feitas à mão se perdem, porque o script gera o arquivo do zero;
- os testes conferem que existem 21 slides, que toda nota começa com `Apresenta: <nome> (bloco N de 4). Tempo previsto: X min.` e que os quatro blocos somam o mesmo tempo. Mantenha esse formato nas notas.

Combine com o grupo qual dos dois caminhos usar até a entrega.

## 6. Preparar o computador

Esta parte só é necessária para rodar os testes ou o pipeline no seu computador.

| Programa | Para quê | Onde baixar |
|---|---|---|
| Git | baixar e enviar o projeto | https://git-scm.com |
| Python 3.11 ou mais novo | rodar o pipeline e os testes | https://www.python.org/downloads (no Windows, marque **Add python.exe to PATH**) |
| 7-Zip (opcional) | abrir o pacote `.rar` dos microdados de 2019 a 2021 | https://www.7-zip.org |
| VS Code (opcional) | editar arquivos | https://code.visualstudio.com |
| GitHub Desktop (opcional) | usar o Git sem linha de comando | https://desktop.github.com |

Os comandos abaixo são para o PowerShell ou o Git Bash do Windows. No Linux e no macOS, troque `.venv/Scripts/python` por `.venv/bin/python`.

### Baixar o projeto (clonar)

Escolha uma pasta e rode:

```bash
git clone https://github.com/kevennlaranjeira/OLAP2026.git
```

Na primeira vez, o Git abre o navegador para você entrar na sua conta do GitHub. Depois:

```bash
cd OLAP2026
```

Pelo GitHub Desktop: **File > Clone repository**, aba **GitHub.com**, escolha `kevennlaranjeira/OLAP2026`.

### Criar o ambiente do Python e instalar o projeto

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python -m pip install -e ".[dev]"
```

O primeiro comando cria a pasta `.venv` (fora do Git), com um Python só do projeto. O segundo instala o projeto e as ferramentas de teste. Isso é feito uma vez só; depois, para atualizar o projeto com o que os outros enviaram:

```bash
git pull
```

## 7. Rodar os testes

Os testes não precisam de internet nem dos dados reais, e levam cerca de 1 minuto.

```bash
.venv/Scripts/python -m pytest
```

O resultado esperado termina com algo como `482 passed`. Qualquer `failed` ou `error` indica um problema.

Para rodar só uma parte:

| Comando | O que roda |
|---|---|
| `.venv/Scripts/python -m pytest tests/test_coerencia.py` | coerência entre README, docs, relatório e slides |
| `.venv/Scripts/python -m pytest tests/test_modelo.py` | desenhos e hierarquias do relatório contra o banco |
| `.venv/Scripts/python -m pytest tests/test_funcionamento.py` | o pipeline pela linha de comando e em volume |
| `.venv/Scripts/python -m pytest -k fila` | só os testes com "fila" no nome |
| `.venv/Scripts/python -m pytest -x` | para no primeiro erro |

E o lint, que o GitHub também roda:

```bash
.venv/Scripts/python -m ruff check src tests
```

### O que os testes conferem no relatório e nos slides

Reescrever um parágrafo do relatório não quebra teste. Os testes reclamam quando uma informação aparece em mais de um lugar e uma das cópias muda sozinha:

| Se você mudar... | Também precisa mudar | Teste que acusa |
|---|---|---|
| nome ou Nº USP de um integrante | README, `relatorio-projeto1.tex` e `gerar.js` | `test_integrantes_e_numeros_usp_iguais_em_todo_lugar` |
| o tipo de uma consulta (ex.: drill-down) | o arquivo SQL, `docs/05-consultas.md`, o título `\subsection{Consulta N: tipo}` e a tabela de consultas do `gerar.js` | `test_consultas_iguais_na_documentacao_no_relatorio_e_nos_slides` |
| uma hierarquia (`\hier{...}`) | o DDL em `src/dw_sme/sql/ddl/` e `docs/03-modelo-dimensional.md` | `test_hierarquias_iguais_no_relatorio_no_ddl_e_na_documentacao` |
| uma caixa ou ligação de um esquema | o DDL (as caixas mostram as colunas das tabelas) | `test_caixas_do_desenho_batem_com_o_ddl` e vizinhos em `test_modelo.py` |
| a matriz de barramento | o DDL e `docs/modelagem/modelagem.tex` | `test_matriz_de_barramento_bate_com_o_ddl` |
| uma contagem citada em vários lugares (5 fatos, 14 dimensões, 14 verificações, 23 decisões) | README, `docs/` e relatório, que citam o mesmo número | `test_cinco_fatos_quatorze_dimensoes_vinte_e_sete_chaves_em_todo_lugar`, `test_quatorze_verificacoes_documentadas`, `test_decisoes_numeradas_em_sequencia` |
| um link entre documentos | o arquivo para o qual ele aponta | `test_links_internos_apontam_para_arquivos_que_existem` |
| o número de slides ou o tempo de um slide | `docs/08-pendencias-da-entrega.md` e os tempos dos outros blocos | `test_vinte_e_um_slides_em_quatro_blocos` e `test_todos_apresentam_com_o_mesmo_tempo` |

Preencher o curso e a data na capa não quebra nada. Já deixar no texto um marcador de pendência (um nome entre colchetes no lugar de um integrante, uma anotação de tarefa em maiúsculas ou texto falso de preenchimento) faz o teste `test_nenhum_texto_pendente_esquecido` falhar, de propósito. A lista exata do que ele procura está no próprio teste, em `tests/test_coerencia.py`.

Quando um teste falha, a última linha da mensagem diz o arquivo e o que não bateu. Se a mudança foi intencional (por exemplo, o grupo decidiu mudar uma hierarquia), mude também os outros lugares da tabela acima. Se não sabe por que falhou, mande a mensagem no grupo.

## 8. Rodar o pipeline com os dados reais

Opcional: o relatório e os slides já têm os números da carga real. Rode se quiser conferir os resultados ou explorar o banco.

### Versão rápida: 2022 a 2024

Baixa cerca de 220 MB, carrega os cinco fatos, inclusive a população do Censo 2022, e não precisa do 7-Zip. Na máquina do Kevenn o processo inteiro, com o download, levou 2 minutos.

```bash
.venv/Scripts/python -m dw_sme tudo --anos 2022-2024
```

### Versão completa: 2015 a 2024

Baixa cerca de 650 MB, precisa do 7-Zip e de uns 3,5 GB livres. Na máquina do Kevenn, com os arquivos já baixados, a carga levou 3,5 minutos e o processo inteiro uns 10.

```bash
.venv/Scripts/python -m dw_sme tudo
```

### O que sai

O comando `tudo` executa cinco etapas em sequência: baixar, preparar, carregar, verificar e consultar. Ao final:

| Arquivo | O que é |
|---|---|
| `data/dw/dw_sme.duckdb` | o data warehouse (banco DuckDB) |
| `data/relatorios/qualidade.md` | as 14 verificações, cada uma com OK, ALERTA ou FALHA |
| `data/relatorios/consultas/*.csv` | o resultado de cada uma das 8 consultas |

ALERTA não é erro: indica um defeito conhecido das fontes, medido e documentado (ver [04 Integração e qualidade](04-integracao-e-qualidade.md)). FALHA indica problema na carga, e o comando termina com código 1. Para rodar uma etapa só, ou abrir o banco, veja [07 Como executar](07-como-executar.md#consultando-o-banco).

## 9. Fluxo de trabalho em equipe

A `main` é a versão que vai para a entrega. A sugestão é que ninguém envie direto para ela: cada mudança vai numa branch e entra por pull request, para o GitHub rodar os testes e outra pessoa do grupo olhar antes.

### 1. Atualize a sua cópia

```bash
git switch main
```

```bash
git pull
```

### 2. Crie uma branch

Use o seu nome e o assunto no nome da branch:

```bash
git switch -c thiago/ajuste-secao-fontes
```

### 3. Faça as mudanças e confira

Depois de editar, rode os testes e o lint:

```bash
.venv/Scripts/python -m pytest
```

```bash
.venv/Scripts/python -m ruff check src tests
```

### 4. Registre a mudança (commit)

Veja o que mudou com `git status`, adicione os arquivos e escreva uma mensagem que diga o que mudou:

```bash
git add docs/relatorio/relatorio-projeto1.tex docs/relatorio/relatorio-projeto1.pdf
```

```bash
git commit -m "docs(relatorio): reescrever a justificativa da consulta 6"
```

O projeto usa o padrão `tipo(área): descrição`. Os tipos mais usados aqui: `docs` (relatório, slides, documentação), `fix` (correção), `feat` (algo novo no pipeline), `test` (testes).

### 5. Envie e abra o pull request

```bash
git push -u origin thiago/ajuste-secao-fontes
```

O terminal mostra um link; ou abra o repositório no GitHub, onde aparece a faixa amarela **Compare & pull request**. Descreva o que mudou e clique em **Create pull request**.

### 6. Espere o CI

Na página do pull request aparece a verificação **testes**, que roda o lint e os 482 testes em Python 3.11 e 3.13 e exige cobertura de pelo menos 85%. Um ✓ verde quer dizer que passou; um ✗ vermelho, que algo falhou. Clique em **Details** para ver qual teste falhou e corrija na mesma branch: um novo `git push` roda tudo de novo.

### 7. Junte na `main`

Com o ✓ verde e alguém do grupo de acordo, clique em **Merge pull request**. Depois, **Delete branch**.

No GitHub Desktop os passos são os mesmos: **Current branch > New branch**, depois **Commit to ...**, **Push origin** e **Create Pull Request**.

## 10. Problemas comuns

| Sintoma | O que fazer |
|---|---|
| a página do repositório dá erro 404 | o convite não foi aceito, ou você está logado com outra conta (parte 1) |
| `git push` pede senha ou dá "Permission denied" | o GitHub não aceita mais senha no terminal. No Windows, o Git abre o navegador para login; se não abrir, instale o GitHub CLI e rode `gh auth login` |
| `python` não é reconhecido | o Python não está no PATH: reinstale marcando **Add python.exe to PATH** |
| `.venv/Scripts/python` não existe | rode `python -m venv .venv` dentro da pasta do projeto |
| o Overleaf dá erro de `fontspec` | troque o compilador para XeLaTeX (parte 4) |
| o PDF compilado está sem índice ou com "??" | compile uma segunda vez |
| `git pull` fala em conflito | duas pessoas mudaram a mesma linha. Abra o arquivo, procure os marcadores `<<<<<<<`, `=======` e `>>>>>>>`, deixe só a versão certa, salve, e rode `git add` e `git commit`. Na dúvida, peça ajuda antes |
| `requer o 7-Zip instalado` | instale o 7-Zip ou rode com `--anos 2022-2024` |
| erro com `ResourceInUseException` ou `Conversion Error` vindo do DuckDB | você tem o DuckDB 2.0, que o projeto não aceita (ele erra uma das somas). Rode de novo `.venv/Scripts/python -m pip install -e ".[dev]"`, que instala a versão 1.x |
| algum teste falhou depois de mudar o relatório | veja a tabela da parte 7 |

Outros erros do pipeline estão em [07 Como executar](07-como-executar.md#problemas-comuns).
