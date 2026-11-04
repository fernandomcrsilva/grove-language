// Roda a Grove em Python (Pyodide) fora da página: um laço infinito não trava a aba,
// e a página pode encerrar este worker se o programa passar do tempo.
const CDN = "https://cdn.jsdelivr.net/npm/pyodide@314.0.7/";
// ?pyodide=caminho/ usa uma cópia local do Pyodide (apresentar sem internet); só da mesma origem
const local = new URLSearchParams(self.location.search).get("pyodide");
const alvo = local && new URL(local.endsWith("/") ? local : local + "/", self.location.href);
const PYODIDE = alvo && alvo.origin === self.location.origin ? alvo.href : CDN;
const MODULOS = ["__init__", "ast", "tokens", "lexer", "parser", "semantic", "interpreter", "ir", "codegen_py"];

const GLUE = `
import json
import re

from grove import (LexError, ParseError, RuntimeError_, SemanticError, check, dump, emit_ir, emit_python,
                   format_ir, format_symbols, parse, run, tokenize)

LIMITE = 5000  # linhas de saída
_programa = None


def _diagnostico(texto, tipo):
    m = re.match(r"linha (\\d+), coluna (\\d+): (.*)", texto)
    if m:
        return {"linha": int(m[1]), "coluna": int(m[2]), "mensagem": m[3], "tipo": tipo}
    return {"linha": None, "coluna": None, "mensagem": texto, "tipo": tipo}


def compilar(src):
    """Roda léxico, sintático e semântico e devolve o que cada etapa produziu."""
    global _programa
    _programa = None
    r = {"etapas": {}, "erros": [], "avisos": []}
    try:
        r["etapas"]["lexico"] = "erro"
        tokens = tokenize(src)
        r["tokens"] = "LINHA:COL\\tTIPO\\tLEXEMA\\n" + "\\n".join(map(str, tokens))
        r["etapas"]["lexico"] = "ok"

        r["etapas"]["sintatico"] = "erro"
        programa = parse(tokens)
        r["ast"] = dump(programa)
        r["etapas"]["sintatico"] = "ok"

        r["etapas"]["semantico"] = "erro"
        analise = check(programa)
        r["avisos"] = [_diagnostico(str(a), "aviso") for a in analise.avisos]
        r["simbolos"] = format_symbols(analise)
        r["ir"] = format_ir(emit_ir(programa, analise))
        r["python"] = emit_python(programa, analise)
        r["esp32"] = emit_python(programa, analise, esp32=True)
        r["etapas"]["semantico"] = "ok"
        _programa = programa
    except LexError as e:
        r["erros"] = [_diagnostico(str(e), "léxico")]
    except ParseError as e:
        r["erros"] = [_diagnostico(str(e), "sintático")]
    except SemanticError as e:
        r["erros"] = [_diagnostico(str(d), "semântico") for d in e.erros]
    return json.dumps(r)


class _SaidaDemais(Exception):
    pass


def executar():
    saida = []

    def out(linha):
        if len(saida) >= LIMITE:
            raise _SaidaDemais()
        saida.append(linha)

    erro = None
    try:
        run(_programa, out=out)
    except RuntimeError_ as e:
        erro = str(e)
    except _SaidaDemais:
        erro = f"saída cortada em {LIMITE} linhas"
    return json.dumps({"saida": saida, "erro": erro})
`;

let pyodide = null;

const progresso = (pct, texto) => postMessage({ tipo: "progresso", pct, texto });

async function carregar() {
  progresso(5, "baixando o Python (Pyodide)");
  const { loadPyodide } = await import(PYODIDE + "pyodide.mjs");  // o Pyodide 314 só roda em module worker
  progresso(20, "iniciando o Python");
  pyodide = await loadPyodide({ indexURL: PYODIDE });
  progresso(75, "carregando o compilador da Grove");
  pyodide.FS.mkdirTree("/home/pyodide/grove");
  await Promise.all(MODULOS.map(async (m) => {
    const resp = await fetch(`../grove/${m}.py`);
    if (!resp.ok) throw new Error(`grove/${m}.py: HTTP ${resp.status}`);
    pyodide.FS.writeFile(`/home/pyodide/grove/${m}.py`, await resp.text());
  }));
  progresso(95, "quase lá");
  pyodide.runPython(GLUE);
  return pyodide.runPython("import sys; sys.version.split()[0]");
}

const pronto = carregar().then(
  (versao) => postMessage({ tipo: "pronto", versao }),
  (erro) => postMessage({ tipo: "falhou", mensagem: String(erro) }),
);

onmessage = async ({ data }) => {
  await pronto;
  const compilado = JSON.parse(pyodide.globals.get("compilar")(data.src));
  postMessage({ tipo: "compilado", id: data.id, ...compilado });
  if (data.executar && compilado.erros.length === 0) {
    postMessage({ tipo: "executado", id: data.id, ...JSON.parse(pyodide.globals.get("executar")()) });
  }
};
