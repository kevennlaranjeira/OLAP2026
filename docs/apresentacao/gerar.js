// Gera docs/apresentacao/apresentacao-projeto1.pptx.
// Requer Node e pptxgenjs:  npm install pptxgenjs  e depois  node docs/apresentacao/gerar.js
// As figuras dos esquemas vêm de docs/modelagem/ (geradas por figuras.tex na mesma pasta).
// Todos os números dos slides vêm da carga com os dados reais documentada em docs/05-consultas.md.
// Cada slide declara quem apresenta e o tempo previsto; o slide de roteiro soma os tempos por bloco.
//
// Sistema visual: azul-ardósia dominante, cobalto para dados, âmbar como único acento; cartões
// arredondados com sombra leve e selos numerados em âmbar; etiqueta do bloco acima de cada título;
// número da página no rodapé. Movimento só por opacidade: transição de esmaecimento em todos os
// slides e entrada em sequência dos elementos marcados com objectName "anim:<ordem>:<nome>".
"use strict";
const fs = require("fs");
const path = require("path");
const MODULO_PPTX = process.env.PPTXGENJS || "pptxgenjs";
const pptxgen = require(MODULO_PPTX);

const AQUI = __dirname;
const FIG = (nome) => path.join(AQUI, "..", "modelagem", nome);
const TOTAL_SLIDES = 21;

const COR = {
  tinta: "1B2A4A",        // azul-ardósia profundo, cor dominante
  cobalto: "2E5EAA",      // dados e destaques sobre fundo claro
  ambar: "F2A541",        // acento único: selos e números sobre fundo escuro
  ambarTexto: "8A5300",   // âmbar escuro, legível como texto sobre fundo claro
  nevoa: "EEF2F8",        // fundo de cartão e de linha alternada
  borda: "D6E0F0",
  texto: "1F2937",
  suave: "566175",
  branco: "FFFFFF",
  claroNoEscuro: "C9D3E6",
};
const FONTE = "Calibri";

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
const PRIMEIRO_NOME = { 1: "Kevenn", 2: "Thiago", 3: "Daniel", 4: "Luís" };
const TEMA_DO_BLOCO = { 1: "Motivação", 2: "Fontes e integração", 3: "Esquemas", 4: "Consultas e decisões" };
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
pres.theme = { headFontFace: FONTE, bodyFontFace: FONTE };

// ------------------------------------------------------------------ layouts: rodapé e número da página
function layout(nome, fundo, corRodape, corNumero) {
  pres.defineSlideMaster({
    title: nome,
    background: { color: fundo },
    objects: [
      { text: { text: "SCC0245 · Grupo 7 · Rede Municipal Paulistana", options: {
        x: 0.6, y: 7.02, w: 7.5, h: 0.3, fontFace: FONTE, fontSize: 10, color: corRodape, margin: 0 } } },
      { text: { text: `/ ${TOTAL_SLIDES}`, options: {
        x: 12.31, y: 7.0, w: 0.5, h: 0.32, fontFace: FONTE, fontSize: 11, color: corRodape, margin: 0, valign: "middle" } } },
    ],
    slideNumber: { x: 11.79, y: 7.0, w: 0.5, h: 0.32, fontFace: FONTE, fontSize: 11, bold: true, color: corNumero, align: "right" },
  });
}
layout("CLARO", COR.branco, COR.suave, COR.cobalto);
layout("ESCURO", COR.tinta, COR.claroNoEscuro, COR.ambar);
pres.defineSlideMaster({ title: "CAPA", background: { color: COR.tinta } });

// ------------------------------------------------------------------ utilitários
let numero = 0;
let objeto = 0;
const slidesDoBloco = { 1: [], 2: [], 3: [], 4: [] };
const virgula = (n) => String(n).replace(".", ",");
const anim = (ordem) => ({ objectName: `anim:${ordem}:${(objeto += 1)}` });
const sombra = () => ({ type: "outer", blur: 8, offset: 2, angle: 90, color: "1B2A4A", opacity: 0.14 });

function novoSlide(titulo, bloco, minutos, notas, opcoes = {}) {
  const s = pres.addSlide({ masterName: opcoes.master || "CLARO" });
  numero += 1;
  slidesDoBloco[bloco].push(numero);
  const escuro = opcoes.master === "ESCURO";
  if (titulo) {
    s.addText(`BLOCO ${bloco} · ${TEMA_DO_BLOCO[bloco].toUpperCase()} · ${PRIMEIRO_NOME[bloco].toUpperCase()}`, {
      x: 0.6, y: 0.38, w: 12.1, h: 0.3, fontFace: FONTE, fontSize: 12, bold: true, charSpacing: 1,
      color: escuro ? COR.ambar : COR.cobalto, margin: 0, isTextBox: true,
    });
    s.addText(titulo, {
      x: 0.6, y: 0.7, w: 12.1, h: 0.75, fontFace: FONTE, fontSize: 32, bold: true,
      color: escuro ? COR.branco : COR.tinta, margin: 0, isTextBox: true, valign: "middle",
    });
  }
  s.addNotes(`Apresenta: ${BLOCO[bloco]} (bloco ${bloco} de 4). Tempo previsto: ${virgula(minutos)} min.\n\n${notas}`);
  return s;
}

function cartao(s, x, y, w, h, opcoes = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.12,
    fill: { color: opcoes.fundo || COR.branco, transparency: opcoes.transparencia || 0 },
    line: { color: opcoes.borda || (opcoes.fundo ? opcoes.fundo : COR.borda), width: 0.75 },
    shadow: opcoes.semSombra ? undefined : sombra(), ...(opcoes.ordem ? anim(opcoes.ordem) : {}),
  });
}

function texto(s, conteudo, x, y, w, h, opcoes = {}) {
  s.addText(conteudo, {
    x, y, w, h, fontFace: FONTE, fontSize: opcoes.tam || 15, bold: Boolean(opcoes.negrito),
    italic: Boolean(opcoes.italico), color: opcoes.cor || COR.texto, align: opcoes.alinhar || "left",
    valign: opcoes.valign || "top", margin: 0, isTextBox: true, paraSpaceAfter: opcoes.espaco || 0,
    charSpacing: opcoes.espacamento, ...(opcoes.ordem ? anim(opcoes.ordem) : {}),
  });
}

function selo(s, x, y, rotulo, opcoes = {}) {
  const d = opcoes.d || 0.5;
  s.addShape(pres.shapes.OVAL, {
    x, y, w: d, h: d, fill: { color: opcoes.fundo || COR.ambar }, line: { color: opcoes.fundo || COR.ambar },
    ...(opcoes.ordem ? anim(opcoes.ordem) : {}),
  });
  texto(s, rotulo, x, y, d, d, { tam: opcoes.tam || 15, negrito: true, cor: opcoes.cor || COR.tinta,
    alinhar: "center", valign: "middle", ordem: opcoes.ordem });
}

function etiqueta(s, rotulo, x, y, w, opcoes = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h: opcoes.h || 0.34, rectRadius: 0.17, fill: { color: opcoes.fundo || COR.cobalto },
    line: { color: opcoes.fundo || COR.cobalto }, ...(opcoes.ordem ? anim(opcoes.ordem) : {}),
  });
  texto(s, rotulo, x, y, w, opcoes.h || 0.34, { tam: opcoes.tam || 12, negrito: true, cor: opcoes.cor || COR.branco,
    alinhar: "center", valign: "middle", ordem: opcoes.ordem });
}

function itens(lista, tam = 15, cor = COR.texto) {
  return lista.map((t, i) => ({
    text: t, options: { bullet: { indent: 18 }, breakLine: i < lista.length - 1, fontSize: tam, color: cor, paraSpaceAfter: 6 },
  }));
}

function fonte(s, conteudo) {
  texto(s, conteudo, 0.6, 6.66, 11.2, 0.28, { tam: 10, italico: true, cor: COR.suave });
}

function tabela(s, cabecalho, linhas, opcoes) {
  const cab = cabecalho.map((t) => ({ text: t, options: { bold: true, color: COR.branco, fill: { color: COR.tinta } } }));
  const corpo = linhas.map((l, i) => l.map((t, j) => ({
    text: t,
    options: {
      fill: { color: i % 2 ? COR.branco : COR.nevoa },
      bold: Boolean(opcoes.primeiraEmNegrito && j === 0) || Boolean(opcoes.corDaColuna && opcoes.corDaColuna(j, t)),
      color: (opcoes.corDaColuna && opcoes.corDaColuna(j, t)) || COR.texto,
    },
  })));
  s.addTable([cab, ...corpo], {
    fontFace: FONTE, color: COR.texto, border: { type: "solid", color: COR.borda, pt: 0.75 }, valign: "middle",
    margin: [0.06, 0.12, 0.06, 0.12], ...opcoes.tabela,
  });
}

// largura / altura lidas do cabeçalho do PNG, para a figura nunca sair distorcida
function proporcao(arquivo) {
  const cab = fs.readFileSync(FIG(arquivo)).subarray(16, 24);
  return cab.readUInt32BE(0) / cab.readUInt32BE(4);
}

// figura dentro de uma moldura branca com sombra, centrada na caixa (x, y, w, h)
function figuraEmMoldura(s, arquivo, x, y, w, h, descricao, ordem) {
  cartao(s, x, y, w, h, { ordem });
  const p = proporcao(arquivo);
  const largura = Math.min(w - 0.4, (h - 0.3) * p);
  const altura = largura / p;
  s.addImage({ path: FIG(arquivo), x: x + (w - largura) / 2, y: y + (h - altura) / 2, w: largura, h: altura,
    altText: descricao, ...anim(ordem) });
}

// ================================================================== bloco 1: motivação

// ------------------------------------------------------------------ 1. capa
{
  const s = novoSlide(null, 1, 0.5,
    "Abertura. Apresentar o grupo, a disciplina e o tema: política pública municipal de educação. " +
    "Dizer em uma frase a pergunta do trabalho: onde existe fila por vaga, onde existe oferta, se a oferta está cheia, " +
    "quantas crianças moram em cada lugar e o que acontece com quem consegue a vaga.", { master: "CAPA" });
  texto(s, "SCC0245 · PROCESSAMENTO ANALÍTICO DE DADOS · PRIMEIRO TRABALHO PRÁTICO", 0.8, 0.75, 11.5, 0.35,
    { tam: 13, negrito: true, cor: COR.ambar, espacamento: 1 });
  texto(s, "Rede Municipal Paulistana: oferta escolar e demanda não atendida", 0.8, 1.25, 8.0, 1.95,
    { tam: 40, negrito: true, cor: COR.branco });
  texto(s, "Um data warehouse para decidir onde abrir vagas, com dados abertos da SME-SP e do IBGE", 0.8, 3.3, 7.6, 0.8,
    { tam: 18, cor: COR.claroNoEscuro });
  etiqueta(s, "GRUPO 7", 0.8, 4.35, 1.35, { fundo: COR.ambar, cor: COR.tinta, ordem: 1 });
  INTEGRANTES.forEach(([nome, nusp], i) => {
    const x = 0.8 + (i % 2) * 4.05;
    const y = 4.9 + Math.floor(i / 2) * 0.86;
    cartao(s, x, y, 3.85, 0.72, { fundo: COR.branco, transparencia: 90, borda: "3A4D73", semSombra: true, ordem: 2 + i });
    texto(s, nome, x + 0.2, y + 0.07, 3.5, 0.32, { tam: 14, negrito: true, cor: COR.branco, ordem: 2 + i });
    texto(s, `Nº USP ${nusp}`, x + 0.2, y + 0.38, 3.5, 0.26, { tam: 12, cor: COR.claroNoEscuro, ordem: 2 + i });
  });
  [["13,4 mi", "matrículas de 2015 a 2024"], ["44", "meses de fila por distrito"], ["26.889", "setores censitários do Censo 2022"]]
    .forEach(([valor, rotulo], i) => {
      const y = 1.35 + i * 1.55;
      texto(s, valor, 9.35, y, 3.4, 0.75, { tam: 40, negrito: true, cor: COR.ambar, ordem: 6 + i });
      texto(s, rotulo, 9.35, y + 0.75, 3.4, 0.4, { tam: 13, cor: COR.claroNoEscuro, ordem: 6 + i });
    });
  texto(s, "Profa. Dra. Cristina Dutra de Aguiar · ICMC-USP, São Carlos", 0.8, 6.8, 9.0, 0.35,
    { tam: 13, cor: COR.claroNoEscuro });
}

// ------------------------------------------------------------------ 2. roteiro (preenchido no fim)
const roteiro = novoSlide("Roteiro: quatro integrantes, quatro blocos", 1, 0.5,
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
  ], 17), { x: 0.6, y: 1.8, w: 6.2, h: 4.4, fontFace: FONTE, margin: 0, isTextBox: true, valign: "top", ...anim(1) });
  cartao(s, 7.2, 1.75, 5.5, 4.75, { fundo: COR.nevoa, semSombra: true, ordem: 2 });
  texto(s, "FILA DE CRECHE EM JUNHO", 7.55, 1.98, 4.8, 0.3, { tam: 12, negrito: true, cor: COR.suave, espacamento: 1, ordem: 2 });
  texto(s, "2015", 7.55, 2.45, 1.2, 0.4, { tam: 15, negrito: true, cor: COR.suave, ordem: 2 });
  texto(s, "124.741", 7.55, 2.8, 4.5, 0.9, { tam: 48, negrito: true, cor: COR.tinta, ordem: 2 });
  texto(s, "crianças · 34% da demanda fora da rede", 7.55, 3.7, 4.8, 0.35, { tam: 14, cor: COR.texto, ordem: 2 });
  etiqueta(s, "-97%", 11.25, 3.98, 1.1, { fundo: COR.ambar, cor: COR.tinta, tam: 14, h: 0.42, ordem: 3 });
  texto(s, "2024", 7.55, 4.45, 1.2, 0.4, { tam: 15, negrito: true, cor: COR.suave, ordem: 4 });
  texto(s, "3.633", 7.55, 4.8, 4.5, 0.9, { tam: 48, negrito: true, cor: COR.cobalto, ordem: 4 });
  texto(s, "crianças · 1% da demanda fora da rede", 7.55, 5.7, 4.8, 0.35, { tam: 14, cor: COR.texto, ordem: 4 });
  fonte(s, "Fonte: Demanda Registrada e Matrículas (SME-SP); consulta 5 sobre a carga com os dados reais.");
}

// ------------------------------------------------------------------ 4. perguntas do gestor
{
  const s = novoSlide("Perguntas que o data warehouse responde", 1, 1,
    "Quem usa: Secretaria Municipal de Educação e as 13 Diretorias Regionais. Cada cartão é uma decisão real de política " +
    "pública e cita as consultas que a apoiam. Destacar que a capacidade das turmas não é publicada, então medimos a ocupação.");
  const perguntas = [
    ["Onde abrir vagas?", "Fila por distrito e DRE, fila contra matrícula e contra a população de 0 a 4 anos.", ["C1", "C5", "C7"]],
    ["Como a oferta é feita?", "Peso da rede conveniada e da jornada integral na creche e em cada DRE.", ["C3", "C4"]],
    ["Turma nova ou lugar ocioso?", "Alunos por turma em funcionamento, do município ao distrito.", ["C8"]],
    ["Fila e abandono andam juntos?", "Fila de creche e abandono no ensino fundamental, por DRE.", ["C6"]],
  ];
  perguntas.forEach(([t, c, cods], i) => {
    const x = 0.6 + (i % 2) * 6.15;
    const y = 1.75 + Math.floor(i / 2) * 2.5;
    cartao(s, x, y, 5.95, 2.25, { ordem: i + 1 });
    selo(s, x + 0.3, y + 0.32, String(i + 1), { d: 0.6, ordem: i + 1 });
    texto(s, t, x + 1.15, y + 0.3, 4.55, 0.45, { tam: 19, negrito: true, cor: COR.tinta, ordem: i + 1 });
    texto(s, c, x + 1.15, y + 0.8, 4.55, 0.8, { tam: 15, ordem: i + 1 });
    cods.forEach((cod, j) => etiqueta(s, cod, x + 1.15 + j * 0.75, y + 1.68, 0.62, { ordem: i + 1 }));
  });
}

// ------------------------------------------------------------------ 5. por que São Paulo
{
  const s = novoSlide("Por que São Paulo, e não São Carlos", 1, 1,
    "O enunciado temático prioriza São Carlos. Nossa primeira proposta foi dimensionar a oferta escolar por setor censitário " +
    "em São Carlos. Sem dado aberto de vaga nem de fila, a demanda não atendida teria de ser estimada, e o enunciado pede dados reais. " +
    "São Paulo publica o microdado de cada matrícula e a fila por distrito. O modelo não depende de São Paulo: matrícula, turma e desfecho " +
    "vêm do tipo de registro que qualquer sistema de gestão escolar mantém, e o Censo 2022 tem população por setor para todos os municípios.");
  cartao(s, 0.6, 1.75, 5.95, 3.15, { ordem: 1 });
  etiqueta(s, "PRIMEIRA PROPOSTA", 0.9, 2.0, 2.2, { fundo: COR.suave, ordem: 1 });
  texto(s, "São Carlos", 0.9, 2.5, 5.3, 0.55, { tam: 24, negrito: true, cor: COR.tinta, ordem: 1 });
  texto(s, "Oferta escolar por setor censitário. Sem dado aberto de vaga nem de fila, a demanda não atendida teria de ser estimada.",
    0.9, 3.15, 5.3, 1.5, { tam: 16, ordem: 1 });
  cartao(s, 6.75, 1.75, 5.95, 3.15, { ordem: 2 });
  etiqueta(s, "ESCOLHA", 7.05, 2.0, 1.3, { ordem: 2 });
  texto(s, "São Paulo", 7.05, 2.5, 5.3, 0.55, { tam: 24, negrito: true, cor: COR.tinta, ordem: 2 });
  texto(s, "A SME publica o microdado de cada matrícula e a fila de espera por distrito: demanda medida, não estimada. " +
    "13,4 milhões de matrículas de 2015 a 2024.", 7.05, 3.15, 5.3, 1.5, { tam: 16, ordem: 2 });
  cartao(s, 0.6, 5.15, 12.1, 1.35, { fundo: COR.nevoa, semSombra: true, ordem: 3 });
  selo(s, 0.9, 5.52, "✓", { d: 0.6, tam: 18, ordem: 3 });
  s.addText([
    { text: "O modelo vale para São Carlos: ", options: { bold: true, color: COR.tinta } },
    { text: "matrícula, turma e desfecho vêm do registro que todo sistema de gestão escolar mantém, e o Censo 2022 já tem a " +
      "população por setor censitário do município. Falta só a rede registrar e publicar a fila." },
  ], { x: 1.75, y: 5.27, w: 10.7, h: 1.1, fontFace: FONTE, fontSize: 15, color: COR.texto, margin: 0, isTextBox: true,
    valign: "middle", ...anim(3) });
}

// ------------------------------------------------------------------ 6. assuntos de interesse
{
  const s = novoSlide("Cinco assuntos de interesse e por que importam", 1, 1,
    "Os cinco assuntos são os registrados na planilha do grupo, e cada um responde a uma parte da decisão de onde abrir vagas. " +
    "Matrícula é a oferta usada; fila é quem pediu e não conseguiu; ocupação diz se a oferta que existe está cheia; " +
    "população é a demanda potencial, que existe mesmo sem pedido; oferta por setor mostra onde e por qual rede a vaga é oferecida. " +
    "Quatro assuntos viram tabelas de fatos; a oferta por setor é respondida pelas dimensões Escola, Território e Setor Censitário. " +
    "O quinto processo, desfecho da matrícula, acompanha o que acontece depois do acesso.");
  const linhas = [
    ["Matrículas", "oferta efetivamente usada, com o perfil de cada aluno", "fato Matrícula"],
    ["Fila (demanda registrada)", "quem pediu vaga e não foi atendido", "fato Fila"],
    ["Capacidade e ocupação das turmas", "se a oferta existente está cheia: turma nova ou lugar ocioso", "fato Ocupação de Turma"],
    ["População em idade escolar", "demanda potencial, mesmo sem pedido de vaga", "fato População"],
    ["Oferta escolar por setor", "onde e por qual rede (direta ou conveniada) a vaga é oferecida", "dimensões Escola, Território, Setor"],
  ];
  texto(s, "ASSUNTO", 0.75, 1.6, 3.2, 0.28, { tam: 11, negrito: true, cor: COR.suave, espacamento: 1 });
  texto(s, "POR QUE IMPORTA", 4.15, 1.6, 5.0, 0.28, { tam: 11, negrito: true, cor: COR.suave, espacamento: 1 });
  texto(s, "NO MODELO", 9.55, 1.6, 3.0, 0.28, { tam: 11, negrito: true, cor: COR.suave, espacamento: 1 });
  linhas.forEach(([assunto, porque, modelo], i) => {
    const y = 1.95 + i * 0.7;
    cartao(s, 0.6, y, 12.1, 0.6, { fundo: i % 2 ? COR.branco : COR.nevoa, borda: COR.borda, semSombra: true, ordem: i + 1 });
    etiqueta(s, assunto, 0.75, y + 0.11, 3.25, { h: 0.38, tam: 12, ordem: i + 1 });
    texto(s, porque, 4.15, y, 5.25, 0.6, { tam: 15, valign: "middle", ordem: i + 1 });
    texto(s, modelo, 9.55, y, 3.05, 0.6, { tam: 13, negrito: true, cor: COR.cobalto, valign: "middle", ordem: i + 1 });
  });
  cartao(s, 0.6, 5.65, 12.1, 0.9, { fundo: COR.nevoa, semSombra: true, ordem: 6 });
  selo(s, 0.85, 5.82, "5", { d: 0.56, ordem: 6 });
  s.addText([
    { text: "Quinto processo: desfecho da matrícula. ", options: { bold: true, color: COR.tinta } },
    { text: "Acompanha o que acontece depois do acesso: aprovação, reprovação, abandono e transferência." },
  ], { x: 1.65, y: 5.7, w: 10.9, h: 0.8, fontFace: FONTE, fontSize: 15, color: COR.texto, margin: 0, isTextBox: true,
    valign: "middle", ...anim(6) });
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
    ["SME-SP · ANUAL", "Microdados de Matrículas", "13,4 mi", "matrículas de escolarização, 2015 a 2024",
      "Uma linha por vínculo aluno-turma: escola, turma, turno, série, idade, perfil, deficiência, datas e desfecho."],
    ["SME-SP · TRIMESTRAL E BIMESTRAL", "Demanda Registrada e Matrículas", "44 meses", "44 meses (33 arquivos) × 96 distritos no recorte",
      "Por distrito e etapa: matrículas, matrículas em processo e fila. Trimestral até 2022, bimestral desde 2023; sete formatos diferentes."],
    ["IBGE · AGREGADOS POR SETORES", "Censo Demográfico 2022", "26.889", "setores do município, 11,4 milhões de moradores",
      "Pessoas residentes por setor censitário e grupo de idade (variáveis V01031 a V01041); referência 31/07/2022."],
  ];
  fontes.forEach(([quem, nome, valor, rotulo, desc], i) => {
    const x = 0.6 + i * 4.1;
    cartao(s, x, 1.75, 3.9, 4.8, { ordem: i + 1 });
    texto(s, quem, x + 0.3, 1.97, 3.4, 0.3, { tam: 11, negrito: true, cor: COR.ambarTexto, espacamento: 1, ordem: i + 1 });
    texto(s, nome, x + 0.3, 2.3, 3.4, 0.75, { tam: 18, negrito: true, cor: COR.tinta, ordem: i + 1 });
    texto(s, valor, x + 0.3, 3.1, 3.4, 0.75, { tam: 36, negrito: true, cor: COR.cobalto, ordem: i + 1 });
    texto(s, rotulo, x + 0.3, 3.85, 3.4, 0.5, { tam: 12, cor: COR.suave, ordem: i + 1 });
    texto(s, desc, x + 0.3, 4.45, 3.35, 1.95, { tam: 14, ordem: i + 1 });
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
  ], { primeiraEmNegrito: true, tabela: { x: 0.6, y: 1.7, w: 12.1, colW: [1.6, 3.6, 3.3, 3.6], fontSize: 14, rowH: 0.62 } });
  cartao(s, 0.6, 5.0, 12.1, 1.5, { fundo: COR.nevoa, semSombra: true, ordem: 1 });
  texto(s, "< 1%", 0.9, 5.1, 2.2, 1.3, { tam: 44, negrito: true, cor: COR.cobalto, valign: "middle", ordem: 1 });
  s.addText([
    { text: "Reconciliação: ", options: { bold: true, color: COR.tinta } },
    { text: "matrículas ativas em junho no microdado contra a matrícula da planilha de fila, por distrito e etapa: diferença abaixo de 1% de 2015 a 2020 (creche: +0,03% em 2015, +0,17% em 2019)." },
  ], { x: 3.2, y: 5.1, w: 9.3, h: 1.3, fontFace: FONTE, fontSize: 15, color: COR.texto, margin: 0, isTextBox: true,
    valign: "middle", ...anim(1) });
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
    const y = 1.75 + Math.floor(i / 3) * 2.45;
    cartao(s, x, y, 3.9, 2.2, { ordem: i + 1 });
    selo(s, x + 0.25, y + 0.27, String(i + 1), { d: 0.48, tam: 14, ordem: i + 1 });
    texto(s, t, x + 0.9, y + 0.22, 2.8, 0.85, { tam: 15, negrito: true, cor: COR.tinta, ordem: i + 1 });
    texto(s, c, x + 0.3, y + 1.15, 3.35, 0.95, { tam: 14, ordem: i + 1 });
  });
}

// ------------------------------------------------------------------ 10. grão e aditividade
{
  const s = novoSlide("Grão e aditividade dos fatos", 2, 1,
    "Grão declarado antes das dimensões. Matrícula no grão mais fino que a fonte permite; fila no grão em que a prefeitura publica; " +
    "desfecho e ocupação são fatos agregados do fato de matrícula; população no grão do IBGE. " +
    "Fila e população são estoques: somam no território, não no tempo. Taxas e alunos por turma são derivados não aditivos, " +
    "sempre recalculados a partir das somas.");
  const corAditividade = (j, t) => (j !== 3 ? null : t.startsWith("semiaditivo") ? COR.ambarTexto : COR.cobalto);
  tabela(s, ["Tabela de fatos", "Grão", "Fatos", "Aditividade"], [
    ["Matrícula", "vínculo aluno-turma × ano", "quantidade (=1), dias de matrícula", "aditivo"],
    ["Fila", "distrito × mês × etapa", "matrículas, em processo, demanda e categorias", "semiaditivo (estoque)"],
    ["Desfecho", "escola × ano × série", "contagens por desfecho; taxas", "aditivo; taxas não aditivas"],
    ["Ocupação de Turma", "turma × ano", "turmas, matrículas, ativas em junho; alunos por turma", "aditivo; média não aditiva"],
    ["População", "setor censitário × faixa × Censo", "pessoas", "semiaditivo (estoque)"],
  ], { primeiraEmNegrito: true, corDaColuna: corAditividade,
    tabela: { x: 0.6, y: 1.7, w: 12.1, colW: [2.3, 3.1, 4.0, 2.7], fontSize: 15, rowH: 0.66 } });
  [["aditivo", "soma em todas as dimensões", COR.cobalto], ["semiaditivo", "estoque: não soma no tempo", COR.ambarTexto],
    ["não aditivo", "recalculado a partir das somas", COR.suave]].forEach(([rotulo, desc, cor], i) => {
    const x = 0.6 + i * 4.1;
    etiqueta(s, rotulo, x, 5.95, 1.55, { fundo: cor, ordem: i + 1 });
    texto(s, desc, x + 1.7, 5.95, 2.3, 0.34, { tam: 12, cor: COR.suave, valign: "middle", ordem: i + 1 });
  });
}

// ------------------------------------------------------------------ 11. estrela matrícula
{
  const s = novoSlide("Esquema estrela Matrícula", 2, 1,
    "Fato no centro, dez dimensões. Dimensão Data com dois papéis, início e fim da matrícula, como a data de internação e de alta " +
    "do artigo da disciplina: as duas datas permitem contar matrículas ativas em um dia. O fato principal é a ocorrência do vínculo, contada por um campo artificial igual a 1, técnica de tabela de fatos sem fato; a única medida é dias de matrícula. " +
    "Três bugigangas. Duas degeneradas. Escola é mudança lenta tipo 2.");
  figuraEmMoldura(s, "estrela-matricula.png", 0.6, 1.6, 8.2, 5.0,
    "Esquema estrela Matrícula: tabela de fatos Matrícula no centro, ligada a dez dimensões", 1);
  cartao(s, 9.05, 1.6, 3.65, 5.0, { fundo: COR.nevoa, semSombra: true, ordem: 2 });
  s.addText(itens([
    "Data com dois papéis: início e fim da matrícula.",
    "Ocorrência contada por campo artificial (= 1), como em fatos sem fato.",
    "Bugigangas: Perfil, Deficiência, Situação.",
    "Degeneradas: id turma, código da matrícula.",
    "Escola: mudança lenta tipo 2.",
    "Hierarquias: dia ≤ mês ≤ trimestre ≤ semestre ≤ ano; série ≤ etapa ≤ nível; idade ≤ faixa IBGE.",
  ], 14), { x: 9.25, y: 1.8, w: 3.3, h: 4.65, fontFace: FONTE, margin: 0, isTextBox: true, valign: "top", ...anim(2) });
}

// ================================================================== bloco 3: estrelas e constelação

// slide de um esquema estrela largo: figura na largura do slide, leitura do esquema em duas colunas embaixo
function estrela(titulo, arquivo, descricao, lista, notas) {
  const s = novoSlide(titulo, 3, 1, notas);
  figuraEmMoldura(s, arquivo, 0.6, 1.6, 12.1, 4.05, descricao, 1);
  const meio = Math.ceil(lista.length / 2);
  [lista.slice(0, meio), lista.slice(meio)].forEach((coluna, i) => {
    s.addText(itens(coluna, 15), { x: 0.6 + i * 6.15, y: 5.85, w: 5.95, h: 1.05, fontFace: FONTE, margin: 0,
      isTextBox: true, valign: "top", ...anim(2) });
  });
  return s;
}

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
  figuraEmMoldura(s, "constelacao.png", 0.6, 1.6, 12.1, 4.8,
    "Constelação de fatos: cinco tabelas de fatos e catorze dimensões compartilhadas", 1);
  texto(s, "Processo de projeto: matriz de barramento (fato × dimensão), dimensões conformadas e, onde os grãos diferem, rollups encolhidos (tracejado).",
    0.6, 6.5, 12.1, 0.4, { tam: 13, italico: true, cor: COR.suave, ordem: 2 });
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
  const corOperacao = (j, t) => (j !== 1 ? null : t === "drill-across" ? COR.ambarTexto : COR.cobalto);
  tabela(s, ["", "Operação", "Pergunta", "Fatos"], linhas,
    { primeiraEmNegrito: true, corDaColuna: corOperacao,
      tabela: { x: 0.6, y: 1.6, w: 12.1, colW: [0.7, 2.0, 6.0, 3.4], fontSize: 14, rowH: 0.54 } });
  texto(s, "Exigido: 2 roll-up ou drill-down, 1 slice and dice, 1 pivot, 1 drill-across. Feito: 3, 1, 1 e 3.",
    0.6, 6.55, 12.1, 0.32, { tam: 13, negrito: true, cor: COR.tinta, ordem: 1 });
}

// ------------------------------------------------------------------ 18. resultados: fila e oferta
{
  const s = novoSlide("Resultados: fila e oferta de creche", 4, 1,
    "Consulta 5 na carga com os dados reais de 2015 a 2024. A fila de creche em junho caiu 97% em dez anos e a " +
    "fração da demanda fora da rede passou de 34% para 1%. A queda maior foi de 2017 a 2021. " +
    "Consulta 3: 85% das matrículas de creche estão na rede conveniada, quase todas em jornada integral, em 2019 e em 2024.");
  const anos = ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"];
  const eixos = { catAxisLabelColor: COR.suave, valAxisLabelColor: COR.suave, catAxisLabelFontFace: FONTE,
    valAxisLabelFontFace: FONTE, catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, dataLabelFontFace: FONTE,
    dataLabelColor: COR.texto, titleColor: COR.tinta, titleFontFace: FONTE, titleFontSize: 15,
    catGridLine: { style: "none" }, showLegend: false };
  s.addChart(pres.charts.BAR, [{ name: "Fila de creche em junho", labels: anos,
    values: [124741, 103496, 104268, 66714, 48910, 22732, 8767, 4761, 4913, 3633] }], {
    x: 0.5, y: 1.55, w: 6.4, h: 5.0, barDir: "col", chartColors: [COR.cobalto], showTitle: true,
    title: "Crianças na fila de creche em junho", showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 9,
    dataLabelFormatCode: "#,##0", valAxisLabelFormatCode: "#,##0", valGridLine: { color: "E3E8F0", size: 0.5 }, ...eixos,
  });
  s.addChart(pres.charts.LINE, [{ name: "Fração fora da rede", labels: anos,
    values: [34.1, 27.1, 26.6, 17.5, 12.8, 6.2, 2.4, 1.3, 1.4, 1.1] }], {
    x: 7.0, y: 1.55, w: 5.8, h: 3.25, chartColors: [COR.ambar], lineSize: 3, lineDataSymbol: "circle",
    lineDataSymbolSize: 8, showTitle: true, title: "Fração da demanda de creche fora da rede (%)", showValue: true,
    dataLabelPosition: "t", dataLabelFontSize: 9, dataLabelFormatCode: "0.0", valGridLine: { color: "E3E8F0", size: 0.5 }, ...eixos,
  });
  cartao(s, 7.05, 4.95, 5.65, 1.55, { fundo: COR.nevoa, semSombra: true, ordem: 1 });
  texto(s, "85%", 7.3, 5.05, 1.7, 1.35, { tam: 40, negrito: true, cor: COR.cobalto, valign: "middle", ordem: 1 });
  texto(s, "da creche é conveniada, quase toda em jornada integral, em 2019 e 2024 (consulta 3).", 9.05, 5.05, 3.5, 1.35,
    { tam: 14, valign: "middle", ordem: 1 });
  fonte(s, "Fonte: SME-SP, Demanda Registrada e Matrículas e Microdados de Matrículas; consultas 3 e 5.");
}

// ------------------------------------------------------------------ 19. resultados: população e ocupação
{
  const s = novoSlide("Resultados: população e ocupação das turmas", 4, 1,
    "Consulta 7, na data do Censo: 598.406 crianças de 0 a 4 anos moram no município e a rede municipal tinha 514.131 matrículas " +
    "ativas dessa idade, 86 por 100. A média esconde distâncias grandes: 25 distritos têm menos de 50 matrículas por 100 crianças " +
    "residentes e outros 25 passam de 100, porque a matrícula conta onde a escola fica e a população onde a criança mora. " +
    "Consulta 8: a creche funciona com perto de 11 crianças por turma em todas as DREs; no fundamental são de 28 a 32.");
  cartao(s, 0.6, 1.6, 5.95, 2.6, { ordem: 1 });
  texto(s, "CONSULTA 7 · 31/07/2022", 0.9, 1.82, 5.3, 0.3, { tam: 12, negrito: true, cor: COR.ambarTexto, espacamento: 1, ordem: 1 });
  texto(s, "86", 0.9, 2.15, 1.6, 1.05, { tam: 60, negrito: true, cor: COR.cobalto, ordem: 1 });
  texto(s, "matrículas por 100 crianças de 0 a 4 anos", 2.45, 2.35, 3.9, 0.75, { tam: 17, negrito: true, cor: COR.tinta, ordem: 1 });
  texto(s, "514.131 matrículas ativas para 598.406 crianças residentes.", 0.9, 3.35, 5.4, 0.6, { tam: 14, cor: COR.suave, ordem: 1 });
  cartao(s, 0.6, 4.4, 5.95, 2.15, { fundo: COR.nevoa, semSombra: true, ordem: 2 });
  texto(s, "Por distrito, longe da média", 0.9, 4.58, 5.3, 0.4, { tam: 17, negrito: true, cor: COR.tinta, ordem: 2 });
  texto(s, "25 distritos com menos de 50 matrículas por 100 crianças; outros 25 com mais de 100. " +
    "A matrícula conta onde a escola fica; a população, onde a criança mora.", 0.9, 5.05, 5.4, 1.4, { tam: 14, ordem: 2 });
  s.addChart(pres.charts.BAR, [
    { name: "2019", labels: ["Creche", "Pré-escola", "Fund. iniciais", "Fund. finais"], values: [11.5, 30.7, 28.7, 29.4] },
    { name: "2024", labels: ["Creche", "Pré-escola", "Fund. iniciais", "Fund. finais"], values: [11.0, 26.9, 30.6, 31.6] },
  ], {
    x: 6.85, y: 1.55, w: 5.95, h: 5.05, barDir: "col", barGrouping: "clustered", chartColors: [COR.cobalto, COR.ambar],
    showTitle: true, title: "Alunos por turma em 30 de junho (consulta 8)", titleFontSize: 15, titleColor: COR.tinta,
    titleFontFace: FONTE, showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelFormatCode: "0.0",
    dataLabelColor: COR.texto, dataLabelFontFace: FONTE, catAxisLabelColor: COR.suave, valAxisLabelColor: COR.suave,
    catAxisLabelFontFace: FONTE, valAxisLabelFontFace: FONTE, valGridLine: { color: "E3E8F0", size: 0.5 },
    catGridLine: { style: "none" }, showLegend: true, legendPos: "b", legendFontSize: 12, legendColor: COR.texto,
    legendFontFace: FONTE, catAxisLabelFontSize: 12, valAxisLabelFontSize: 10, valAxisMinVal: 0,
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
    const y = 1.65 + Math.floor(i / 2) * 1.68;
    cartao(s, x, y, 5.95, 1.48, { ordem: i + 1 });
    selo(s, x + 0.3, y + 0.44, n, { d: 0.6, ordem: i + 1 });
    texto(s, t, x + 1.15, y + 0.2, 4.6, 0.42, { tam: 17, negrito: true, cor: COR.tinta, ordem: i + 1 });
    texto(s, c, x + 1.15, y + 0.66, 4.6, 0.7, { tam: 14, ordem: i + 1 });
  });
}

// ------------------------------------------------------------------ 21. encerramento
{
  const s = novoSlide("Obrigado. Perguntas?", 4, 0.5,
    "Encerramento. Lembrar que o relatório em PDF traz a descrição completa de cada atributo, com a coluna de origem e a integração, " +
    "e que o repositório tem o pipeline completo, os testes e a documentação. Abrir para perguntas.", { master: "ESCURO" });
  [["13,4 mi", "matrículas de 2015 a 2024"], ["551 mil", "turmas carregadas"], ["26.889", "setores censitários"]]
    .forEach(([valor, rotulo], i) => {
      const x = 0.6 + i * 4.1;
      cartao(s, x, 1.75, 3.9, 1.5, { fundo: COR.branco, transparencia: 90, borda: "3A4D73", semSombra: true, ordem: i + 1 });
      texto(s, valor, x + 0.3, 1.88, 3.3, 0.75, { tam: 34, negrito: true, cor: COR.ambar, ordem: i + 1 });
      texto(s, rotulo, x + 0.3, 2.63, 3.3, 0.45, { tam: 14, cor: COR.claroNoEscuro, ordem: i + 1 });
    });
  s.addText(itens([
    "Relatório: descrição do problema, povoamento atributo por atributo, cinco estrelas, constelação e oito consultas.",
    "Repositório: pipeline do portal ao DuckDB, 14 verificações de qualidade e testes automáticos, inclusive da modelagem.",
    "Carga real: 13,4 milhões de matrículas, 551 mil turmas e 26.889 setores censitários em 3,5 minutos, sem nenhuma FALHA nas verificações.",
  ], 16, COR.branco), { x: 0.6, y: 3.55, w: 12.0, h: 2.0, fontFace: FONTE, margin: 0, isTextBox: true, valign: "top", ...anim(4) });
  texto(s, "github.com/kevennlaranjeira/OLAP2026", 0.6, 5.7, 11.8, 0.45, { tam: 18, negrito: true, cor: COR.ambar, ordem: 5 });
  texto(s, INTEGRANTES.map(([n]) => n).join("  ·  "), 0.6, 6.3, 11.8, 0.4, { tam: 14, cor: COR.claroNoEscuro, ordem: 5 });
}

// ------------------------------------------------------------------ roteiro, a partir dos blocos montados
for (let b = 1; b <= 4; b += 1) {
  const x = 0.6 + (b - 1) * 3.075;
  const lista = slidesDoBloco[b];
  cartao(roteiro, x, 1.75, 2.9, 4.8, { ordem: b });
  selo(roteiro, x + 0.25, 2.0, String(b), { d: 0.6, ordem: b });
  texto(roteiro, BLOCO[b], x + 0.25, 2.75, 2.45, 0.75, { tam: 16, negrito: true, cor: COR.tinta, ordem: b });
  texto(roteiro, `slides ${lista[0]} a ${lista[lista.length - 1]}`, x + 0.25, 3.5, 2.45, 0.32,
    { tam: 13, negrito: true, cor: COR.cobalto, ordem: b });
  texto(roteiro, ASSUNTO_DO_BLOCO[b], x + 0.25, 3.95, 2.45, 2.4, { tam: 16, ordem: b });
}

if (numero !== TOTAL_SLIDES) throw new Error(`a apresentação tem ${numero} slides, e o rodapé diz ${TOTAL_SLIDES}`);

// ------------------------------------------------------------------ tema, transições e animações
// O pptxgenjs não escreve as cores do tema nem animações: os dois entram no XML depois de gerado.
const PALETA_TEMA = { dk2: COR.tinta, lt2: COR.nevoa, accent1: COR.cobalto, accent2: COR.ambar, accent3: COR.suave,
  accent4: "8FA6CB", accent5: COR.ambarTexto, accent6: COR.borda };
const PASSO_MS = 250;     // intervalo entre um grupo e o seguinte
const DURACAO_MS = 400;   // duração de cada esmaecimento

function tempos(alvos) {
  const grupos = [...new Set(alvos.map((a) => a.ordem))].sort((a, b) => a - b);
  let id = 3;
  const efeitos = [];
  grupos.forEach((g, i) => {
    for (const a of alvos.filter((x) => x.ordem === g)) {
      const [externo, efeito, visivel, fade] = [++id, ++id, ++id, ++id];
      efeitos.push(
        `<p:par><p:cTn id="${externo}" fill="hold"><p:stCondLst><p:cond delay="${i * PASSO_MS}"/></p:stCondLst><p:childTnLst>` +
        `<p:par><p:cTn id="${efeito}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" grpId="0" nodeType="withEffect">` +
        `<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>` +
        `<p:set><p:cBhvr><p:cTn id="${visivel}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>` +
        `<p:tgtEl><p:spTgt spid="${a.id}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>` +
        `</p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>` +
        `<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="${fade}" dur="${DURACAO_MS}"/>` +
        `<p:tgtEl><p:spTgt spid="${a.id}"/></p:tgtEl></p:cBhvr></p:animEffect>` +
        `</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>`);
    }
  });
  const construcao = alvos.filter((a) => a.tipo === "sp").map((a) => `<p:bldP spid="${a.id}" grpId="0" animBg="1"/>`).join("");
  return `<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>` +
    `<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>` +
    `<p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>` +
    `</p:stCondLst><p:childTnLst>${efeitos.join("")}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn>` +
    `<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>` +
    `<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>` +
    `</p:childTnLst></p:cTn></p:par></p:tnLst>${construcao ? `<p:bldLst>${construcao}</p:bldLst>` : ""}</p:timing>`;
}

async function finalizar(buffer) {
  const JSZip = require(require.resolve("jszip", { paths: [path.dirname(require.resolve(MODULO_PPTX))] }));
  const zip = await JSZip.loadAsync(buffer);
  const tema = "ppt/theme/theme1.xml";
  let xmlTema = await zip.file(tema).async("string");
  for (const [nome, cor] of Object.entries(PALETA_TEMA)) {
    xmlTema = xmlTema.replace(new RegExp(`<a:${nome}>\\s*<a:srgbClr val="[0-9A-Fa-f]{6}"\\s*/>\\s*</a:${nome}>`),
      `<a:${nome}><a:srgbClr val="${cor}"/></a:${nome}>`);
  }
  zip.file(tema, xmlTema);
  const slides = Object.keys(zip.files).filter((n) => /^ppt\/slides\/slide\d+\.xml$/.test(n));
  for (const nome of slides) {
    let xml = await zip.file(nome).async("string");
    const alvos = [...xml.matchAll(/<p:(sp|pic)>\s*<p:nv(?:Sp|Pic)Pr>\s*<p:cNvPr id="(\d+)" name="anim:(\d+):/g)]
      .map((m) => ({ tipo: m[1], id: m[2], ordem: Number(m[3]) }));
    const extra = `<p:transition spd="med"><p:fade/></p:transition>${alvos.length ? tempos(alvos) : ""}`;
    if (!xml.includes("</p:clrMapOvr>")) throw new Error(`${nome}: sem clrMapOvr para inserir a transição`);
    xml = xml.replace("</p:clrMapOvr>", `</p:clrMapOvr>${extra}`);
    zip.file(nome, xml);
  }
  return zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
}

const destino = process.argv[2] || path.join(AQUI, "apresentacao-projeto1.pptx");
pres.write({ outputType: "nodebuffer" })
  .then(finalizar)
  .then((buffer) => { fs.writeFileSync(destino, buffer); console.log(`gravado: ${destino}`); });
