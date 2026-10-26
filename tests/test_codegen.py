import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from grove.codegen_py import emit_python

from tests.test_ir import TRECHOS, compilar, programas, saida_interpretador, saida_tac
from tests.test_lexer import FATORIAL
from tests.test_semantic import cli

RAIZ = Path(__file__).resolve().parent.parent


def python_de(src):
    return emit_python(*compilar(src))


def saida_python(codigo):
    out = io.StringIO()
    with redirect_stdout(out):
        exec(compile(codigo, "<grove>", "exec"), {"__name__": "__grove__"})
    return out.getvalue().splitlines()


def corpo(src):
    """Python gerado sem a linha de comentário do topo."""
    return python_de(src).splitlines()[1:]


class CodegenPythonTest(unittest.TestCase):
    def test_fatorial(self):
        self.assertEqual(python_de(FATORIAL).splitlines(), [
            "# gerado pela Grove",
            "n = 5",
            "r = 1",
            "while n > 1:",
            "    r = r * n",
            "    n = n - 1",
            "print(r)",
        ])

    def test_if_else_if_else(self):
        src = "HESOYAM n = 1; TURNUPTHEHEAT (n < 0) { } BRINGITON (n == 0) { HELLOLADIES 0; } TURNDOWNTHEHEAT { }"
        self.assertEqual(corpo(src), ["n = 1", "if n < 0:", "    pass", "elif n == 0:", "    print(0)", "else:", "    pass"])

    def test_literais_e_operadores(self):
        self.assertEqual(corpo('HELLOLADIES "a\\b" + "c"; HELLOLADIES 7 / 2; HELLOLADIES FULLCLIP && !GHOSTTOWN;'), [
            'print("a\\\\b" + "c")',
            "print(7 // 2)",
            'print("FULLCLIP" if True and not False else "GHOSTTOWN")',
        ])

    def test_parenteses_so_onde_precisa(self):
        casos = {
            "2 + 3 * 4": "2 + 3 * 4",
            "(2 + 3) * 4": "(2 + 3) * 4",
            "10 - 4 - 3": "10 - 4 - 3",
            "10 - (4 - 3)": "10 - (4 - 3)",
            "-(2 + 3)": "-(2 + 3)",
            "!a == b": "(not a) == b",         # not é mais fraco que == em Python
            "!(a == b)": "not a == b",
            "a == !b": "a == (not b)",          # a == not b é erro de sintaxe em Python
            "1 == 2 == b": "(1 == 2) == b",     # sem encadear comparação
            "b == (1 == 2)": "b == (1 == 2)",
            "!(a && b) || a": "not (a and b) or a",
            "a || b && a": "a or b and a",
        }
        for grove, py in casos.items():
            with self.subTest(grove):
                linha = corpo(f"HESOYAM a = FULLCLIP; HESOYAM b = GHOSTTOWN; HELLOLADIES {grove};")[-1]
                self.assertIn(linha, (f"print({py})", f'print("FULLCLIP" if {py} else "GHOSTTOWN")'))

    def test_nomes_unicos_e_reservados_do_python(self):
        self.assertEqual(corpo(TRECHOS["sombra"]), ["x = 1", "x_1 = x + 1", "print(x_1)", "print(x)"])
        self.assertEqual(corpo("HESOYAM print = 1; HESOYAM print_ = 2; HELLOLADIES print + print_;"),
                         ["print__ = 1", "print_ = 2", "print(print__ + print_)"])

    def test_python_faz_o_mesmo_que_interpretador_e_tac(self):
        for nome, src in programas():
            with self.subTest(nome):
                prog, analise = compilar(src)
                esperado = saida_interpretador(prog)
                self.assertEqual(saida_tac(prog, analise), esperado)
                self.assertEqual(saida_python(emit_python(prog, analise)), esperado)

    def test_divisao_por_zero_vira_zerodivisionerror(self):
        with self.assertRaises(ZeroDivisionError):
            saida_python(python_de("HESOYAM z = 0; HELLOLADIES 1 / z;"))

    def test_cli_python_roda_no_python(self):
        codigo, out, _ = cli(str(RAIZ / "examples" / "fatorial.cj"), "--python")
        self.assertEqual(codigo, 0)
        rodou = subprocess.run([sys.executable, "-"], input=out, capture_output=True, text=True, check=True)
        self.assertEqual(rodou.stdout, "120\n")


if __name__ == "__main__":
    unittest.main()
