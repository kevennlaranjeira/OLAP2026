// Gera docs/apresentacao/apresentacao-projeto1.pptx.
// Requer Node e pptxgenjs:  npm install pptxgenjs  e depois  node docs/apresentacao/gerar.js
// As figuras dos esquemas vêm de docs/modelagem/ (geradas por figuras.tex na mesma pasta).
// Todos os números dos slides vêm da carga com os dados reais documentada em docs/05-consultas.md.
// Cada slide declara quem apresenta e o tempo previsto; o slide de roteiro soma os tempos por bloco.
"use strict";
const fs = require("fs");
const path = require("path");
const pptxgen = require(process.env.PPTXGENJS || "pptxgenjs");

const AQUI = __dirname;
const FIG = (nome) => path.join(AQUI, "..", "modelagem", nome);

const ESCURO = "183D3D";
const TINTA = "E7F0ED";
const AREIA = "F6EBD3";
const DESTAQUE = "D98E04";
const DESTAQUE_TEXTO = "8A5A00";
const TEXTO = "1E2B2B";
const SUAVE = "56676A";
const BRANCO = "FFFFFF";
const TITULO = "Cambria";
const CORPO = "Calibri";

const INTEGRANTES = [
  ["Kevenn Laranjeira de Oliveira", "18046529"],
  ["Thiago Rodrigues Gouveia da Silva", "18066911"],
  ["Daniel Afonso Borges dos Santos", "12608581"],
  ["Luís Antônio Arruda Soares", "12559486"],
];
const BLOCO = {
  1: "Kevenn Laranjeira de Oliveira",
  2: "Thiago Rodrigues Gouveia da Silva",
  3: "Daniel Afonso Borges dos Santos",
  4: "Luís Antônio Arruda Soares",
};
const ASSUNTO_DO_BLOCO = {
  1: "Motivação: o problema, as perguntas do gestor, a escolha de São Paulo e os cinco assuntos de interesse.",
  2: "Fontes de dados, integração, problemas nos dados, grão e aditividade e a estrela Matrícula.",
  3: "Estrelas Fila, Desfecho, Ocupação de Turma e População; constelação de fatos.",
  4: "Consultas OLAP, resultados com os dados reais e decisões de projeto.",
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,33 x 7,5 polegadas
pres.title = "Rede Municipal Paulistana: oferta escolar e demanda não atendida";
pres.author = "Grupo 7, SCC0245";

let numero = 0;
const slidesDoBloco = { 1: [], 2: [], 3: [], 4: [] };
const minutosDoBloco = { 1: 0, 2: 0, 3: 0, 4: 0 };
const virgula = (n) => String(n).replace(".", ",");

function novoSlide(titulo, bloco, minutos, notas, escuro = false) {
  const s = pres.addSlide();
  numero += 1;
  slidesDoBloco[bloco].push(numero);
  minutosDoBloco[bloco] += minutos;
  s.background = { color: escuro ? ESCURO : BRANCO };
  if (titulo) {
    s.addText(titulo, {
      x: 0.6, y: 0.35, w: 12.1, h: 0.85, fontFace: TITULO, fontSize: 30, bold: true,
      color: escuro ? BRANCO : ESCURO, margin: 0, isTextBox: true, valign: "middle",
    });
  }
  if (numero > 1) {
    s.addText(String(numero), {
      x: 12.2, y: 7.0, w: 0.6, h: 0.3, fontFace: CORPO, fontSize: 10, color: escuro ? "B9CFC9" : SUAVE,
      align: "right", margin: 0, isTextBox: true,
    });
  }
  s.addNotes(`Apresenta: ${BLOCO[bloco]} (bloco ${bloco} de 4). Tempo previsto: ${virgula(minutos)} min.\n\n${notas}`);
  return s;
}

function cartao(s, x, y, w, h, titulo, corpo, opcoes = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, fill: { color: opcoes.fundo || TINTA }, line: { color: opcoes.fundo || TINTA }, rectRadius: 0.08,
  });
  s.addText(titulo, {
    x: x + 0.25, y: y + 0.18, w: w - 0.5, h: opcoes.altTitulo || 0.45, fontFace: CORPO, fontSize: opcoes.tamTitulo || 17,
    bold: true, color: ESCURO, margin: 0, isTextBox: true, valign: "top",
  });
  s.addText(corpo, {
    x: x + 0.25, y: y + (opcoes.corpoY || 0.68), w: w - 0.5, h: h - (opcoes.corpoY || 0.68) - 0.17,
    fontFace: CORPO, fontSize: opcoes.tamCorpo || 13.5,
    color: TEXTO, margin: 0, isTextBox: true, valign: "top", paraSpaceAfter: 4,
  });
}

function circulo(s, x, y, rotulo, d = 0.55) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: DESTAQUE }, line: { color: DESTAQUE } });
  s.addText(rotulo, {
    x, y, w: d, h: d, fontFace: CORPO, fontSize: 15, bold: true, color: BRANCO, align: "center",
    valign: "middle", margin: 0, isTextBox: true,
  });
}

function itens(lista, tam = 15) {
  return lista.map((t, i) => ({
    text: t, options: { bullet: true, breakLine: i < lista.length - 1, fontSize: tam, paraSpaceAfter: 8 },
  }));
}

function fonte(s, texto) {
  s.addText(texto, {
    x: 0.6, y: 6.95, w: 11.2, h: 0.35, fontFace: CORPO, fontSize: 10, color: SUAVE, italic: true,
    margin: 0, isTextBox: true,
  });
}

function tabela(s, cabecalho, linhas, opcoes) {
  const cab = cabecalho.map((t) => ({ text: t, options: { bold: true, color: BRANCO, fill: { color: ESCURO } } }));
  const corpo = linhas.map((l, i) => l.map((t, j) => ({
    text: t, options: { fill: { color: i % 2 ? BRANCO : TINTA }, bold: Boolean(opcoes.primeiraEmNegrito && j === 0) },
  })));
  s.addTable([cab, ...corpo], {
    fontFace: CORPO, color: TEXTO, border: { type: "solid", color: "C9D8D3", pt: 0.75 }, valign: "middle", ...opcoes.tabela,
  });
}

// largura / altura lidas do cabeçalho do PNG, para a figura nunca sair distorcida
function proporcao(arquivo) {
  const cab = fs.readFileSync(FIG(arquivo)).subarray(16, 24);
  return cab.readUInt32BE(0) / cab.readUInt32BE(4);
}

// cabe a figura na caixa (x, y, w, hMax) sem distorcer
function figura(s, arquivo, x, y, w, hMax, descricao) {
  const p = proporcao(arquivo);
  const largura = Math.min(w, hMax * p);
  s.addImage({ path: FIG(arquivo), x, y, w: largura, h: largura / p, altText: descricao });
}

// slide de um esquema estrela largo: figura na largura do slide, leitura do esquema em duas colunas embaixo
function estrela(titulo, arquivo, descricao, lista, notas) {
  const s = novoSlide(titulo, 3, 1, notas);
  const p = proporcao(arquivo);
  const largura = Math.min(12.1, 4.1 * p);
  const altura = largura / p;
  s.addImage({ path: FIG(arquivo), x: 0.6 + (12.1 - largura) / 2, y: 1.3, w: largura, h: altura, altText: descricao });
  const y = 1.3 + altura + 0.3;
  const meio = Math.ceil(lista.length / 2);
  [lista.slice(0, meio), lista.slice(meio)].forEach((coluna, i) => {
    s.addText(itens(coluna, 15).map((t) => ({ ...t, options: { ...t.options, paraSpaceAfter: 4 } })), {
      x: 0.6 + i * 6.15, y, w: 5.95, h: 6.9 - y, fontFace: CORPO, color: TEXTO, margin: 0, isTextBox: true, valign: "top",
    });
  });
  return s;
}

// ================================================================== bloco 1: motivação

// ------------------------------------------------------------------ 1. capa
{
  const s = novoSlide(null, 1, 0.5,
    "Abertura. Apresentar o grupo, a disciplina e o tema: política pública municipal de educação. " +
    "Dizer em uma frase a pergunta do trabalho: onde existe fila por vaga, onde existe oferta, se a oferta está cheia, " +
    "quantas crianças moram em cada lugar e o que acontece com quem consegue a vaga.", true);
  s.addText("SCC0245 Processamento Analítico de Dados · Primeiro Trabalho Prático · Grupo 7", {
    x: 0.8, y: 0.7, w: 11.5, h: 0.4, fontFace: CORPO, fontSize: 15, color: "B9CFC9", margin: 0, isTextBox: true,
  });
  s.addText("Rede Municipal Paulistana: oferta escolar e demanda não atendida", {
    x: 0.8, y: 1.45, w: 11.0, h: 1.9, fontFace: TITULO, fontSize: 40, bold: true, color: BRANCO, margin: 0,
    isTextBox: true, valign: "top",
  });
  s.addText("Um data warehouse para decidir onde abrir vagas, com dados abertos da SME-SP e do IBGE", {
    x: 0.8, y: 3.35, w: 11.0, h: 0.5, fontFace: CORPO, fontSize: 18, italic: true, color: "F2C46B", margin: 0,
    isTextBox: true,
  });
  s.addText(INTEGRANTES.map(([nome, nusp], i) => ({
    text: `${nome}   ${nusp}`, options: { breakLine: i < INTEGRANTES.length - 1, fontSize: 16, paraSpaceAfter: 6 },
  })), { x: 0.8, y: 4.45, w: 7.5, h: 1.8, fontFace: CORPO, color: BRANCO, margin: 0, isTextBox: true, valign: "top" });
  s.addText("Profa. Dra. Cristina Dutra de Aguiar\nICMC-USP, São Carlos", {
    x: 8.6, y: 5.45, w: 4.0, h: 0.8, fontFace: CORPO, fontSize: 14, color: "B9CFC9", align: "right", margin: 0,
    isTextBox: true,
  });
}

// ------------------------------------------------------------------ 2. roteiro (preenchido no fim)
const roteiro = novoSlide("Roteiro: quatro integrantes, tempos iguais", 1, 0.5,
  "Mostrar a divisão: cada integrante apresenta um bloco, com o mesmo tempo previsto. " +
  "Os quatro blocos seguem a ordem pedida no enunciado: motivação; fontes; esquemas estrela e constelação; consultas e decisões.");

// ------------------------------------------------------------------ 3. problema
{
  const s = novoSlide("O problema: falta de vaga na educação infantil", 1, 1,
    "Motivação. A falta de vaga em creche foi por anos o principal problema de acesso da educação infantil paulistana. " +
    "O PNE (Lei 13.005/2014), Meta 1, pede creche para pelo menos metade das crianças de até 3 anos e pré-escola universal. " +
    "A prefeitura publica a fila por distrito para dar transparência. Os números do slide são da nossa carga com os dados reais: " +
    "a fila de creche em junho caiu de 124.741 crianças em 2015 para 3.633 em 2024. O gestor ainda precisa saber onde " +
    "a oferta está cheia e quantas crianças moram em cada região, e é isso que o modelo junta.");
  s.addText(itens([
    "A falta de vaga em creche foi por anos o principal problema de acesso da educação infantil em São Paulo.",
    "PNE (Lei 13.005/2014), Meta 1: creche para ao menos metade das crianças de até 3 anos; pré-escola universal.",
    "Para decidir onde abrir vagas, o gestor precisa cruzar fila, matrícula, ocupação das turmas e população, que estão em bases diferentes.",
  ], 16), { x: 0.6, y: 1.5, w: 6.4, h: 4.6, fontFace: CORPO, color: TEXTO, margin: 0, isTextBox: true, valign: "top" });
  cartao(s, 7.5, 1.5, 5.2, 2.3, "Fila de creche em junho de 2015", "");
  s.addText("124.741 crianças", {
    x: 7.75, y: 2.2, w: 4.8, h: 1.0, fontFace: TITULO, fontSize: 34, bold: true, color: DESTAQUE_TEXTO, margin: 0,
    isTextBox: true,
  });
  s.addText("34% da demanda de creche fora da rede", { x: 7.75, y: 3.15, w: 4.8, h: 0.4, fontFace: CORPO, fontSize: 14,
    color: TEXTO, margin: 0, isTextBox: true });
  cartao(s, 7.5, 4.05, 5.2, 2.3, "Fila de creche em junho de 2024", "");
  s.addText("3.633 crianças", {
    x: 7.75, y: 4.75, w: 4.8, h: 1.0, fontFace: TITULO, fontSize: 34, bold: true, color: ESCURO, margin: 0,
    isTextBox: true,
  });
  s.addText("1% da demanda de creche fora da rede", { x: 7.75, y: 5.7, w: 4.8, h: 0.4, fontFace: CORPO, fontSize: 14,
    color: TEXTO, margin: 0, isTextBox: true });
  fonte(s, "Fonte: Demanda Registrada e Matrículas (SME-SP); consulta 5 sobre a carga com os dados reais.");
}

// ------------------------------------------------------------------ 4. perguntas do gestor
{
  const s = novoSlide("Perguntas que o data warehouse responde", 1, 1,
    "Quem usa: Secretaria Municipal de Educação e as 13 Diretorias Regionais. Cada cartão é uma decisão real de política " +
    "pública e cita as consultas que a apoiam. Destacar que a capacidade das turmas não é publicada, então medimos a ocupação.");
  const perguntas = [
    ["Onde abrir vagas?", "Fila por distrito e DRE, fila contra matrícula e contra a população de 0 a 4 anos.", "C1 · C5 · C7"],
    ["Como a oferta é feita?", "Peso da rede conveniada e da jornada integral na creche e em cada DRE.", "C3 · C4"],
    ["Turma nova ou lugar ocioso?", "Alunos por turma em funcionamento, do município ao distrito.", "C8"],
    ["Fila e abandono andam juntos?", "Fila de creche e abandono no ensino fundamental, por DRE.", "C6"],
  ];
  perguntas.forEach(([t, c, q], i) => {
    const x = 0.6 + (i % 2) * 6.15;
    const y = 1.5 + Math.floor(i / 2) * 2.65;
    cartao(s, x, y, 5.95, 2.4, t, c, { tamTitulo: 19, tamCorpo: 15 });
    s.addText(q, { x: x + 0.25, y: y + 1.85, w: 5.4, h: 0.4, fontFace: CORPO, fontSize: 14, bold: true,
      color: DESTAQUE_TEXTO, margin: 0, isTextBox: true });
  });
}

// ------------------------------------------------------------------ 5. por que São Paulo
{
  const s = novoSlide("Por que São Paulo, e não São Carlos", 1, 1,
    "O enunciado temático prioriza São Carlos. Nossa primeira proposta foi dimensionar a oferta escolar por setor censitário " +
    "em São Carlos. Sem dado aberto de vaga nem de fila, a demanda não atendida teria de ser estimada, e o enunciado pede dados reais. " +
    "São Paulo publica o microdado de cada matrícula e a fila por distrito. O modelo não depende de São Paulo: matrícula, turma e desfecho " +
    "vêm do tipo de registro que qualquer sistema de gestão escolar mantém, e o Censo 2022 tem população por setor para todos os municípios.");
  cartao(s, 0.6, 1.5, 5.9, 3.2, "Primeira proposta: São Carlos",
    "Oferta escolar por setor censitário.\n\nSem dado aberto de vaga nem de fila, a demanda não atendida teria de ser estimada.",
    { tamCorpo: 16, tamTitulo: 19 });
  cartao(s, 6.8, 1.5, 5.9, 3.2, "Escolha: São Paulo",
    "A SME publica o microdado de cada matrícula e a fila de espera por distrito: demanda medida, não estimada.\n\n" +
    "13,4 milhões de matrículas de 2015 a 2024.", { tamCorpo: 16, tamTitulo: 19 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.0, w: 12.1, h: 1.55, fill: { color: AREIA },
    line: { color: AREIA }, rectRadius: 0.08 });
  s.addText([
    { text: "O modelo vale para São Carlos: ", options: { bold: true, color: DESTAQUE_TEXTO } },
    { text: "matrícula, turma e desfecho vêm do registro que todo sistema de gestão escolar mantém, e o Censo 2022 já tem a " +
      "população por setor censitário do município. Falta só a rede registrar e publicar a fila." },
  ], { x: 0.85, y: 5.1, w: 11.6, h: 1.35, fontFace: CORPO, fontSize: 16, color: TEXTO, margin: 0, isTextBox: true,
    valign: "middle" });
}

// ------------------------------------------------------------------ 6. assuntos de interesse
{
  const s = novoSlide("Cinco assuntos de interesse e por que importam", 1, 1,
    "Os cinco assuntos são os registrados na planilha do grupo, e cada um responde a uma parte da decisão de onde abrir vagas. " +
    "Matrícula é a oferta usada; fila é quem pediu e não conseguiu; ocupação diz se a oferta que existe está cheia; " +
    "população é a demanda potencial, que existe mesmo sem pedido; oferta por setor mostra onde e por qual rede a vaga é oferecida. " +
    "Quatro assuntos viram tabelas de fatos; a oferta por setor é respondida pelas dimensões Escola, Território e Setor Censitário. " +
    "O quinto processo, desfecho da matrícula, acompanha o que acontece depois do acesso.");
  tabela(s, ["Assunto de interesse", "Por que importa", "No modelo"], [
    ["Matrículas", "oferta efetivamente usada, com o perfil de cada aluno", "fato Matrícula"],
    ["Fila (demanda registrada)", "quem pediu vaga e não foi atendido", "fato Fila"],
    ["Capacidade e ocupação das turmas", "se a oferta existente está cheia: turma nova ou lugar ocioso", "fato Ocupação de Turma"],
    ["População em idade escolar", "demanda potencial, mesmo sem pedido de vaga", "fato População"],
    ["Oferta escolar por setor", "onde e por qual rede (direta ou conveniada) a vaga é oferecida", "dimensões Escola, Território, Setor"],
  ], { primeiraEmNegrito: true, tabela: { x: 0.6, y: 1.45, w: 12.1, colW: [3.3, 5.4, 3.4], fontSize: 15, rowH: 0.62 } });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.55, w: 12.1, h: 1.0, fill: { color: AREIA },
    line: { color: AREIA }, rectRadius: 0.08 });
  s.addText([
    { text: "Quinto processo: desfecho da matrícula. ", options: { bold: true, color: DESTAQUE_TEXTO } },
    { text: "Acompanha o que acontece depois do acesso: aprovação, reprovação, abandono e transferência." },
  ], { x: 0.85, y: 5.6, w: 11.6, h: 0.9, fontFace: CORPO, fontSize: 16, color: TEXTO, margin: 0, isTextBox: true,
    valign: "middle" });
}

// ================================================================== bloco 2: fontes, integração e grão

// ------------------------------------------------------------------ 7. fontes
{
  const s = novoSlide("Três fontes de dados reais e oficiais", 2, 1,
    "Duas fontes da SME no Portal de Dados Abertos da Prefeitura, com grão, formato e vocabulário diferentes, e o Censo 2022 do IBGE. " +
    "A fila tem sete formatos entre 2006 e 2026, e o significado das colunas numeradas muda com o formato. " +
    "O Censo traz a demanda potencial: quantas crianças moram em cada setor. Na carga real entraram 26.889 setores do município, " +
    "todos ligados a um distrito da SME.");
  const fontes = [
    ["Microdados de Matrículas", "SME-SP · anual",
      "Uma linha por vínculo aluno-turma: escola, turma, turno, série, idade, perfil, deficiência, datas e desfecho.\n\n13,4 milhões de matrículas de escolarização (2015-2024)."],
    ["Demanda Registrada e Matrículas", "SME-SP · trimestral, bimestral desde 2023",
      "Por distrito e etapa: matrículas, matrículas em processo e fila.\n\n44 planilhas × 96 distritos no recorte; sete formatos diferentes."],
    ["Censo Demográfico 2022", "IBGE · Agregados por Setores",
      "Pessoas residentes por setor censitário e grupo de idade (variáveis V01031 a V01041).\n\n26.889 setores do município, 11,4 milhões de moradores; referência 31/07/2022."],
  ];
  fontes.forEach(([t, sub, c], i) => {
    const x = 0.6 + i * 4.1;
    cartao(s, x, 1.5, 3.9, 5.0, t, "", { tamTitulo: 18, altTitulo: 0.8 });
    s.addText(sub, { x: x + 0.25, y: 2.55, w: 3.4, h: 0.6, fontFace: CORPO, fontSize: 13, bold: true,
      color: DESTAQUE_TEXTO, margin: 0, isTextBox: true, valign: "top" });
    s.addText(c, { x: x + 0.25, y: 3.25, w: 3.4, h: 3.1, fontFace: CORPO, fontSize: 14, color: TEXTO, margin: 0,
      isTextBox: true, valign: "top" });
  });
}

// ------------------------------------------------------------------ 8. integração
{
  const s = novoSlide("Integração: o mesmo dado em formas diferentes", 2, 1,
    "Exemplos de integração exigidos no enunciado. Distrito: maiúsculas sem acento na SME, com acento no IBGE; a regra de " +
    "normalização é a mesma. Idade: simples no microdado, grupos de cinco anos no IBGE; a dimensão Idade carrega a faixa do IBGE. " +
    "CD_SETOR é um homônimo: na SME é setor administrativo de 4 dígitos, no IBGE setor censitário de 15. " +
    "A prova de que a integração entre as bases da SME está certa: contando no microdado as matrículas ativas em junho, " +
    "a diferença para a planilha fica abaixo de 1% de 2015 a 2020.");
  tabela(s, ["Dado", "SME", "IBGE", "No data warehouse"], [
    ["Distrito", "AGUA RASA", "Água Rasa + código de 9 dígitos", "nome normalizado, chave da dimensão Território"],
    ["Idade", "idade simples em 31/03", "grupo de 0 a 4, 5 a 9, ...", "faixa IBGE na dimensão Idade"],
    ["Etapa", "Creche, Pré Escola (fila); MODALIDADE (microdado)", "não se aplica", "catálogo único de etapas"],
    ["Setor", "CD_SETOR: 4 dígitos, administrativo", "CD_SETOR: 15 dígitos, censitário", "homônimo: nunca cruzados"],
  ], { tabela: { x: 0.6, y: 1.5, w: 12.1, colW: [1.6, 3.6, 3.3, 3.6], fontSize: 14, rowH: 0.7 } });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.35, w: 12.1, h: 1.2, fill: { color: AREIA },
    line: { color: AREIA }, rectRadius: 0.08 });
  s.addText([
    { text: "Reconciliação: ", options: { bold: true, color: DESTAQUE_TEXTO } },
    { text: "matrículas ativas em junho no microdado contra a matrícula da planilha de fila, por distrito e etapa: diferença abaixo de 1% de 2015 a 2020 (creche: +0,03% em 2015, +0,17% em 2019)." },
  ], { x: 0.85, y: 5.45, w: 11.6, h: 1.0, fontFace: CORPO, fontSize: 15, color: TEXTO, margin: 0, isTextBox: true,
    valign: "middle" });
}

// ------------------------------------------------------------------ 9. qualidade
{
  const s = novoSlide("Problemas reais nos dados e como foram tratados", 2, 1,
    "Cada problema foi medido nos dados reais e tratado por uma regra testada. O mais grave: de 2022 a 2024 o código da escola " +
    "chega corrompido; recuperamos o código real pelo nome, tipo e distrito para 94,8% a 98,6% das matrículas. " +
    "Princípio: medida não publicada fica nula, nunca zero. O pipeline roda catorze verificações automáticas depois de cada carga; " +
    "na carga real nenhuma deu FALHA.");
  const probs = [
    ["Código da escola corrompido (2022-2024)", "recuperado pelo nome, tipo e distrito em 94,8% a 98,6% das matrículas"],
    ["Sete formatos da planilha de fila", "colunas lidas do cabeçalho; significado de (1), (2), (3) lido do rodapé"],
    ["Turno não publicado em 2021", "deduzido do código da turma, conferido pelos horários"],
    ["Idade com vírgula, nula ou nascida em 1900", "recalculada pelo nascimento; impossível vira não informada"],
    ["Datas em cinco formatos, inclusive serial do Excel", "todos lidos; fora da janela do ano letivo, descartadas"],
    ["Valores suprimidos pelo IBGE em setores pequenos", "6.543 valores ficam nulos, nunca zero"],
  ];
  probs.forEach(([t, c], i) => {
    const x = 0.6 + (i % 3) * 4.1;
    const y = 1.5 + Math.floor(i / 3) * 2.6;
    cartao(s, x, y, 3.9, 2.4, t, c, { tamTitulo: 15.5, tamCorpo: 14, altTitulo: 0.8, corpoY: 1.05 });
  });
}

// ------------------------------------------------------------------ 10. grão e aditividade
{
  const s = novoSlide("Grão e aditividade dos fatos", 2, 1,
    "Grão declarado antes das dimensões. Matrícula no grão mais fino que a fonte permite; fila no grão em que a prefeitura publica; " +
    "desfecho e ocupação são fatos agregados do fato de matrícula; população no grão do IBGE. " +
    "Fila e população são estoques: somam no território, não no tempo. Taxas e alunos por turma são derivados não aditivos, " +
    "sempre recalculados a partir das somas.");
  tabela(s, ["Tabela de fatos", "Grão", "Fatos", "Aditividade"], [
    ["Matrícula", "vínculo aluno-turma × ano", "quantidade (=1), dias de matrícula", "aditivo"],
    ["Fila", "distrito × mês × etapa", "matrículas, em processo, demanda e categorias", "semiaditivo (estoque)"],
    ["Desfecho", "escola × ano × série", "contagens por desfecho; taxas", "aditivo; taxas não aditivas"],
    ["Ocupação de Turma", "turma × ano", "turmas, matrículas, ativas em junho; alunos por turma", "aditivo; média não aditiva"],
    ["População", "setor censitário × faixa × Censo", "pessoas", "semiaditivo (estoque)"],
  ], { tabela: { x: 0.6, y: 1.55, w: 12.1, colW: [2.3, 3.1, 4.0, 2.7], fontSize: 15, rowH: 0.72 } });
}

// ------------------------------------------------------------------ 11. estrela matrícula
{
  const s = novoSlide("Esquema estrela Matrícula", 2, 1,
    "Fato no centro, dez dimensões. Dimensão Data com dois papéis, início e fim da matrícula, como a data de internação e de alta " +
    "do artigo da disciplina: as duas datas permitem contar matrículas ativas em um dia. O fato principal é a ocorrência do vínculo, contada por um campo artificial igual a 1, técnica de tabela de fatos sem fato; a única medida é dias de matrícula. " +
    "Três bugigangas. Duas degeneradas. Escola é mudança lenta tipo 2.");
  figura(s, "estrela-matricula.png", 0.5, 1.3, 8.15, 5.6, "Esquema estrela Matrícula: tabela de fatos Matrícula no centro, ligada a dez dimensões");
  s.addText(itens([
    "Data com dois papéis: início e fim da matrícula.",
    "Ocorrência contada por campo artificial (= 1), como em fatos sem fato.",
    "Bugigangas: Perfil, Deficiência, Situação.",
    "Degeneradas: id turma, código da matrícula.",
    "Escola: mudança lenta tipo 2.",
    "Hierarquias: dia ≤ mês ≤ trimestre ≤ semestre ≤ ano; série ≤ etapa ≤ nível; idade ≤ faixa IBGE.",
  ], 14), { x: 8.95, y: 1.4, w: 3.85, h: 5.5, fontFace: CORPO, color: TEXTO, margin: 0, isTextBox: true, valign: "top" });
}

// ================================================================== bloco 3: estrelas e constelação

// ------------------------------------------------------------------ 12. estrela fila
estrela("Esquema estrela Fila", "estrela-fila.png",
  "Esquema estrela Fila: tabela de fatos Fila ligada às dimensões Tempo, Território e Etapa", [
    "Grão: distrito × mês × etapa.",
    "Estoque: SOMA no território e na etapa; um único mês no tempo.",
    "Tempo: mês ≤ trimestre ≤ semestre ≤ ano e mês ≤ bimestre ≤ ano.",
    "Território: distrito ≤ DRE ≤ município ≤ UF.",
    "Formato da planilha: dimensão degenerada.",
  ],
  "Fila: medidas nulas onde a prefeitura não publicou a quebra; formato da planilha como dimensão degenerada. " +
  "Tempo tem duas hierarquias porque a fila foi trimestral até 2022 e bimestral depois. " +
  "A fila é estoque: soma entre distritos e etapas, mas no tempo se escolhe um mês, nunca se soma.");

// ------------------------------------------------------------------ 13. estrela desfecho
estrela("Esquema estrela Desfecho", "estrela-desfecho.png",
  "Esquema estrela Desfecho: tabela de fatos Desfecho ligada a Ano Letivo, Escola, Território e Série", [
    "Grão: escola × ano letivo × série.",
    "Fato agregado do fato Matrícula.",
    "Contagens por desfecho: SOMA.",
    "Taxas derivadas, não aditivas: recalculadas pelas contagens.",
    "Série: série ≤ etapa ≤ nível.",
  ],
  "Desfecho: fato agregado do fato de matrícula, porque taxa de rendimento só faz sentido sobre um conjunto de alunos. " +
  "As contagens somam; as taxas são recalculadas pelas contagens em qualquer nível, nunca como média de taxas. " +
  "Na educação infantil não há aprovação, então a taxa fica nula.");

// ------------------------------------------------------------------ 14. estrela ocupação de turma
estrela("Esquema estrela Ocupação de Turma", "estrela-turma.png",
  "Esquema estrela Ocupação de Turma: tabela de fatos ligada a Ano Letivo, Escola, Território, Série e Turno", [
    "Grão: turma × ano letivo.",
    "Turmas (= 1), matrículas e ativas em 30/06: SOMA.",
    "Alunos por turma: derivado, recalculado pelas somas.",
    "Capacidade não publicada por nenhuma fonte: não é estimada.",
    "id turma: dimensão degenerada.",
  ],
  "Ocupação de turma: agregado do fato de matrícula pelo id da turma. A capacidade não é publicada, então medimos " +
  "os alunos ativos em 30 de junho por turma em funcionamento. A média é sempre soma de alunos dividida por soma de turmas.");

// ------------------------------------------------------------------ 15. estrela população
estrela("Esquema estrela População", "estrela-populacao.png",
  "Esquema estrela População: tabela de fatos População ligada a Tempo, Setor Censitário, Território e Faixa Etária", [
    "Grão: setor censitário × faixa etária × data do Censo.",
    "Estoque: SOMA entre setores e faixas, não no tempo.",
    "Setor censitário ≤ distrito ≤ DRE ≤ município ≤ UF.",
    "Faixa Etária: rollup encolhido de Idade.",
    "Valor suprimido pelo IBGE fica nulo.",
  ],
  "População: Censo 2022 no grão de setor censitário, a menor unidade territorial do modelo. " +
  "Na carga real são 26.889 setores, todos ligados a um distrito da SME, e 11,4 milhões de moradores. " +
  "Faixa Etária é o rollup encolhido de Idade que conforma com a matrícula.");

// ------------------------------------------------------------------ 16. constelação
{
  const s = novoSlide("Constelação de fatos", 3, 1,
    "Cinco fatos, catorze dimensões. Território é compartilhado pelos cinco. Processo de projeto: matriz de barramento com fato e " +
    "dimensão, dimensões conformadas e, onde os grãos diferem, rollups encolhidos conformados (tracejado): Tempo e Ano Letivo de Data, " +
    "Etapa de Série, Faixa Etária de Idade, Território de Setor Censitário. O drill-across agrega cada fato até o grão comum e une pelos atributos conformados.");
  figura(s, "constelacao.png", 0.55, 1.35, 12.2, 5.0, "Constelação de fatos: cinco tabelas de fatos e catorze dimensões compartilhadas");
  s.addText("Processo de projeto: matriz de barramento (fato × dimensão), dimensões conformadas e, onde os grãos diferem, rollups encolhidos (tracejado).", {
    x: 0.6, y: 6.5, w: 12.1, h: 0.4, fontFace: CORPO, fontSize: 13, italic: true, color: SUAVE, margin: 0, isTextBox: true,
  });
}

// ================================================================== bloco 4: consultas, resultados e decisões

// ------------------------------------------------------------------ 17. consultas
{
  const s = novoSlide("Oito consultas OLAP", 4, 1.5,
    "O enunciado pede ao menos duas de roll-up ou drill-down, uma slice and dice, uma pivot e uma drill-across. " +
    "Temos três, uma, uma e três. Cada consulta responde a uma pergunta do gestor e cita os fatos que usa. " +
    "C7 é a que liga fila, matrícula e população; C8 é a da ocupação das turmas.");
  const linhas = [
    ["C1", "drill-down", "fila de creche: município → DRE → distrito", "Fila"],
    ["C2", "roll-up", "matrículas: etapa → nível → total, ano a ano", "Matrícula"],
    ["C3", "slice and dice", "creche por rede e jornada, 2019 e 2024", "Matrícula"],
    ["C4", "pivot", "DRE nas linhas, jornada nas colunas", "Matrícula"],
    ["C5", "drill-across", "fila contra matrícula ativa em junho, por distrito", "Fila, Matrícula"],
    ["C6", "drill-across", "fila de creche e abandono no fundamental, por DRE", "Fila, Matrícula, Desfecho"],
    ["C7", "drill-across", "crianças de 0 a 4 anos: residentes, matriculadas e na fila", "População, Matrícula, Fila"],
    ["C8", "drill-down", "alunos por turma: município → DRE → distrito", "Ocupação de Turma"],
  ];
  tabela(s, ["", "Operação", "Pergunta", "Fatos"], linhas,
    { primeiraEmNegrito: true, tabela: { x: 0.6, y: 1.45, w: 12.1, colW: [0.7, 2.0, 6.0, 3.4], fontSize: 14, rowH: 0.56 } });
}

// ------------------------------------------------------------------ 18. resultados: fila e oferta
{
  const s = novoSlide("Resultados: fila e oferta de creche", 4, 1,
    "Consulta 5 na carga com os dados reais de 2015 a 2024. A fila de creche em junho caiu 97% em dez anos e a " +
    "fração da demanda fora da rede passou de 34% para 1%. A queda maior foi de 2017 a 2021. " +
    "Consulta 3: 85% das matrículas de creche estão na rede conveniada, quase todas em jornada integral, em 2019 e em 2024.");
  const anos = ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"];
  s.addChart(pres.charts.BAR, [{ name: "Fila de creche em junho", labels: anos,
    values: [124741, 103496, 104268, 66714, 48910, 22732, 8767, 4761, 4913, 3633] }], {
    x: 0.5, y: 1.35, w: 6.2, h: 4.9, barDir: "col", chartColors: [ESCURO], showTitle: true,
    title: "Crianças na fila de creche em junho", titleFontSize: 15, titleColor: TEXTO, titleFontFace: CORPO,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 9, dataLabelFormatCode: "#,##0",
    dataLabelColor: TEXTO, catAxisLabelColor: SUAVE, valAxisLabelColor: SUAVE, valAxisLabelFormatCode: "#,##0",
    valGridLine: { color: "E3E8E6", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false,
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
  });
  s.addChart(pres.charts.LINE, [{ name: "Fração fora da rede", labels: anos,
    values: [34.1, 27.1, 26.6, 17.5, 12.8, 6.2, 2.4, 1.3, 1.4, 1.1] }], {
    x: 6.9, y: 1.35, w: 5.9, h: 3.3, chartColors: [DESTAQUE], lineSize: 3, lineDataSymbol: "circle",
    lineDataSymbolSize: 8, showTitle: true, title: "Fração da demanda de creche fora da rede (%)", titleFontSize: 15,
    titleColor: TEXTO, titleFontFace: CORPO, showValue: true, dataLabelPosition: "t", dataLabelFontSize: 9, dataLabelFormatCode: "0.0",
    dataLabelColor: TEXTO, catAxisLabelColor: SUAVE, valAxisLabelColor: SUAVE, valGridLine: { color: "E3E8E6", size: 0.5 },
    catGridLine: { style: "none" }, showLegend: false, catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
  });
  cartao(s, 6.9, 4.85, 5.9, 1.45, "85% da creche é conveniada", "2019 e 2024, quase toda em jornada integral (consulta 3).",
    { fundo: AREIA, tamCorpo: 14 });
  fonte(s, "Fonte: SME-SP, Demanda Registrada e Matrículas e Microdados de Matrículas; consultas 3 e 5.");
}

// ------------------------------------------------------------------ 19. resultados: população e ocupação
{
  const s = novoSlide("Resultados: população e ocupação das turmas", 4, 1,
    "Consulta 7, na data do Censo: 598.406 crianças de 0 a 4 anos moram no município e a rede municipal tinha 514.131 matrículas " +
    "ativas dessa idade, 86 por 100. A média esconde distâncias grandes: 25 distritos têm menos de 50 matrículas por 100 crianças " +
    "residentes e outros 25 passam de 100, porque a matrícula conta onde a escola fica e a população onde a criança mora. " +
    "Consulta 8: a creche funciona com perto de 11 crianças por turma em todas as DREs; no fundamental são de 28 a 32.");
  cartao(s, 0.6, 1.45, 5.9, 2.35, "Consulta 7 · 31/07/2022", "");
  s.addText("86 por 100 crianças", {
    x: 0.85, y: 2.05, w: 5.4, h: 0.7, fontFace: TITULO, fontSize: 28, bold: true, color: DESTAQUE_TEXTO, margin: 0,
    isTextBox: true,
  });
  s.addText("514.131 matrículas ativas de 0 a 4 anos na rede municipal para 598.406 crianças dessa idade residentes.", {
    x: 0.85, y: 2.85, w: 5.4, h: 0.8, fontFace: CORPO, fontSize: 14, color: TEXTO, margin: 0, isTextBox: true, valign: "top",
  });
  cartao(s, 0.6, 4.0, 5.9, 2.5, "Por distrito, longe da média",
    "25 distritos com menos de 50 matrículas por 100 crianças; outros 25 com mais de 100.\n\n" +
    "A matrícula conta onde a escola fica; a população, onde a criança mora.", { tamCorpo: 15 });
  s.addChart(pres.charts.BAR, [
    { name: "2019", labels: ["Creche", "Pré-escola", "Fund. iniciais", "Fund. finais"], values: [11.5, 30.7, 28.7, 29.4] },
    { name: "2024", labels: ["Creche", "Pré-escola", "Fund. iniciais", "Fund. finais"], values: [11.0, 26.9, 30.6, 31.6] },
  ], {
    x: 6.9, y: 1.35, w: 5.9, h: 5.2, barDir: "col", barGrouping: "clustered", chartColors: [ESCURO, DESTAQUE],
    showTitle: true, title: "Alunos por turma em 30 de junho (consulta 8)", titleFontSize: 15, titleColor: TEXTO,
    titleFontFace: CORPO, showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelFormatCode: "0.0",
    dataLabelColor: TEXTO, catAxisLabelColor: SUAVE, valAxisLabelColor: SUAVE, valGridLine: { color: "E3E8E6", size: 0.5 },
    catGridLine: { style: "none" }, showLegend: true, legendPos: "b", legendFontSize: 12, legendColor: TEXTO,
    catAxisLabelFontSize: 12, valAxisLabelFontSize: 10, valAxisMinVal: 0,
  });
  fonte(s, "Fonte: Censo 2022 (IBGE) e Microdados de Matrículas (SME-SP); consultas 7 e 8.");
}

// ------------------------------------------------------------------ 20. decisões
{
  const s = novoSlide("Decisões de projeto em destaque", 4, 1,
    "Seis das 23 decisões documentadas no repositório. Cada uma tem a alternativa descartada e o argumento. " +
    "Destacar as duas que mais aparecem em perguntas: por que rollups encolhidos em vez de um grão único, e por que nulo e não zero.");
  const decisoes = [
    ["1", "Grão mais fino na matrícula", "vínculo aluno-turma: preserva perfil e desfecho de cada aluno"],
    ["2", "Rollups encolhidos", "cada fato mantém o seu grão; Etapa, Tempo, Faixa Etária e Território conformam"],
    ["3", "Nulo não é zero", "medida não publicada fica nula; zero faria a fila sumir"],
    ["4", "Escola tipo 2", "402 escolas mudam de nome, tipo, distrito ou DRE na série"],
    ["5", "Capacidade não inventada", "ocupação medida pelos alunos ativos; nenhuma vaga estimada"],
    ["6", "Datas de referência", "junho para fila × matrícula; 31/07/2022 para população × matrícula"],
  ];
  decisoes.forEach(([n, t, c], i) => {
    const x = 0.6 + (i % 2) * 6.15;
    const y = 1.5 + Math.floor(i / 2) * 1.75;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.95, h: 1.55, fill: { color: TINTA }, line: { color: TINTA },
      rectRadius: 0.08 });
    circulo(s, x + 0.25, y + 0.5, n);
    s.addText(t, { x: x + 1.0, y: y + 0.18, w: 4.75, h: 0.45, fontFace: CORPO, fontSize: 17, bold: true, color: ESCURO,
      margin: 0, isTextBox: true });
    s.addText(c, { x: x + 1.0, y: y + 0.65, w: 4.75, h: 0.8, fontFace: CORPO, fontSize: 14, color: TEXTO, margin: 0,
      isTextBox: true, valign: "top" });
  });
}

// ------------------------------------------------------------------ 21. encerramento
{
  const s = novoSlide("Obrigado. Perguntas?", 4, 0.5,
    "Encerramento. Lembrar que o relatório em PDF traz a descrição completa de cada atributo, com a coluna de origem e a integração, " +
    "e que o repositório tem o pipeline completo, os testes e a documentação. Abrir para perguntas.", true);
  s.addText(itens([
    "Relatório: descrição do problema, povoamento atributo por atributo, cinco estrelas, constelação e oito consultas.",
    "Repositório: pipeline do portal ao DuckDB, 14 verificações de qualidade e testes automáticos, inclusive da modelagem.",
    "Carga real: 13,4 milhões de matrículas, 551 mil turmas e 26.889 setores censitários em 3,5 minutos, sem nenhuma FALHA nas verificações.",
  ], 18), { x: 0.6, y: 1.7, w: 11.8, h: 3.3, fontFace: CORPO, color: BRANCO, margin: 0, isTextBox: true, valign: "top" });
  s.addText("github.com/kevennlaranjeira/OLAP2026", { x: 0.6, y: 5.3, w: 11.8, h: 0.5, fontFace: CORPO, fontSize: 18,
    bold: true, color: "F2C46B", margin: 0, isTextBox: true });
  s.addText(INTEGRANTES.map(([n]) => n).join("  ·  "), { x: 0.6, y: 6.2, w: 11.8, h: 0.45, fontFace: CORPO,
    fontSize: 14, color: "B9CFC9", margin: 0, isTextBox: true });
}

// ------------------------------------------------------------------ roteiro, a partir dos blocos montados
for (let b = 1; b <= 4; b += 1) {
  const x = 0.6 + (b - 1) * 3.075;
  const lista = slidesDoBloco[b];
  roteiro.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.5, w: 2.9, h: 4.95, fill: { color: TINTA },
    line: { color: TINTA }, rectRadius: 0.08 });
  circulo(roteiro, x + 0.25, 1.75, String(b));
  roteiro.addText(BLOCO[b], { x: x + 0.25, y: 2.45, w: 2.45, h: 0.75, fontFace: CORPO, fontSize: 16, bold: true,
    color: ESCURO, margin: 0, isTextBox: true, valign: "top" });
  roteiro.addText(`slides ${lista[0]} a ${lista[lista.length - 1]}`, { x: x + 0.25, y: 3.2, w: 2.45, h: 0.35,
    fontFace: CORPO, fontSize: 13, bold: true, color: DESTAQUE_TEXTO, margin: 0, isTextBox: true });
  roteiro.addText(ASSUNTO_DO_BLOCO[b], { x: x + 0.25, y: 3.6, w: 2.45, h: 1.9, fontFace: CORPO, fontSize: 14,
    color: TEXTO, margin: 0, isTextBox: true, valign: "top" });
  roteiro.addText(`${virgula(minutosDoBloco[b])} min`, { x: x + 0.25, y: 5.6, w: 2.45, h: 0.6, fontFace: TITULO,
    fontSize: 26, bold: true, color: ESCURO, margin: 0, isTextBox: true });
}
const total = Object.values(minutosDoBloco).reduce((a, b) => a + b, 0);
roteiro.addText(`Total previsto: ${virgula(total)} minutos, sem contar as perguntas. Com outro limite de tempo, a divisão continua em quatro partes iguais.`, {
  x: 0.6, y: 6.6, w: 11.5, h: 0.35, fontFace: CORPO, fontSize: 12, italic: true, color: SUAVE, margin: 0, isTextBox: true,
});

const destino = process.argv[2] || path.join(AQUI, "apresentacao-projeto1.pptx");
pres.writeFile({ fileName: destino }).then((f) => console.log(`gravado: ${f}`));
