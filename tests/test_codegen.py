import io
import shutil
import subprocess
import sys
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from grove.codegen_py import emit_python

from tests.test_ir import TRECHOS, compilar, programas, saida_interpretador, saida_tac
from tests.test_lexer import FATORIAL
from tests.test_semantic import cli

RAIZ = Path(__file__).resolve().parent.parent


def python_de(src):
    return emit_python(*compilar(src))


def saida_python(codigo, globais=None):
    out = io.StringIO()
    with redirect_stdout(out):
        exec(compile(codigo, "<grove>", "exec"), globais if globais is not None else {"__name__": "__grove__"})
    return out.getvalue().splitlines()


class PlacaFalsa:
    """machine e time do MicroPython, só o que o --esp32 usa; registra o que acontece no LED."""

    def __init__(self):
        self.pinos, self.periodos, self.esperas = [], [], []
        placa = self

        class Pin:
            OUT = 1

            def __init__(self, n, modo):
                placa.pinos.append(n)
                self.v = 0

            def value(self, v=None):
                if v is None:
                    return self.v
                self.v = int(bool(v))

        class Timer:
            PERIODIC = 1

            def __init__(self, n):
                self.callback = None

            def init(self, period, mode, callback):
                placa.periodos.append(period)
                self.callback = callback

            def deinit(self):
                self.callback = None

        self.machine = types.SimpleNamespace(Pin=Pin, Timer=Timer)
        self.time = types.SimpleNamespace(sleep_ms=self.esperas.append)

    def rodar(self, codigo):
        globais = {"__name__": "__grove__"}
        with mock.patch.dict(sys.modules, {"machine": self.machine, "time": self.time}):
            return saida_python(codigo, globais), globais


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

    @unittest.skipUnless(shutil.which("micropython"), "MicroPython (porta unix) não instalado")
    def test_python_gerado_roda_igual_no_micropython(self):
        for nome, src in programas():
            with self.subTest(nome):
                prog, analise = compilar(src)
                rodou = subprocess.run(["micropython", "-c", emit_python(prog, analise)],
                                       capture_output=True, text=True, check=True)
                self.assertEqual(rodou.stdout.splitlines(), saida_interpretador(prog))

    def test_cli_python_roda_no_python(self):
        codigo, out, _ = cli(str(RAIZ / "examples" / "fatorial.cj"), "--python")
        self.assertEqual(codigo, 0)
        rodou = subprocess.run([sys.executable, "-"], input=out, capture_output=True, text=True, check=True)
        self.assertEqual(rodou.stdout, "120\n")


class Esp32Test(unittest.TestCase):
    PROCURADO = (RAIZ / "examples" / "procurado.cj").read_text()

    def test_estrelas_comandam_o_led(self):
        prog, analise = compilar(self.PROCURADO)
        placa = PlacaFalsa()
        saida, globais = placa.rodar(emit_python(prog, analise, esp32=True, pino=4))
        self.assertEqual(saida, saida_interpretador(prog))     # HELLOLADIES sai na serial igual
        self.assertEqual(placa.pinos, [4])
        self.assertEqual(placa.periodos, [600, 300, 200, 150, 120, 100])  # 0 estrelas: apagado, sem timer
        self.assertEqual(placa.esperas, [1500] * 7)             # uma pausa por valor novo, incluindo o 0
        timer, led = globais["_timer"], globais["_led"]
        timer.callback(timer)
        self.assertEqual(led.value(), 1)                        # o tique do timer acende o LED

    def test_sem_estrelas_sai_igual_ao_python(self):
        prog, analise = compilar(FATORIAL)
        self.assertEqual(emit_python(prog, analise, esp32=True), emit_python(prog, analise))

    def test_estrelas_que_nao_e_inteiro_nao_mexe_no_led(self):
        prog, analise = compilar('HESOYAM estrelas = "seis"; HELLOLADIES estrelas;')
        self.assertNotIn("_procurado", emit_python(prog, analise, esp32=True))

    def test_nomes_do_preludio_ficam_reservados(self):
        src = "HESOYAM estrelas = 1; HESOYAM time = 2; HESOYAM _led = 3; HESOYAM max = 4; HELLOLADIES time + _led + max;"
        codigo = emit_python(*compilar(src), esp32=True)
        self.assertIn("time_ = 2", codigo)
        self.assertIn("_led_ = 3", codigo)
        self.assertIn("max_ = 4", codigo)  # o prelúdio chama max()
        self.assertEqual(PlacaFalsa().rodar(codigo)[0], ["9"])

    def test_cli(self):
        codigo, out, err = cli(str(RAIZ / "examples" / "procurado.cj"), "--esp32", "--pino", "5")
        self.assertEqual(codigo, 0)
        self.assertIn("_led = Pin(5, Pin.OUT)", out)
        self.assertEqual(err, "")
        _, _, err = cli(str(RAIZ / "examples" / "fatorial.cj"), "--esp32")
        self.assertIn("aviso: nenhuma variável inteira 'estrelas'", err)


if __name__ == "__main__":
    unittest.main()
