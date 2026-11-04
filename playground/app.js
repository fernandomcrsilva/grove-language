// Grove Online: liga o editor, o Python do navegador (worker.js) e as abas de saída.
import { criarEditor } from "./editor.js";

const $ = (s) => document.querySelector(s);
const TEMPO_MAXIMO = 5000;  // ms; depois disso o programa é interrompido (laço infinito)
const GUARDADO = "grove-online";  // localStorage: { fonte, nome }
const RECOMPENSA = 250000;  // o dinheiro do HESOYAM, por missão cumprida

// [cheat, classe do realce, papel na Grove, efeito no jogo, modelo inserido; ⟨ ⟩ = trecho que fica selecionado]
const CHEATS = [
  ["HESOYAM", "decl", "declara variável", "vida, colete e $250.000", "HESOYAM ⟨nome⟩ = 0;"],
  ["TURNUPTHEHEAT", "ctrl", "if", "+2 estrelas de procurado", "TURNUPTHEHEAT (⟨condição⟩) {\n    \n}"],
  ["BRINGITON", "ctrl", "else if", "6 estrelas de procurado", "BRINGITON (⟨condição⟩) {\n    \n}"],
  ["TURNDOWNTHEHEAT", "ctrl", "else", "zera o nível de procurado", "TURNDOWNTHEHEAT {\n    ⟨⟩\n}"],
  ["KANGAROO", "ctrl", "while", "pulo gigante", "KANGAROO (⟨condição⟩) {\n    \n}"],
  ["GOODBYECRUELWORLD", "ctrl", "break", "CJ morre na hora", "GOODBYECRUELWORLD;"],
  ["HELLOLADIES", "decl", "imprime", "sex appeal no máximo", "HELLOLADIES ⟨valor⟩;"],
  ["FULLCLIP", "lit", "verdadeiro", "munição infinita", "FULLCLIP"],
  ["GHOSTTOWN", "lit", "falso", "ruas vazias", "GHOSTTOWN"],
];

// fim de missão, como no jogo; as falas são as da CLI (grove/sounds.py)
const MISSAO = {
  ok: ["ok", "Mission passed!", "Respect +"],
  "léxico": ["wasted", "Wasted", "a Grove não conhece um caractere do seu código"],
  "sintático": ["falhou", "Mission failed!", "All you had to do was follow the damn train, CJ!"],
  "semântico": ["busted", "Busted", "a polícia achou os erros antes de você sair de casa"],
  "execução": ["wasted", "Wasted", "Ah shit, here we go again."],
  tempo: ["falhou", "Mission failed!", "o programa passou de 5 s: faltou um GOODBYECRUELWORLD?"],
  parado: ["falhou", "Mission failed!", "você parou o programa"],
};

// as falas que tocam no fim de cada execução: os mesmos assets/<evento>.wav da CLI (grove/sounds.py)
const SOM = { ok: "passed", "léxico": "lex_error", "sintático": "parse_error", "semântico": "semantic_error",
  "execução": "runtime_error", tempo: "runtime_error" };
const PREF_SOM = "grove-online-som";

const ETAPA_ANTES = { lexico: "léxico", sintatico: "sintático", semantico: "semântico" };
const reduzMovimento = matchMedia("(prefers-reduced-motion: reduce)").matches;
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

let worker, pronto = false, primeiraVez = true, falhaCarga = null;
let seq = 0, idCompilacao = 0, idExecucao = 0, relogio = null, espera = null;
let compilado = null;   // o que o worker devolveu da última compilação
let execucao = null;    // { saida, erro, fim, fonte, rodando } da última execução
let carregando = { pct: 0, texto: "" };
let alvoPython = "python", nome = "main.cj", dinheiro = 0, estrelas = -1, ultimaMissao = "";
let somLigado = (() => { try { return localStorage.getItem(PREF_SOM) !== "desligado"; } catch (_) { return true; } })();
const sons = {};  // evento → Audio; null quando o arquivo não existe
let avisouSemSom = false;

const editor = criarEditor({
  area: $("#fonte"),
  realce: $("#realce"),
  numeros: $("#numeros"),
  aoMudar() {
    guardar();
    clearTimeout(espera);
    espera = setTimeout(() => enviar(false), 300);  // compila enquanto digita; executar é no botão
  },
  aoMoverCursor(linha, coluna) {
    $("#posicao").textContent = `Ln ${linha}, Col ${coluna}`;
  },
});

// ---- o Python, num worker: um laço infinito não trava a página ----
function iniciarWorker() {
  pronto = false;
  desenharBotao();
  const local = new URLSearchParams(location.search).get("pyodide");  // cópia local do Pyodide: ver worker.js
  worker = new Worker(local ? `worker.js?pyodide=${encodeURIComponent(local)}` : "worker.js", { type: "module" });
  worker.onmessage = ({ data }) => receber[data.tipo](data);
  worker.onerror = (e) => receber.falhou({ mensagem: e.message || "erro no worker" });
}

const receber = {
  progresso({ pct, texto }) {
    carregando = { pct, texto };
    if (!compilado) desenharConsole();
  },
  pronto({ versao }) {
    pronto = true;
    $("#versao").textContent = `Python ${versao} no navegador (Pyodide)`;
    enviar(primeiraVez, true);  // na primeira vez já roda o programa aberto, sem som
    primeiraVez = false;
    desenharBotao();
  },
  falhou({ mensagem }) {
    falhaCarga = mensagem;
    $("#versao").textContent = "o Python não carregou";
    desenharConsole();
  },
  compilado(d) {
    if (d.id === idExecucao && d.erros.length) {  // tem erro: não vai executar
      clearTimeout(relogio);
      if (execucao && !execucao.automatica) tocar(d.erros[0].tipo);
      execucao = null;
    }
    if (d.id !== idCompilacao) return;
    compilado = d;
    mostrar();
  },
  executado(d) {
    if (d.id !== idExecucao) return;
    clearTimeout(relogio);
    Object.assign(execucao, { saida: d.saida, erro: d.erro, fim: d.erro ? "execução" : "ok", rodando: false });
    if (!d.erro) ganhar(RECOMPENSA);
    if (!execucao.automatica) tocar(execucao.fim);
    mostrar();
  },
};

function enviar(executar, automatica = false) {
  if (!pronto) {
    if (executar) avisar("O Python ainda está carregando.");
    return;
  }
  const id = ++seq;
  idCompilacao = id;
  if (executar) {
    idExecucao = id;
    execucao = { saida: [], erro: null, fim: null, fonte: editor.valor(), rodando: true, automatica };
    clearTimeout(relogio);
    relogio = setTimeout(() => interromper("tempo"), TEMPO_MAXIMO);
    abrirAba($("#tab-console"));
    mostrar();
  }
  worker.postMessage({ id, src: editor.valor(), executar });
}

function interromper(fim) {
  clearTimeout(relogio);
  worker.terminate();
  Object.assign(execucao, {
    rodando: false,
    fim,
    erro: fim === "tempo" ? `tempo esgotado: o programa rodou por mais de ${TEMPO_MAXIMO / 1000} s` : "programa interrompido",
  });
  if (!execucao.automatica) tocar(fim);
  mostrar();
  iniciarWorker();  // um Python novo, em ~2 s
}

// ---- desenho ----
function mostrar() {
  const d = compilado;
  const mudou = execucao && execucao.fonte !== editor.valor();
  for (const el of document.querySelectorAll(".etapa")) {
    const e = el.dataset.etapa;
    el.dataset.estado = e !== "execucao" ? (d?.etapas[e] || "")
      : !execucao || mudou ? "" : execucao.rodando ? "rodando" : execucao.erro ? "erro" : "ok";
  }
  desenharEstrelas(d?.erros.length ? Math.min(6, d.erros.length) : execucao && !mudou && execucao.erro ? 1 : 0);
  desenharBotao();
  if (!d) return desenharConsole();
  editor.marcar(d.erros.map((x) => x.linha), d.avisos.map((x) => x.linha));
  const parou = d.erros.length
    ? `Não chegou nesta etapa: o programa parou no erro ${d.erros[0].tipo}.` : "";
  $("#aba-tokens").innerHTML = d.tokens ? tabela(d.tokens) : vazio(parou);
  $("#aba-ast").innerHTML = d.ast ? `<pre class="codigo">${esc(d.ast)}</pre>` : vazio(parou);
  $("#aba-simbolos").innerHTML = d.simbolos === undefined ? vazio(parou)
    : d.simbolos.includes("\n") ? tabela(d.simbolos) : vazio("O programa não declara variáveis.");
  $("#aba-ir").innerHTML = d.ir === undefined ? vazio(parou)
    : d.ir ? `<pre class="codigo">${tac(d.ir)}</pre>` : vazio("Programa vazio.");
  $("#aba-python").innerHTML = d.python === undefined ? vazio(parou) : python(d);
  desenharConsole();
}

function desenharConsole() {
  $("#aba-console").innerHTML = htmlConsole();
}

function htmlConsole() {
  let h = `<div class="prompt">grove ${esc(nome)}</div>`;
  const d = compilado;
  if (!d) {
    if (falhaCarga) {
      return h + `<p class="falha">Não deu para carregar o Python: ${esc(falhaCarga)}</p>
        <p class="nota">Confira a conexão e recarregue a página. Para apresentar sem internet, veja "Sem internet" no README do repositório.</p>`;
    }
    return h + `<div class="carregando"><span class="gta carregando-titulo">Carregando…</span>
      <div class="barra" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${carregando.pct}" aria-label="Carregando o Python">
      <div class="barra-cheia" style="width:${carregando.pct}%"></div></div>
      <span class="carregando-passo">${esc(carregando.texto || "preparando")}</span></div>`;
  }
  const diags = [...d.erros.map((x) => ["erro", x]), ...d.avisos.map((x) => ["aviso", x])];
  if (diags.length) {
    h += `<ul class="diagnosticos">${diags.map(([cls, x]) => `<li><button type="button" class="diag ${cls}"
      data-linha="${x.linha ?? ""}" data-coluna="${x.coluna ?? ""}"><span class="diag-onde">${esc(nome)}${x.linha ? `:${x.linha}:${x.coluna}` : ""}:</span>
      <span class="diag-tipo">${cls === "erro" ? `erro ${esc(x.tipo)}` : "aviso"}:</span> <span class="diag-msg">${esc(x.mensagem)}</span></button></li>`).join("")}</ul>`;
  }
  if (d.erros.length) {
    return h + `<p class="nota">Clique num erro para ir até a linha.</p>` + missao(d.erros[0].tipo);
  }
  if (!execucao) {
    return h + `<p class="nota">Aperte <strong>Executar</strong> ou <kbd>Ctrl</kbd> + <kbd>Enter</kbd> para rodar.</p>`;
  }
  if (execucao.rodando) return h + `<p class="nota">rodando…</p>`;
  const mudou = execucao.fonte !== editor.valor();
  const linhas = execucao.saida.map(esc).join("\n");
  const falha = execucao.erro ? `${linhas ? "\n" : ""}<span class="falha">erro: ${esc(execucao.erro)}</span>` : "";
  const nada = !linhas && !falha ? `<span class="nota">(o programa não imprimiu nada)</span>` : "";
  h += `<pre class="saida${mudou ? " velha" : ""}">${linhas}${falha}${nada}</pre>`;
  if (mudou) return h + `<p class="nota">O código mudou desde a última execução.</p>`;
  return h + missao(execucao.fim);
}

function missao(tipo) {
  const [classe, titulo, sub] = MISSAO[tipo];
  const chave = `${tipo}|${execucao?.fonte ?? ""}|${compilado?.erros.length}`;
  const fixa = chave === ultimaMissao || reduzMovimento ? " fixa" : "";  // anima só quando o resultado é novo
  ultimaMissao = chave;
  return `<div class="missao ${classe}${fixa}"><span class="gta missao-titulo">${esc(titulo)}</span>
    <span class="gta missao-sub">${esc(sub)}</span></div>`;
}

function desenharEstrelas(n) {
  if (n === estrelas) return;
  const el = $("#estrelas");
  el.innerHTML = Array.from({ length: 6 }, (_, i) => `<svg class="estrela${i < n ? " acesa" : ""}" viewBox="0 0 24 24" aria-hidden="true">
    <path d="M12 1.5l3.1 6.6 7.2.9-5.3 5 1.4 7.1L12 17.6l-6.4 3.5 1.4-7.1-5.3-5 7.2-.9z"/></svg>`).join("");
  el.setAttribute("aria-label", `Nível de procurado: ${n} de 6`);
  el.classList.remove("piscando");
  if (n > estrelas && estrelas >= 0) {
    void el.offsetWidth;  // reinicia a animação
    el.classList.add("piscando");
  }
  estrelas = n;
}

function ganhar(valor) {
  const de = dinheiro, ate = (dinheiro += valor);
  const pintar = (v) => { $("#dinheiro").textContent = "$" + String(v).padStart(8, "0"); };
  if (reduzMovimento) return pintar(ate);
  const t0 = performance.now();
  const passo = (t) => {
    const k = Math.min(1, (t - t0) / 900);
    pintar(Math.round(de + (ate - de) * k));
    if (k < 1) requestAnimationFrame(passo);
  };
  requestAnimationFrame(passo);
}

function desenharBotao() {
  const b = $("#executar"), rodando = execucao?.rodando;
  b.disabled = !pronto && !rodando;
  b.classList.toggle("parar", !!rodando);
  b.querySelector(".executar-rotulo").textContent = rodando ? "Parar" : "Executar";
}

const vazio = (texto) => `<p class="vazio">${esc(texto)}</p>`;

function tabela(tsv) {
  const [cab, ...linhas] = tsv.split("\n").map((l) => l.split("\t"));
  return `<table><thead><tr>${cab.map((c) => `<th scope="col">${esc(c)}</th>`).join("")}</tr></thead><tbody>${
    linhas.map((l) => `<tr>${l.map((c) => `<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}

function tac(texto) {
  return texto.split("\n").map((l) => {
    const m = l.match(/^(\s*\d+)(\s+)(.*)$/);
    if (!m) return esc(l);
    const corpo = /^L\d+:$/.test(m[3]) ? `<span class="rotulo">${esc(m[3])}</span>` : esc(m[3]);
    return `<span class="num">${m[1]}</span>${m[2]}${corpo}`;
  }).join("\n");
}

function python(d) {
  const botoes = [["python", "Python"], ["esp32", "MicroPython · ESP32"]]
    .map(([v, n]) => `<button type="button" data-alvo="${v}" aria-pressed="${alvoPython === v}">${n}</button>`).join("");
  const nota = alvoPython === "esp32"
    ? `A variável inteira <code>estrelas</code> pisca o LED no GPIO 2: quanto mais estrelas, mais rápido. Na CLI: <code>python -m grove arquivo.cj --esp32</code>.`
    : `O mesmo programa, traduzido da AST. Na CLI: <code>python -m grove arquivo.cj --python | python3</code>.`;
  return `<div class="alternar" role="group" aria-label="Alvo">${botoes}</div><p class="nota">${nota}</p>
    <pre class="codigo">${esc(d[alvoPython])}</pre>`;
}

// ---- falas do jogo ----
// Os áudios são da Rockstar e não vão para o repositório: cada um coloca os seus em assets/
// (ver assets/README.md). Sem o arquivo, o app fica em silêncio e avisa uma vez.
function tocar(fim) {
  const evento = SOM[fim];
  if (!somLigado || !evento || sons[evento] === null) return;
  const audio = (sons[evento] ??= carregarSom(evento));
  for (const outro of Object.values(sons)) if (outro && outro !== audio) outro.pause();
  audio.currentTime = 0;
  audio.play().catch(() => {});  // o navegador pode recusar som sem um clique: tudo bem
}

function carregarSom(evento) {
  const audio = new Audio(), formatos = ["wav", "mp3"];
  const proximo = () => { audio.src = `../assets/${evento}.${formatos.shift()}`; };
  audio.addEventListener("error", () => {
    if (formatos.length) {
      proximo();
      audio.play().catch(() => {});
    } else {
      sons[evento] = null;
      if (!avisouSemSom) {
        avisouSemSom = true;
        avisar(`Sem a fala do jogo: falta assets/${evento}.wav (veja assets/README.md).`);
      }
    }
  });
  proximo();
  return audio;
}

function desenharSom() {
  const b = $("#som");
  b.setAttribute("aria-pressed", somLigado);
  b.title = somLigado ? "Falas do jogo ligadas: clique para desligar" : "Falas do jogo desligadas: clique para ligar";
  b.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9h4l5-4v14l-5-4H4z" fill="currentColor"/>${somLigado
    ? '<path d="M16 8.5a5 5 0 0 1 0 7M18.5 6a8.5 8.5 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
    : '<path d="M16.5 9.5l5 5m0-5l-5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'}</svg>`;
}

// ---- arquivo: guardar, abrir, baixar, compartilhar ----
function guardar() {
  try {
    localStorage.setItem(GUARDADO, JSON.stringify({ fonte: editor.valor(), nome }));
    $("#salvo").textContent = "salvo neste navegador";
  } catch (_) { /* sem armazenamento: tudo bem */ }
}

function guardado() {
  try { return JSON.parse(localStorage.getItem(GUARDADO)); } catch (_) { return null; }
}

function abrirTexto(texto, novoNome) {
  nome = novoNome;
  $("#nome-arquivo").textContent = nome;
  editor.definir(texto);
  guardar();
}

function codificar(texto) {  // UTF-8 → base64url, para caber no endereço
  let bin = "";
  for (const b of new TextEncoder().encode(texto)) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function decodificar(s) {
  const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/"));
  return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
}

function codigoDoLink() {
  const m = location.hash.match(/^#c=([\w-]+)$/);
  if (!m) return null;
  try { return decodificar(m[1]); } catch (_) { return null; }
}

async function compartilhar() {
  const url = `${location.href.split("#")[0]}#c=${codificar(editor.valor())}`;
  try {
    await navigator.clipboard.writeText(url);
    avisar("Link copiado: quem abrir vê este código.");
  } catch (_) {
    prompt("Copie o link:", url);
  }
}

function baixar() {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([editor.valor()], { type: "text/plain" }));
  a.download = nome;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

async function exemplo(nomeExemplo) {
  const resp = await fetch(`../examples/${nomeExemplo}.cj`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.text();
}

let toastRelogio;
function avisar(texto) {
  const t = $("#toast");
  t.textContent = texto;
  t.hidden = false;
  clearTimeout(toastRelogio);
  toastRelogio = setTimeout(() => { t.hidden = true; }, 3200);
}

// ---- abas ----
const abas = [...document.querySelectorAll('[role="tab"]')];
function abrirAba(tab) {
  for (const t of abas) {
    const sel = t === tab;
    t.setAttribute("aria-selected", sel);
    t.tabIndex = sel ? 0 : -1;
    document.getElementById(t.getAttribute("aria-controls")).hidden = !sel;
  }
}
for (const t of abas) {
  t.addEventListener("click", () => abrirAba(t));
  t.addEventListener("keydown", (e) => {
    const i = abas.indexOf(t), j = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : null;
    if (j === null) return;
    const alvo = abas.at(j % abas.length);
    alvo.focus();
    abrirAba(alvo);
  });
}

// ---- eventos ----
$("#lista-cheats").innerHTML = CHEATS.map(([cheat, classe, papel, efeito], i) => `<li><button type="button" class="cheat" data-i="${i}"
  title="No jogo: ${esc(efeito)}"><span class="cheat-nome c-${classe}">${cheat}</span><span class="cheat-papel">${esc(papel)}</span></button></li>`).join("");
$("#lista-cheats").addEventListener("click", (e) => {
  const b = e.target.closest(".cheat");
  if (b) editor.inserir(CHEATS.at(Number(b.dataset.i)).at(4));
});

$("#executar").addEventListener("click", () => (execucao?.rodando ? interromper("parado") : enviar(true)));
$("#baixar").addEventListener("click", baixar);
$("#som").addEventListener("click", () => {
  somLigado = !somLigado;
  try { localStorage.setItem(PREF_SOM, somLigado ? "ligado" : "desligado"); } catch (_) { /* sem armazenamento */ }
  if (!somLigado) for (const a of Object.values(sons)) a?.pause();
  desenharSom();
});
$("#compartilhar").addEventListener("click", compartilhar);
$("#abrir").addEventListener("click", () => $("#arquivo").click());
$("#arquivo").addEventListener("change", async (e) => {
  const arq = e.target.files[0];
  if (!arq) return;
  abrirTexto(await arq.text(), arq.name);
  e.target.value = "";
  enviar(true);
});
$("#exemplo").addEventListener("change", async (e) => {
  const n = e.target.value;
  if (!n) return;
  e.target.value = "";
  try {
    abrirTexto(await exemplo(n), `${n}.cj`);
  } catch (erro) {
    return avisar(`Não deu para abrir examples/${n}.cj: ${erro.message}`);
  }
  clearTimeout(espera);
  enviar(true);
});

document.addEventListener("keydown", (e) => {
  if (!(e.ctrlKey || e.metaKey)) return;
  if (e.key === "Enter") {
    e.preventDefault();
    if (!execucao?.rodando) enviar(true);
  } else if (e.key === "s") {
    e.preventDefault();
    baixar();
  }
});

$("#aba-console").addEventListener("click", (e) => {
  const b = e.target.closest(".diag");
  if (b?.dataset.linha) editor.irPara(Number(b.dataset.linha), Number(b.dataset.coluna));
});
$("#aba-python").addEventListener("click", (e) => {
  const b = e.target.closest("button[data-alvo]");
  if (!b) return;
  alvoPython = b.dataset.alvo;
  mostrar();
});

// ---- início: código do link, ou o último deste navegador, ou o fatorial ----
desenharEstrelas(0);
desenharSom();
desenharConsole();
(async () => {
  const doLink = codigoDoLink(), salvo = guardado();
  if (doLink !== null) {
    abrirTexto(doLink, "main.cj");
    history.replaceState(null, "", location.href.split("#")[0]);  // usado uma vez: recarregar mantém as edições
    avisar("Código carregado do link.");
  } else if (salvo?.fonte) {
    abrirTexto(salvo.fonte, salvo.nome || "main.cj");
  } else {
    try { abrirTexto(await exemplo("fatorial"), "main.cj"); } catch (_) { abrirTexto("", "main.cj"); }
  }
  iniciarWorker();
})();
