import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from grove.codegen_ino import (GIROFLEX_A_PARTIR_DE, MOSTRA_MS, PINO_AZUL, PINO_PLACA, PINO_VERMELHO, PINOS_ESTRELAS,
                               emit_ino)
from grove.codegen_py import emit_python

from tests.test_ir import TRECHOS, compilar, linhas, programas, saida_interpretador, saida_tac
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


GPP = shutil.which("g++")
ARDUINO_FALSO = RAIZ / "tests" / "arduino_falso.h"


class PlacaFalsa:
    """Compila o sketch com o Arduino de mentira e roda no PC, guardando o que cada pino fez.

    tests/arduino_falso.h tem relógio virtual: o delay do prelúdio é que faz o
    tempo andar, então a simulação é determinística e instantânea.
    """

    def __init__(self, codigo, entrada=()):
        self.saida, self.eventos, self.fim = [], [], 0  # eventos: (ms, pino, valor)
        with tempfile.TemporaryDirectory() as tmp:
            sketch, exe = Path(tmp) / "sketch.ino", Path(tmp) / "sketch"
            sketch.write_text(codigo, encoding="utf-8")
            subprocess.run([GPP, "-x", "c++", "-std=c++17", "-Werror", "-Wall", "-include", str(ARDUINO_FALSO),
                            str(sketch), "-o", str(exe)], check=True, capture_output=True, text=True)
            texto = "".join(f"{linha}\n" for linha in entrada)
            self.rodou = subprocess.run([str(exe)], input=texto, capture_output=True, text=True)
        for linha in self.rodou.stdout.splitlines():
            marca, resto = linha.split(" ", 1)
            if marca == "F":
                self.fim = int(resto)
            elif marca == "O":
                ms, texto = resto.split(" ", 1)
                self.saida.append(texto)
            else:
                ms, pino, valor = map(int, resto.split())
                self.eventos.append((ms, pino, valor))

    def nivel(self, n):
        """Os eventos do n-ésimo _procurado: cada um fica MOSTRA_MS parado."""
        return [e for e in self.eventos if n * MOSTRA_MS <= e[0] < (n + 1) * MOSTRA_MS]

    def pinos_no_nivel(self, n, pinos):
        """Valor de cada pino no começo do nível n (as estrelas não mudam durante ele)."""
        estado = {p: 0 for p in pinos}
        for ms, pino, valor in self.eventos:
            if ms > n * MOSTRA_MS:
                break
            if pino in estado:
                estado[pino] = valor
        return [estado[p] for p in pinos]

    def estrelas_por_chamada(self):
        """Quantas estrelas ficaram acesas em cada passada do _procurado.

        Cada chamada escreve as seis de uma vez, então basta contar de seis em seis;
        não depende do relógio, que com entrada deixa de marcar os níveis.
        """
        estado, vistos, saida = {}, 0, []
        for _, pino, valor in self.eventos:
            if pino not in PINOS_ESTRELAS:
                continue
            estado[pino], vistos = valor, vistos + 1
            if vistos % len(PINOS_ESTRELAS) == 0:
                saida.append(sum(estado.values()))
        return saida

    def periodo(self, n, pino):
        """Intervalo entre as piscadas do pino no nível n; 0 se ele não piscou.

        A primeira escrita do nível é o reset do _procurado, fora do ritmo: conta a partir da segunda.
        """
        quando = [ms for ms, p, _ in self.nivel(n) if p == pino]
        return quando[2] - quando[1] if len(quando) > 2 else 0


def globais_com(entrada):
    """Globais para o exec() do Python gerado, com o input() trocado pela lista."""
    return {"__name__": "__grove__", "input": linhas(entrada)}


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


@unittest.skipUnless(GPP, "g++ não instalado")
class MegaTest(unittest.TestCase):
    """O sketch gerado é compilado de verdade e rodado contra o Arduino de mentira."""

    PROCURADO = (RAIZ / "examples" / "procurado.cj").read_text()
    PERIODOS_LED = [600, 300, 200, 150, 120, 100]  # 600 // n, nos níveis 1 a 6

    def ino(self, src, **kw):
        prog, analise = compilar(src)
        return prog, emit_ino(prog, analise, **kw)

    def test_estrelas_piscam_o_led_da_placa(self):
        prog, codigo = self.ino(self.PROCURADO, pino=4)
        placa = PlacaFalsa(codigo)
        self.assertEqual(placa.saida, saida_interpretador(prog))  # HELLOLADIES sai na serial igual
        self.assertEqual({p for _, p, _ in placa.eventos}, {4})
        self.assertEqual(placa.periodo(0, 4), 0)                   # 0 estrelas: apagado, sem piscar
        self.assertEqual([placa.periodo(n, 4) for n in range(1, 7)], self.PERIODOS_LED)

    def test_hud_acende_uma_luz_por_estrela_e_o_giroflex(self):
        prog, codigo = self.ino(self.PROCURADO, hud=True)
        placa = PlacaFalsa(codigo)
        self.assertEqual(placa.saida, saida_interpretador(prog))
        for n in range(7):  # as primeiras n acesas, na ordem
            self.assertEqual(placa.pinos_no_nivel(n, PINOS_ESTRELAS), [1] * n + [0] * (6 - n))
        self.assertEqual([placa.periodo(n, PINO_PLACA) for n in range(1, 7)], self.PERIODOS_LED)
        giroflex = [placa.periodo(n, PINO_VERMELHO) for n in range(7)]
        self.assertEqual(giroflex, [0] * GIROFLEX_A_PARTIR_DE + [300, 250, 200])  # mais rápido a cada estrela
        for n in range(GIROFLEX_A_PARTIR_DE, 7):
            vermelho = [v for _, p, v in placa.nivel(n) if p == PINO_VERMELHO]
            azul = [v for _, p, v in placa.nivel(n) if p == PINO_AZUL]
            self.assertEqual(azul, [1 - v for v in vermelho])                        # sempre opostos
            self.assertTrue(all(a != b for a, b in zip(vermelho, vermelho[1:])))      # e alternando

    def test_hud_apaga_o_giroflex_quando_as_estrelas_baixam(self):
        _, codigo = self.ino("HESOYAM estrelas = 5; estrelas = 2; estrelas = 9; estrelas = -1;", hud=True)
        placa = PlacaFalsa(codigo)
        acesas = [sum(placa.pinos_no_nivel(n, PINOS_ESTRELAS)) for n in range(4)]
        self.assertEqual(acesas, [5, 2, 6, 0])                      # 9 estrelas acendem as 6; -1 apaga tudo
        ligado = [placa.periodo(n, PINO_VERMELHO) > 0 for n in range(4)]
        self.assertEqual(ligado, [True, False, True, False])
        self.assertEqual(placa.pinos_no_nivel(4, (PINO_VERMELHO, PINO_AZUL)), [0, 0])  # no fim, apagado

    def test_sem_estrelas_nao_tem_preludio(self):
        _, codigo = self.ino(FATORIAL)
        self.assertNotIn("_procurado", codigo)
        self.assertEqual(PlacaFalsa(codigo).saida, ["120"])

    def test_estrelas_que_nao_e_inteiro_nao_mexe_no_led(self):
        _, codigo = self.ino('HESOYAM estrelas = "seis"; HELLOLADIES estrelas;')
        self.assertNotIn("_procurado", codigo)
        self.assertEqual(PlacaFalsa(codigo).saida, ["seis"])

    def test_nomes_do_preludio_e_do_c_ficam_reservados(self):
        src = ("HESOYAM estrelas = 1; HESOYAM _LED = 2; HESOYAM _div = 3; HESOYAM loop = 4; HESOYAM delay = 5;"
               " HESOYAM _ESTRELAS = 6; HELLOLADIES _LED + _div + loop + delay + _ESTRELAS;")
        for hud in (False, True):
            with self.subTest(hud=hud):
                _, codigo = self.ino(src, hud=hud)
                for nome in ("_LED_", "_div_", "loop_", "delay_", "_ESTRELAS_"):
                    self.assertIn(f"{nome} = ", codigo)
                self.assertEqual(PlacaFalsa(codigo).saida, ["20"])

    def test_divisao_e_resto_arredondam_como_o_interpretador(self):
        src = ("HELLOLADIES -7 / 2; HELLOLADIES 7 / -2; HELLOLADIES -7 % 2; HELLOLADIES 7 % -2;"
               " HESOYAM a = -7; HESOYAM b = 2; HELLOLADIES a / b; HELLOLADIES a % b;")  # e com variáveis
        prog, codigo = self.ino(src)
        self.assertEqual(PlacaFalsa(codigo).saida, saida_interpretador(prog))

    def test_divisao_por_zero_para_o_programa(self):
        _, codigo = self.ino("HESOYAM z = 0; HELLOLADIES 1 / z; HELLOLADIES 2;")
        placa = PlacaFalsa(codigo)
        self.assertEqual(placa.rodou.returncode, 1)
        self.assertEqual(placa.saida, ["erro: divisão por zero"])

    def test_strings_somam_e_comparam(self):
        src = 'HELLOLADIES "a" + "b"; HESOYAM s = "x"; HELLOLADIES s + "y"; HELLOLADIES "x" == s;'
        prog, codigo = self.ino(src)
        self.assertEqual(PlacaFalsa(codigo).saida, saida_interpretador(prog))

    def test_parenteses_so_onde_precisa(self):
        casos = {
            "2 + 3 * 4": "2L + 3L * 4L",
            "(2 + 3) * 4": "(2L + 3L) * 4L",
            "10 - 4 - 3": "10L - 4L - 3L",
            "10 - (4 - 3)": "10L - (4L - 3L)",
            "-(2 + 3)": "-(2L + 3L)",
            "!a == b": "!a == b",              # no C o ! é mais forte que o ==
            "!(a == b)": "!(a == b)",
            "a == !b": "a == !b",
            "!(a && b) || a": "!(a && b) || a",
            "a || b && a": "a || b && a",
            "(a || b) && a": "(a || b) && a",
        }
        for grove, c in casos.items():
            with self.subTest(grove):
                _, codigo = self.ino(f"HESOYAM a = FULLCLIP; HESOYAM b = GHOSTTOWN; HELLOLADIES {grove};")
                linha = [l.strip() for l in codigo.splitlines() if "Serial.println" in l][-1]
                self.assertIn(linha, (f"Serial.println({c});", f'Serial.println({c} ? "FULLCLIP" : "GHOSTTOWN");'))

    def test_ino_faz_o_mesmo_que_o_interpretador(self):
        for nome, src in programas():
            with self.subTest(nome):
                prog, codigo = self.ino(src)
                self.assertEqual(PlacaFalsa(codigo).saida, saida_interpretador(prog))

    def test_entrada_chega_na_placa(self):
        """O mesmo .cj, a mesma entrada: interpretador, TAC, Python e Arduino dão a mesma saída."""
        src = ("HESOYAM estrelas = 0; HESOYAM i = 0;\n"
               "KANGAROO (i < 3) { estrelas = CJPHONEHOME; HELLOLADIES estrelas * 2; i = i + 1; }")
        entrada = ["3", "6", "0"]
        prog, analise = compilar(src)
        esperado = ["6", "12", "0"]
        self.assertEqual(saida_interpretador(prog, entrada), esperado)
        self.assertEqual(saida_tac(prog, analise, entrada), esperado)
        self.assertEqual(saida_python(emit_python(prog, analise), globais_com(entrada)), esperado)
        self.assertEqual(PlacaFalsa(emit_ino(prog, analise, hud=True), entrada).saida, esperado)

    def test_entrada_acende_as_estrelas_sem_pausa(self):
        src = "HESOYAM estrelas = 0; KANGAROO (FULLCLIP) { estrelas = CJPHONEHOME; }"
        _, codigo = self.ino(src, hud=True)
        self.assertNotIn("para dar para ver", codigo)  # quem dá o ritmo agora é a entrada
        placa = PlacaFalsa(codigo, ["4", "1"])
        self.assertEqual(placa.estrelas_por_chamada(), [0, 4, 1])  # o 0 é a declaração

    def test_cli(self):
        codigo, out, err = cli(str(RAIZ / "examples" / "procurado.cj"), "--mega", "--pino", "5")
        self.assertEqual(codigo, 0)
        self.assertIn("const int _LED = 5;", out)
        self.assertEqual(err, "")
        codigo, out, _ = cli(str(RAIZ / "examples" / "procurado.cj"), "--mega", "--hud")
        self.assertEqual(codigo, 0)
        self.assertIn("_GIROFLEX", out)
        _, _, err = cli(str(RAIZ / "examples" / "fatorial.cj"), "--mega")
        self.assertIn("aviso: nenhuma variável inteira 'estrelas'", err)


if __name__ == "__main__":
    unittest.main()
