// Gera docs/apresentacao/apresentacao-projeto1.pptx.
// Requer Node e pptxgenjs:  npm install pptxgenjs  e depois  node docs/apresentacao/gerar.js
// As figuras dos esquemas vêm de docs/apresentacao/figuras/ (ver esquemas.tex na mesma pasta).
// Todos os números dos slides vêm da carga com os dados reais documentada em docs/05-consultas.md.
"use strict";
const path = require("path");
const pptxgen = require(process.env.PPTXGENJS || "pptxgenjs");

const AQUI = __dirname;
const FIG = (nome) => path.join(AQUI, "figuras", nome);

const ESCURO = "183D3D";
const TINTA = "E7F0ED";
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

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,33 x 7,5 polegadas
pres.title = "Rede Municipal Paulistana: oferta escolar e demanda não atendida";
pres.author = "Grupo 7, SCC0245";

let numero = 0;

function novoSlide(titulo, bloco, notas, escuro = false) {
  const s = pres.addSlide();
  numero += 1;
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
  const quem = bloco ? `Apresenta: ${BLOCO[bloco]} (bloco ${bloco} de 4).\n\n` : "";
  s.addNotes(quem + notas);
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

function figura(s, arquivo, x, y, w, proporcao) {
  s.addImage({ path: FIG(arquivo), x, y, w, h: w / proporcao });
}

// ------------------------------------------------------------------ 1. capa
{
  const s = novoSlide(null, 1,
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

// ------------------------------------------------------------------ 2. problema
{
  const s = novoSlide("O problema: falta de vaga na educação infantil", 1,
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

// ------------------------------------------------------------------ 3. perguntas do gestor
{
  const s = novoSlide("Perguntas que o data warehouse responde", 1,
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

// ------------------------------------------------------------------ 4. por que São Paulo
{
  const s = novoSlide("Por que São Paulo, e não São Carlos", 1,
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
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.0, w: 12.1, h: 1.55, fill: { color: "F6EBD3" },
    line: { color: "F6EBD3" }, rectRadius: 0.08 });
  s.addText([
    { text: "O modelo vale para São Carlos: ", options: { bold: true, color: DESTAQUE_TEXTO } },
    { text: "matrícula, turma e desfecho vêm do registro que todo sistema de gestão escolar mantém, e o Censo 2022 já tem a " +
      "população por setor censitário do município. Falta só a rede registrar e publicar a fila." },
  ], { x: 0.85, y: 5.1, w: 11.6, h: 1.35, fontFace: CORPO, fontSize: 16, color: TEXTO, margin: 0, isTextBox: true,
    valign: "middle" });
}

// ------------------------------------------------------------------ 5. assuntos e processos
{
  const s = novoSlide("Cinco assuntos de interesse, cinco processos", 2,
    "Os cinco assuntos são os registrados na planilha do grupo. Cada um vira um processo com tabela de fatos, ou atributos. " +
    "Oferta por setor é respondida pela rede (direta ou conveniada) e pelo território. O desfecho da matrícula é o quinto processo, " +
    "que acompanha o que acontece depois do acesso.");
  const linhas = [
    ["Matrículas", "Matrícula", "vínculo aluno-turma em um ano letivo"],
    ["Fila (demanda registrada)", "Fila por vaga", "distrito × mês × etapa"],
    ["Capacidade e ocupação das turmas", "Ocupação de turma", "turma em um ano letivo"],
    ["População em idade escolar", "População residente", "setor censitário × faixa etária"],
    ["Oferta escolar por setor", "rede da escola e território", "dimensões Escola, Território, Setor"],
    ["(acompanhamento do acesso)", "Desfecho da matrícula", "escola × ano × série"],
  ];
  const cab = ["Assunto de interesse", "Processo (tabela de fatos)", "Grão"].map((t) => ({
    text: t, options: { bold: true, color: BRANCO, fill: { color: ESCURO } },
  }));
  const corpo = linhas.map((l, i) => l.map((t) => ({ text: t, options: { fill: { color: i % 2 ? BRANCO : TINTA } } })));
  s.addTable([cab, ...corpo], {
    x: 0.6, y: 1.55, w: 12.1, colW: [4.0, 3.9, 4.2], fontFace: CORPO, fontSize: 15, color: TEXTO,
    border: { type: "solid", color: "C9D8D3", pt: 0.75 }, rowH: 0.62, valign: "middle",
  });
}

// ------------------------------------------------------------------ 6. fontes
{
  const s = novoSlide("Três fontes de dados reais e oficiais", 2,
    "Duas fontes da SME no Portal de Dados Abertos da Prefeitura, com grão, formato e vocabulário diferentes, e o Censo 2022 do IBGE. " +
    "A fila tem sete formatos entre 2006 e 2026, e o significado das colunas numeradas muda com o formato. " +
    "O Censo traz a demanda potencial: quantas crianças moram em cada setor. A população foi implementada e testada, " +
    "e os números reais dela saem na próxima carga.");
  const fontes = [
    ["Microdados de Matrículas", "SME-SP · anual",
      "Uma linha por vínculo aluno-turma: escola, turma, turno, série, idade, perfil, deficiência, datas e desfecho.\n\n13,4 milhões de matrículas de escolarização (2015-2024)."],
    ["Demanda Registrada e Matrículas", "SME-SP · trimestral, bimestral desde 2023",
      "Por distrito e etapa: matrículas, matrículas em processo e fila.\n\n44 planilhas × 96 distritos no recorte; sete formatos diferentes."],
    ["Censo Demográfico 2022", "IBGE · Agregados por Setores",
      "Pessoas residentes por setor censitário e grupo de idade (variáveis V01031 a V01041).\n\nData de referência: noite de 31/07 para 01/08/2022."],
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

// ------------------------------------------------------------------ 7. integração
{
  const s = novoSlide("Integração: mesmo dado, representações diferentes", 2,
    "Exemplos de integração exigidos no enunciado. Distrito: maiúsculas sem acento na SME, com acento no IBGE; a regra de " +
    "normalização é a mesma. Idade: simples no microdado, grupos de cinco anos no IBGE; a dimensão Idade carrega a faixa do IBGE. " +
    "CD_SETOR é um homônimo: na SME é setor administrativo de 4 dígitos, no IBGE setor censitário de 15. " +
    "A prova de que a integração entre as bases da SME está certa: contando no microdado as matrículas ativas em junho, " +
    "a diferença para a planilha fica abaixo de 1% de 2015 a 2020.");
  const cab = ["Dado", "SME", "IBGE", "No data warehouse"].map((t) => ({
    text: t, options: { bold: true, color: BRANCO, fill: { color: ESCURO } },
  }));
  const linhas = [
    ["Distrito", "AGUA RASA", "Água Rasa + código de 9 dígitos", "nome normalizado, chave da dimensão Território"],
    ["Idade", "idade simples em 31/03", "grupo de 0 a 4, 5 a 9, ...", "faixa IBGE na dimensão Idade"],
    ["Etapa", "Creche, Pré Escola (fila); MODALIDADE (microdado)", "não se aplica", "catálogo único de etapas"],
    ["Setor", "CD_SETOR: 4 dígitos, administrativo", "CD_SETOR: 15 dígitos, censitário", "homônimo: nunca cruzados"],
  ].map((l, i) => l.map((t) => ({ text: t, options: { fill: { color: i % 2 ? BRANCO : TINTA } } })));
  s.addTable([cab, ...linhas], {
    x: 0.6, y: 1.5, w: 12.1, colW: [1.6, 3.6, 3.3, 3.6], fontFace: CORPO, fontSize: 14, color: TEXTO,
    border: { type: "solid", color: "C9D8D3", pt: 0.75 }, rowH: 0.7, valign: "middle",
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.35, w: 12.1, h: 1.2, fill: { color: "F6EBD3" },
    line: { color: "F6EBD3" }, rectRadius: 0.08 });
  s.addText([
    { text: "Reconciliação: ", options: { bold: true, color: DESTAQUE_TEXTO } },
    { text: "matrículas ativas em junho no microdado contra a matrícula da planilha de fila, por distrito e etapa: diferença abaixo de 1% de 2015 a 2020 (creche: +0,03% em 2015, +0,17% em 2019)." },
  ], { x: 0.85, y: 5.45, w: 11.6, h: 1.0, fontFace: CORPO, fontSize: 15, color: TEXTO, margin: 0, isTextBox: true,
    valign: "middle" });
}

// ------------------------------------------------------------------ 8. qualidade
{
  const s = novoSlide("Problemas reais nos dados e como foram tratados", 2,
    "Cada problema foi medido nos dados reais e tratado por uma regra testada. O mais grave: de 2022 a 2024 o código da escola " +
    "chega corrompido; recuperamos o código real pelo nome, tipo e distrito para 94,8% a 98,6% das matrículas. " +
    "Princípio: medida não publicada fica nula, nunca zero. O pipeline roda doze verificações automáticas depois de cada carga.");
  const probs = [
    ["Código da escola corrompido (2022-2024)", "recuperado pelo nome, tipo e distrito em 94,8% a 98,6% das matrículas"],
    ["Sete formatos da planilha de fila", "colunas lidas do cabeçalho; significado de (1), (2), (3) lido do rodapé"],
    ["Turno não publicado em 2021", "deduzido do código da turma, conferido pelos horários"],
    ["Idade com vírgula, nula ou nascida em 1900", "recalculada pelo nascimento; impossível vira não informada"],
    ["Datas em cinco formatos, inclusive serial do Excel", "todos lidos; fora da janela do ano letivo, descartadas"],
    ["Quebra da fila publicada só a partir de 2020", "nulo onde não foi publicada, nunca zero"],
  ];
  probs.forEach(([t, c], i) => {
    const x = 0.6 + (i % 3) * 4.1;
    const y = 1.5 + Math.floor(i / 3) * 2.6;
    cartao(s, x, y, 3.9, 2.4, t, c, { tamTitulo: 15.5, tamCorpo: 14, altTitulo: 0.8, corpoY: 1.05 });
  });
}

// ------------------------------------------------------------------ 9. grão e aditividade
{
  const s = novoSlide("Grão e aditividade dos fatos", 3,
    "Grão declarado antes das dimensões. Matrícula no grão mais fino que a fonte permite; fila no grão em que a prefeitura publica; " +
    "desfecho e ocupação são fatos agregados do fato de matrícula; população no grão do IBGE. " +
    "Fila e população são estoques: somam no território, não no tempo. Taxas e alunos por turma são derivados não aditivos, " +
    "sempre recalculados a partir das somas.");
  const cab = ["Tabela de fatos", "Grão", "Fatos", "Aditividade"].map((t) => ({
    text: t, options: { bold: true, color: BRANCO, fill: { color: ESCURO } },
  }));
  const linhas = [
    ["Matrícula", "vínculo aluno-turma × ano", "quantidade (=1), dias de matrícula", "aditivo"],
    ["Fila", "distrito × mês × etapa", "matrículas, em processo, demanda e categorias", "semiaditivo (estoque)"],
    ["Desfecho", "escola × ano × série", "contagens por desfecho; taxas", "aditivo; taxas não aditivas"],
    ["Ocupação de Turma", "turma × ano", "turmas, matrículas, ativas em junho; alunos por turma", "aditivo; média não aditiva"],
    ["População", "setor censitário × faixa × Censo", "pessoas", "semiaditivo (estoque)"],
  ].map((l, i) => l.map((t) => ({ text: t, options: { fill: { color: i % 2 ? BRANCO : TINTA } } })));
  s.addTable([cab, ...linhas], {
    x: 0.6, y: 1.55, w: 12.1, colW: [2.3, 3.1, 4.0, 2.7], fontFace: CORPO, fontSize: 15, color: TEXTO,
    border: { type: "solid", color: "C9D8D3", pt: 0.75 }, rowH: 0.72, valign: "middle",
  });
}

// ------------------------------------------------------------------ 10. estrela matrícula
{
  const s = novoSlide("Esquema estrela Matrícula", 3,
    "Fato no centro, dez dimensões. Dimensão Data com dois papéis, início e fim da matrícula, como a data de internação e de alta " +
    "do artigo da disciplina: as duas datas permitem contar matrículas ativas em um dia. Tabela de fatos sem fato com campo artificial. " +
    "Três bugigangas. Duas degeneradas. Escola é mudança lenta tipo 2.");
  figura(s, "estrela-matricula.png", 0.5, 1.3, 8.15, 1529 / 1063);
  s.addText(itens([
    "Data com dois papéis: início e fim da matrícula.",
    "Tabela de fatos sem fato: quantidade = 1.",
    "Bugigangas: Perfil, Deficiência, Situação.",
    "Degeneradas: id turma, código da matrícula.",
    "Escola: mudança lenta tipo 2.",
    "Hierarquias: dia ≤ mês ≤ trimestre ≤ semestre ≤ ano; série ≤ etapa ≤ nível; idade ≤ faixa IBGE.",
  ], 14), { x: 8.95, y: 1.4, w: 3.85, h: 5.5, fontFace: CORPO, color: TEXTO, margin: 0, isTextBox: true, valign: "top" });
}

// ------------------------------------------------------------------ 11. estrelas fila e desfecho
{
  const s = novoSlide("Estrelas Fila e Desfecho", 3,
    "Fila: medidas nulas onde a prefeitura não publicou a quebra; formato da planilha como dimensão degenerada. " +
    "Tempo tem duas hierarquias porque a fila foi trimestral até 2022 e bimestral depois. " +
    "Desfecho: fato agregado; as taxas são recalculadas pelas contagens em qualquer nível, nunca como média de taxas.");
  figura(s, "estrela-fila.png", 0.5, 1.3, 8.0, 1529 / 501);
  figura(s, "estrela-desfecho.png", 0.5, 4.15, 8.0, 1529 / 482);
  s.addText(itens([
    "Fila: estoque; SOMA no território e na etapa, um único mês no tempo.",
    "Tempo: mês ≤ trimestre ≤ semestre ≤ ano e mês ≤ bimestre ≤ ano.",
    "Desfecho: contagens aditivas; taxas derivadas, recalculadas.",
    "Território: distrito ≤ DRE ≤ município ≤ UF.",
  ], 14), { x: 8.85, y: 1.4, w: 3.95, h: 5.5, fontFace: CORPO, color: TEXTO, margin: 0, isTextBox: true, valign: "top" });
}

// ------------------------------------------------------------------ 12. estrelas turma e população
{
  const s = novoSlide("Estrelas Ocupação de Turma e População", 3,
    "Os dois assuntos que completam a planilha do grupo. Ocupação de turma: agregado do fato de matrícula pelo id da turma; " +
    "a capacidade não é publicada, então medimos alunos ativos em 30 de junho. População: Censo 2022 no grão de setor censitário, " +
    "com setor ≤ distrito ≤ DRE ≤ município ≤ UF. As duas estrelas estão implementadas e testadas; os números reais saem na próxima carga.");
  figura(s, "estrela-turma.png", 0.5, 1.3, 7.0, 1529 / 649);
  figura(s, "estrela-populacao.png", 0.5, 4.45, 7.0, 1529 / 536);
  s.addText(itens([
    "Ocupação: alunos ativos em 30/06 por turma ativa; média recalculada pelas somas.",
    "Capacidade não publicada por nenhuma fonte: não é estimada.",
    "População: estoque na data do Censo; valor não publicado fica nulo.",
    "Setor censitário ≤ distrito ≤ DRE ≤ município ≤ UF.",
    "Faixa Etária é rollup encolhido de Idade.",
  ], 14), { x: 7.85, y: 1.4, w: 4.95, h: 5.5, fontFace: CORPO, color: TEXTO, margin: 0, isTextBox: true, valign: "top" });
}

// ------------------------------------------------------------------ 13. constelação
{
  const s = novoSlide("Constelação de fatos", 3,
    "Cinco fatos, catorze dimensões. Território é compartilhado pelos cinco. Onde os grãos diferem, cada fato manteve o seu e " +
    "as dimensões de grão mais alto são rollups encolhidos conformados (tracejado): Tempo e Ano Letivo de Data, Etapa de Série, " +
    "Faixa Etária de Idade, Território de Setor Censitário. O drill-across agrega cada fato até o grão comum e une pelos atributos conformados.");
  figura(s, "constelacao.png", 0.55, 1.35, 12.2, 2455 / 1019);
  s.addText("Tracejado: rollup encolhido conformado. Território é compartilhado pelos cinco fatos.", {
    x: 0.6, y: 6.55, w: 12.1, h: 0.4, fontFace: CORPO, fontSize: 13, italic: true, color: SUAVE, margin: 0, isTextBox: true,
  });
}

// ------------------------------------------------------------------ 14. consultas
{
  const s = novoSlide("Oito consultas OLAP", 4,
    "O enunciado pede ao menos duas de roll-up ou drill-down, uma slice and dice, uma pivot e uma drill-across. " +
    "Temos três, uma, uma e três. Cada consulta responde a uma pergunta do gestor e cita os fatos que usa. " +
    "C7 é a que liga fila, matrícula e população; C8 é a da ocupação das turmas.");
  const cab = ["", "Operação", "Pergunta", "Fatos"].map((t) => ({
    text: t, options: { bold: true, color: BRANCO, fill: { color: ESCURO } },
  }));
  const linhas = [
    ["C1", "drill-down", "fila de creche: município → DRE → distrito", "Fila"],
    ["C2", "roll-up", "matrículas: etapa → nível → total, ano a ano", "Matrícula"],
    ["C3", "slice and dice", "creche por rede e jornada, 2019 e 2024", "Matrícula"],
    ["C4", "pivot", "DRE nas linhas, jornada nas colunas", "Matrícula"],
    ["C5", "drill-across", "fila contra matrícula ativa em junho, por distrito", "Fila, Matrícula"],
    ["C6", "drill-across", "fila de creche e abandono no fundamental, por DRE", "Fila, Matrícula, Desfecho"],
    ["C7", "drill-across", "crianças de 0 a 4 anos: residentes, matriculadas e na fila", "População, Matrícula, Fila"],
    ["C8", "drill-down", "alunos por turma: município → DRE → distrito", "Ocupação de Turma"],
  ].map((l, i) => l.map((t, j) => ({ text: t, options: { fill: { color: i % 2 ? BRANCO : TINTA }, bold: j === 0 } })));
  s.addTable([cab, ...linhas], {
    x: 0.6, y: 1.45, w: 12.1, colW: [0.7, 2.0, 6.0, 3.4], fontFace: CORPO, fontSize: 14, color: TEXTO,
    border: { type: "solid", color: "C9D8D3", pt: 0.75 }, rowH: 0.56, valign: "middle",
  });
}

// ------------------------------------------------------------------ 15. resultados
{
  const s = novoSlide("Resultados com os dados reais", 4,
    "Resultados da consulta 5 na carga com os dados reais de 2015 a 2024. A fila de creche em junho caiu 97% em dez anos e a " +
    "fração da demanda fora da rede passou de 34% para 1%. Os anos 2016, 2018 e 2023 não aparecem no gráfico porque não estão " +
    "na tabela de resultados documentada. Consulta 3: 85% das matrículas de creche estão na rede conveniada, quase todas em " +
    "jornada integral. C7 e C8 ainda não foram rodadas com os dados reais.");
  const anos = ["2015", "2017", "2019", "2020", "2021", "2022", "2024"];
  s.addChart(pres.charts.BAR, [{ name: "Fila de creche em junho", labels: anos,
    values: [124741, 104268, 48910, 22732, 8767, 4761, 3633] }], {
    x: 0.5, y: 1.35, w: 6.2, h: 4.9, barDir: "col", chartColors: [ESCURO], showTitle: true,
    title: "Crianças na fila de creche em junho", titleFontSize: 15, titleColor: TEXTO, titleFontFace: CORPO,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelFormatCode: "#,##0",
    dataLabelColor: TEXTO, catAxisLabelColor: SUAVE, valAxisLabelColor: SUAVE, valAxisLabelFormatCode: "#,##0",
    valGridLine: { color: "E3E8E6", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false,
    catAxisLabelFontSize: 12, valAxisLabelFontSize: 10,
  });
  s.addChart(pres.charts.LINE, [{ name: "Fração fora da rede", labels: anos,
    values: [34.1, 26.6, 12.8, 6.2, 2.4, 1.3, 1.1] }], {
    x: 6.9, y: 1.35, w: 5.9, h: 3.3, chartColors: [DESTAQUE], lineSize: 3, lineDataSymbol: "circle",
    lineDataSymbolSize: 8, showTitle: true, title: "Fração da demanda de creche fora da rede (%)", titleFontSize: 15,
    titleColor: TEXTO, titleFontFace: CORPO, showValue: true, dataLabelPosition: "t", dataLabelFontSize: 10, dataLabelFormatCode: "0.0",
    dataLabelColor: TEXTO, catAxisLabelColor: SUAVE, valAxisLabelColor: SUAVE, valGridLine: { color: "E3E8E6", size: 0.5 },
    catGridLine: { style: "none" }, showLegend: false, catAxisLabelFontSize: 12, valAxisLabelFontSize: 10,
  });
  cartao(s, 6.9, 4.85, 5.9, 1.45, "85% da creche é conveniada", "2019 e 2024, quase toda em jornada integral (consulta 3).",
    { fundo: "F6EBD3", tamCorpo: 14 });
  fonte(s, "Fonte: SME-SP, Demanda Registrada e Matrículas e Microdados de Matrículas; consultas 3 e 5. C7 e C8 serão medidas na próxima carga.");
}

// ------------------------------------------------------------------ 16. decisões
{
  const s = novoSlide("Decisões de projeto em destaque", 4,
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

// ------------------------------------------------------------------ 17. encerramento
{
  const s = novoSlide("Obrigado. Perguntas?", 4,
    "Encerramento. Lembrar que o relatório em PDF traz a descrição completa de cada atributo, com a coluna de origem e a integração, " +
    "e que o repositório tem o pipeline completo, os testes e a documentação. Abrir para perguntas.", true);
  s.addText(itens([
    "Relatório: descrição do problema, povoamento atributo por atributo, cinco estrelas, constelação e oito consultas.",
    "Repositório: pipeline do portal ao DuckDB, 12 verificações de qualidade e testes automáticos.",
    "Próximo passo: rodar a carga com o Censo 2022 e medir as consultas 7 e 8 com os dados reais.",
  ], 18), { x: 0.6, y: 1.7, w: 11.8, h: 3.0, fontFace: CORPO, color: BRANCO, margin: 0, isTextBox: true, valign: "top" });
  s.addText("github.com/kevennlaranjeira/OLAP2026", { x: 0.6, y: 5.3, w: 11.8, h: 0.5, fontFace: CORPO, fontSize: 18,
    bold: true, color: "F2C46B", margin: 0, isTextBox: true });
  s.addText(INTEGRANTES.map(([n]) => n).join("  ·  "), { x: 0.6, y: 6.2, w: 11.8, h: 0.45, fontFace: CORPO,
    fontSize: 14, color: "B9CFC9", margin: 0, isTextBox: true });
}

const destino = process.argv[2] || path.join(AQUI, "apresentacao-projeto1.pptx");
pres.writeFile({ fileName: destino }).then((f) => console.log(`gravado: ${f}`));
