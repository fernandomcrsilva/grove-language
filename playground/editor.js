// Editor de código com realce de sintaxe, sem biblioteca: um <textarea> de texto
// transparente por cima de um <pre> colorido, os dois com a mesma fonte, o mesmo
// espaçamento e a mesma rolagem. O usuário digita no textarea; o pre só desenha.

const CHEATS = {
  HESOYAM: "decl", HELLOLADIES: "decl",
  TURNUPTHEHEAT: "ctrl", BRINGITON: "ctrl", TURNDOWNTHEHEAT: "ctrl", KANGAROO: "ctrl", GOODBYECRUELWORLD: "ctrl",
  FULLCLIP: "lit", GHOSTTOWN: "lit",
};
// mesmas classes do léxico (grove/lexer.py): comentário, string, número, palavra, operador
const TOKEN = /(#[^\n]*)|("[^"\n]*"?)|(\d+)|([A-Za-z_][A-Za-z0-9_]*)|(==|!=|<=|>=|&&|\|\||[=<>!+\-*/%{}();])/g;
const RECUO = "    ";

const esc = (s) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);

export function realcar(linha) {
  let html = "", fim = 0;
  for (const m of linha.matchAll(TOKEN)) {
    html += esc(linha.slice(fim, m.index));
    const [texto, comentario, string, numero, palavra] = m;
    const classe = comentario ? "c-coment" : string ? "c-string" : numero ? "c-num"
      : palavra ? (CHEATS[palavra] ? `c-${CHEATS[palavra]}` : "c-ident") : "c-op";
    html += `<span class="${classe}">${esc(texto)}</span>`;
    fim = m.index + texto.length;
  }
  return html + esc(linha.slice(fim));
}

export function criarEditor({ area, realce, numeros, aoMudar, aoMoverCursor }) {
  let erros = new Set(), avisos = new Set();
  let sairComTab = false;  // depois de Esc, Tab sai do editor (quem navega pelo teclado não fica preso)

  function desenhar() {
    const linhas = area.value.split("\n");
    const classe = (i) => (erros.has(i + 1) ? " erro" : avisos.has(i + 1) ? " aviso" : "");
    realce.innerHTML = linhas.map((l, i) => `<span class="linha${classe(i)}">${realcar(l) || " "}</span>`).join("");
    numeros.innerHTML = linhas.map((_, i) => `<span class="${classe(i).trim()}">${i + 1}</span>`).join("");
    rolar();
  }

  function rolar() {
    realce.scrollTop = numeros.scrollTop = area.scrollTop;
    realce.scrollLeft = area.scrollLeft;
  }

  function cursor() {
    const antes = area.value.slice(0, area.selectionStart).split("\n");
    aoMoverCursor?.(antes.length, antes.at(-1).length + 1);
  }

  // insertText mantém o Ctrl+Z funcionando; setRangeText é o plano B
  function digitar(texto) {
    if (!document.execCommand("insertText", false, texto)) {
      area.setRangeText(texto, area.selectionStart, area.selectionEnd, "end");
      area.dispatchEvent(new Event("input"));
    }
  }

  function inicioDaLinha(pos = area.selectionStart) {
    return area.value.lastIndexOf("\n", pos - 1) + 1;
  }

  function recuoDaLinha(pos = area.selectionStart) {
    return area.value.slice(inicioDaLinha(pos)).match(/^ */)[0];
  }

  area.addEventListener("input", () => { desenhar(); cursor(); aoMudar?.(area.value); });
  area.addEventListener("scroll", rolar);
  for (const ev of ["click", "keyup", "select"]) area.addEventListener(ev, cursor);

  area.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const pos = area.selectionStart, linha = area.value.slice(inicioDaLinha(), pos);
    if (e.key === "Escape") {
      sairComTab = true;
      return;
    }
    if (e.key === "Tab") {
      if (sairComTab) return;  // deixa o navegador mover o foco
      e.preventDefault();
      if (e.shiftKey) {
        const ini = inicioDaLinha(), tira = recuoDaLinha().length % 4 || Math.min(4, recuoDaLinha().length);
        if (tira) {
          area.setSelectionRange(ini, ini + tira);
          if (!document.execCommand("delete")) {
            area.setRangeText("", ini, ini + tira, "end");
            area.dispatchEvent(new Event("input"));
          }
        }
      } else {
        digitar(RECUO);
      }
      return;
    }
    sairComTab = false;
    if (e.key === "Enter") {  // mantém o recuo; depois de { recua mais um nível
      e.preventDefault();
      digitar("\n" + recuoDaLinha() + (linha.trimEnd().endsWith("{") ? RECUO : ""));
    } else if (e.key === "}" && /^ +$/.test(linha) && linha.length >= 4) {  // } numa linha só de espaços volta um nível
      e.preventDefault();
      area.setSelectionRange(pos - 4, pos);
      digitar("}");
    }
  });

  desenhar();

  return {
    valor: () => area.value,

    definir(texto) {
      area.value = texto;
      area.setSelectionRange(0, 0);
      area.scrollTop = area.scrollLeft = 0;
      desenhar();
      cursor();
    },

    // marca as linhas com erro e com aviso (números de linha começando em 1)
    marcar(linhasErro, linhasAviso) {
      erros = new Set(linhasErro);
      avisos = new Set(linhasAviso);
      desenhar();
    },

    // insere um modelo no cursor, no recuo da linha; o trecho entre ⟨ ⟩ fica selecionado para o usuário digitar por cima
    inserir(modelo) {
      area.focus();
      const texto = modelo.replaceAll("\n", "\n" + recuoDaLinha());
      const marca = texto.indexOf("⟨"), limpo = texto.replace(/[⟨⟩]/g, "");
      const inicio = area.selectionStart;
      digitar(limpo);
      if (marca >= 0) {
        const fim = texto.indexOf("⟩") - 1;
        area.setSelectionRange(inicio + marca, inicio + fim);
      }
      cursor();
    },

    // leva o cursor até linha:coluna e seleciona a palavra que começa ali
    irPara(linha, coluna) {
      const linhas = area.value.split("\n");
      let pos = 0;
      for (let i = 0; i < linha - 1 && i < linhas.length; i++) pos += linhas[i].length + 1;
      pos += Math.max(0, coluna - 1);
      const palavra = area.value.slice(pos).match(/^\w+/);
      area.focus();
      area.setSelectionRange(pos, pos + (palavra ? palavra[0].length : 1));
      cursor();
    },
  };
}
