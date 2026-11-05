"""Uso: python -m grove arquivo.cj [--tokens] [--ast] [--simbolos] [--ir] [--otimizar] [--python] [--esp32 [--hud] [--pino N]]

Sem flags confere e executa o programa. Com flags só mostra essas etapas.
Sai com código 1 em erro léxico, sintático, semântico ou de execução.
"""
import argparse
import sys

from . import (LexError, ParseError, RuntimeError_, SemanticError, check, dump, emit_ir, emit_python, format_ir,
               format_symbols, otimizar, parse, resumo, run, tokenize)
from .codegen_py import ESTRELAS, tem_estrelas
from .sounds import play

ETAPAS = {"tokens": 0, "ast": 1, "simbolos": 2, "ir": 2, "otimizar": 2, "python": 2, "esp32": 2}  # flag → etapa que ela precisa
SONS = {LexError: "lex_error", ParseError: "parse_error", SemanticError: "semantic_error"}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="grove", description=__doc__.splitlines()[0])
    ap.add_argument("arquivo")
    ap.add_argument("--tokens", action="store_true", help="imprime a tabela de tokens em vez de executar")
    ap.add_argument("--ast", action="store_true", help="imprime a AST em vez de executar")
    ap.add_argument("--simbolos", action="store_true", help="imprime a tabela de símbolos em vez de executar")
    ap.add_argument("--ir", action="store_true", help="imprime o código de três endereços em vez de executar")
    ap.add_argument("--otimizar", action="store_true", help="imprime o código de três endereços otimizado e o que mudou")
    ap.add_argument("--python", action="store_true", help="imprime o programa traduzido para Python em vez de executar")
    ap.add_argument("--esp32", action="store_true",
                    help=f"imprime MicroPython para o ESP32: a variável '{ESTRELAS}' pisca o LED")
    ap.add_argument("--hud", action="store_true",
                    help="com --esp32: uma luz por estrela e o giroflex da polícia (ver docs/esp32.md)")
    ap.add_argument("--pino", type=int, default=2, metavar="N", help="GPIO do LED no --esp32 (padrão: 2)")
    args = ap.parse_args(argv)

    with open(args.arquivo, encoding="utf-8") as f:
        src = f.read()

    pedidas = [e for e in ETAPAS if getattr(args, e)]
    executar = not pedidas
    ate = max(ETAPAS.values()) if executar else max(ETAPAS[e] for e in pedidas)
    secoes = []

    def mostrar(texto):
        if secoes:
            print()
        print(texto)
        secoes.append(texto)

    try:
        tokens = tokenize(src)
        if args.tokens:
            mostrar("LINHA:COL\tTIPO\tLEXEMA\n" + "\n".join(map(str, tokens)))
        if ate >= ETAPAS["ast"]:
            program = parse(tokens)
            if args.ast:
                mostrar(dump(program))
        if ate >= ETAPAS["simbolos"]:
            analise = check(program)
            for aviso in analise.avisos:
                print(f"aviso: {aviso}", file=sys.stderr)
            if args.simbolos:
                mostrar(format_symbols(analise))
            if args.ir:
                mostrar(format_ir(emit_ir(program, analise)))
            if args.otimizar:
                code = emit_ir(program, analise)
                otimizado, conta = otimizar(code, analise)
                mostrar(format_ir(otimizado) + f"\n# {resumo(code, otimizado, conta)}")
            if args.python:
                mostrar(emit_python(program, analise, origem=args.arquivo))
            if args.esp32:
                if not tem_estrelas(analise):
                    print(f"aviso: nenhuma variável inteira '{ESTRELAS}': o programa não mexe no LED", file=sys.stderr)
                mostrar(emit_python(program, analise, origem=args.arquivo, esp32=True, pino=args.pino, hud=args.hud))
        if executar:
            run(program)
    except (LexError, ParseError, SemanticError, RuntimeError_) as e:
        erros = getattr(e, "erros", [e])
        for erro in erros:
            print(f"erro: {erro}", file=sys.stderr)
        if len(erros) > 1:
            print(f"{len(erros)} erros {'sintáticos' if isinstance(e, ParseError) else 'semânticos'}", file=sys.stderr)
        play(SONS.get(type(e), "runtime_error"))
        return 1
    play("passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
