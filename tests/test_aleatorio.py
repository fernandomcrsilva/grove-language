"""Teste diferencial com programas aleatórios: interpretador, TAC e Python têm que dar a mesma saída.

Gera expressões bem tipadas (inteiros, booleanos, todos os operadores, divisão por
zero incluída) e confere os três executores. Roda 300 programas por padrão;
GROVE_ALEATORIOS=3000 roda mais, GROVE_SEMENTE escolhe a semente.
"""
import io
import os
import random
import unittest
from contextlib import redirect_stdout

from grove.codegen_py import emit_python
from grove.interpreter import RuntimeError_, run
from grove.ir import emit_ir, execute

from tests.test_ir import compilar

QUANTOS = int(os.environ.get("GROVE_ALEATORIOS", "300"))
SEMENTE = int(os.environ.get("GROVE_SEMENTE", "1"))
DIVISAO = "<divisão por zero>"


class Gerador:
    def __init__(self, semente):
        self.r = random.Random(semente)

    def atomo(self, texto):
        return texto if texto.lstrip("-").isalnum() else f"({texto})"

    def inteiro(self, d):
        r = self.r
        if d == 0 or r.random() < 0.2:
            return r.choice(["a", "b", str(r.randint(0, 9)), f"-{r.randint(1, 5)}"])
        k = r.random()
        if k < 0.15:
            return f"-{self.atomo(self.inteiro(d - 1))}"
        if k < 0.3:
            return f"({self.inteiro(d - 1)})"
        return f"{self.inteiro(d - 1)} {r.choice('+-*/%')} {self.inteiro(d - 1)}"

    def booleano(self, d):
        r = self.r
        if d == 0 or r.random() < 0.15:
            return r.choice(["p", "q", "FULLCLIP", "GHOSTTOWN"])
        k = r.random()
        if k < 0.15:
            return f"!{self.atomo(self.booleano(d - 1))}"
        if k < 0.25:
            return f"({self.booleano(d - 1)})"
        if k < 0.55:
            return f"{self.inteiro(d - 1)} {r.choice(['<', '>', '<=', '>=', '==', '!='])} {self.inteiro(d - 1)}"
        if k < 0.7:  # o lado direito entre parênteses: p == a == b seria (p == a) == b, mal tipado
            return f"{self.booleano(d - 1)} {r.choice(['==', '!='])} {self.atomo(self.booleano(d - 1))}"
        return f"{self.booleano(d - 1)} {r.choice(['&&', '||'])} {self.booleano(d - 1)}"

    def programa(self):
        r = self.r
        expr = self.booleano(4) if r.random() < 0.5 else self.inteiro(4)
        return (f"HESOYAM a = {r.randint(-9, 9)}; HESOYAM b = {r.randint(1, 9)}; "
                f"HESOYAM p = FULLCLIP; HESOYAM q = GHOSTTOWN;\n"
                f"HELLOLADIES {expr};\nHELLOLADIES a + b; HELLOLADIES p || q;")


def rodar(executor):
    saida = []
    try:
        executor(saida.append)
    except (RuntimeError_, ZeroDivisionError):
        saida.append(DIVISAO)
    return saida


def rodar_python(codigo, out):
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(compile(codigo, "<grove>", "exec"), {"__name__": "__grove__"})
    finally:
        for linha in buf.getvalue().splitlines():
            out(linha)


class AleatorioTest(unittest.TestCase):
    def test_tres_executores_concordam(self):
        g = Gerador(SEMENTE)
        for i in range(QUANTOS):
            src = g.programa()
            prog, analise = compilar(src)
            interpretador = rodar(lambda out: run(prog, out=out))
            tac = rodar(lambda out: execute(emit_ir(prog, analise), out))
            python = rodar(lambda out: rodar_python(emit_python(prog, analise), out))
            with self.subTest(i=i, src=src):
                self.assertEqual(tac, interpretador)
                self.assertEqual(python, interpretador)


if __name__ == "__main__":
    unittest.main()
