import unittest
from pathlib import Path

from grove.interpreter import RuntimeError_, run
from grove.ir import emit_ir, execute, format_ir
from grove.otimizador import otimizar
from grove.lexer import tokenize
from grove.parser import parse
from grove.semantic import check

from tests.test_lexer import FATORIAL
from tests.test_semantic import cli

EXEMPLOS = Path(__file__).resolve().parent.parent / "examples"
VALIDOS = ("fatorial", "fizzbuzz", "procurado")

# trechos que exercitam os pontos delicados da tradução; usados também em test_codegen
TRECHOS = {
    "sombra": "HESOYAM x = 1; { HESOYAM x = x + 1; HELLOLADIES x; } HELLOLADIES x;",
    "blocos irmãos": "{ HESOYAM a = 1; HELLOLADIES a; } { HESOYAM a = 2; HELLOLADIES a; }",
    "curto-circuito pula a direita": "HESOYAM i = 0; HELLOLADIES GHOSTTOWN && 1 / i == 0; HELLOLADIES FULLCLIP || 1 / i == 0;",
    "curto-circuito lendo o destino": "HESOYAM x = GHOSTTOWN; HESOYAM y = FULLCLIP; x = y && x; HELLOLADIES x;",
    "! antes de ==": "HESOYAM a = GHOSTTOWN; HELLOLADIES !a == FULLCLIP; HELLOLADIES !(a == FULLCLIP);",
    "== encadeado": "HELLOLADIES 1 == 2 == GHOSTTOWN; HELLOLADIES FULLCLIP != (1 < 2);",
    "negativos em / e %": "HELLOLADIES -7 / 2; HELLOLADIES -7 % 2; HELLOLADIES 7 / -2; HELLOLADIES - -3;",
    "precedência": "HELLOLADIES 2 + 3 * 4; HELLOLADIES (2 + 3) * 4; HELLOLADIES 10 - 4 - 3; HELLOLADIES 10 - (4 - 3);",
    "strings": 'HESOYAM s = "Grove"; s = s + " Street"; HELLOLADIES s; HELLOLADIES s == "Grove Street";',
    "break aninhado": """
        HESOYAM i = 0;
        KANGAROO (i < 3) {
            HESOYAM j = 0;
            KANGAROO (FULLCLIP) { TURNUPTHEHEAT (j == 2) { GOODBYECRUELWORLD; } j = j + 1; }
            HELLOLADIES i * 10 + j;
            i = i + 1;
        }""",
    "else-if sem else": "HESOYAM n = 5; TURNUPTHEHEAT (n < 0) { HELLOLADIES 0; } BRINGITON (n < 10) { HELLOLADIES 1; }",
    "nomes de Python": "HESOYAM print = 1; HESOYAM if = 2; HESOYAM None = 3; HELLOLADIES print + if + None;",
    "temporário não colide": "HESOYAM t1 = 2; HELLOLADIES t1 * 3 + 1;",
}


def compilar(src):
    prog = parse(tokenize(src))
    return prog, check(prog)


def linhas(entrada):
    """Uma função no lugar do input(): entrega uma linha por vez e depois acaba."""
    it = iter(entrada)

    def ler():
        try:
            return next(it)
        except StopIteration:
            raise EOFError from None
    return ler


def saida_interpretador(prog, entrada=()):
    saida = []
    run(prog, out=saida.append, entrada=linhas(entrada))
    return saida


def saida_tac(prog, analise, entrada=()):
    saida = []
    execute(emit_ir(prog, analise), out=saida.append, entrada=linhas(entrada))
    return saida


def programas():
    """(nome, fonte) de cada exemplo válido e de cada trecho."""
    for nome in VALIDOS:
        yield nome, (EXEMPLOS / f"{nome}.cj").read_text()
    yield from TRECHOS.items()


class LeituraTest(unittest.TestCase):
    """CJPHONEHOME: a única expressão da linguagem com efeito colateral."""

    def test_vira_uma_instrucao_read(self):
        self.assertEqual(format_ir(emit_ir(*compilar("HESOYAM n = CJPHONEHOME; HELLOLADIES n;"))).splitlines(),
                         ["  1      n = read", "  2      print n"])

    def test_interpretador_e_tac_leem_igual(self):
        src = "HESOYAM a = CJPHONEHOME; HESOYAM b = CJPHONEHOME; HELLOLADIES a * b;"
        prog, analise = compilar(src)
        self.assertEqual(saida_interpretador(prog, ["6", "7"]), ["42"])
        self.assertEqual(saida_tac(prog, analise, ["6", "7"]), ["42"])

    def test_otimizador_nao_apaga_leitura_sem_uso(self):
        prog, analise = compilar("HESOYAM lixo = CJPHONEHOME; HELLOLADIES 1 + 1;")
        otimizado, conta = otimizar(emit_ir(prog, analise), analise)
        self.assertIn("read", format_ir(otimizado))  # some a soma, fica a leitura
        self.assertEqual(saida_interpretador(prog, ["9"]), ["2"])

    def test_entrada_que_nao_e_numero_da_erro(self):
        prog, _ = compilar("HELLOLADIES CJPHONEHOME;")
        with self.assertRaises(RuntimeError_):
            saida_interpretador(prog, ["seis"])


class IrTest(unittest.TestCase):
    def test_listagem_do_fatorial(self):
        self.assertEqual(format_ir(emit_ir(*compilar(FATORIAL))).splitlines(), [
            "  1      n = 5",
            "  2      r = 1",
            "  3  L1:",
            "  4      t1 = n > 1",
            "  5      ifFalse t1 goto L2",
            "  6      r = r * n",
            "  7      n = n - 1",
            "  8      goto L1",
            "  9  L2:",
            " 10      print r",
        ])

    def test_curto_circuito_vira_desvio(self):
        code = emit_ir(*compilar("HESOYAM a = FULLCLIP; HESOYAM b = a && GHOSTTOWN; HELLOLADIES b;"))
        self.assertEqual([str(q) for q in code], [
            "a = FULLCLIP", "t1 = a", "ifFalse t1 goto L1", "t1 = GHOSTTOWN", "L1:", "b = t1", "print b",
        ])

    def test_sombra_usa_nome_unico(self):
        code = emit_ir(*compilar(TRECHOS["sombra"]))
        self.assertEqual([str(q) for q in code], ["x = 1", "x_1 = x + 1", "print x_1", "print x"])

    def test_temporario_nao_colide_com_variavel(self):
        code = emit_ir(*compilar(TRECHOS["temporário não colide"]))
        self.assertEqual([str(q) for q in code], ["t1 = 2", "t2 = t1 * 3", "t3 = t2 + 1", "print t3"])

    def test_constantes(self):
        code = emit_ir(*compilar('HELLOLADIES "oi"; HELLOLADIES GHOSTTOWN; HELLOLADIES -5;'))
        self.assertEqual([str(q) for q in code], ['print "oi"', "print GHOSTTOWN", "t1 = -5", "print t1"])

    def test_tac_faz_o_mesmo_que_o_interpretador(self):
        for nome, src in programas():
            with self.subTest(nome):
                prog, analise = compilar(src)
                self.assertEqual(saida_tac(prog, analise), saida_interpretador(prog))

    def test_divisao_por_zero(self):
        with self.assertRaises(RuntimeError_):
            saida_tac(*compilar("HESOYAM z = 0; HELLOLADIES 1 / z;"))

    def test_cli(self):
        codigo, out, _ = cli(str(EXEMPLOS / "fatorial.cj"), "--ir")
        self.assertEqual(codigo, 0)
        self.assertIn("ifFalse t1 goto L2", out)


if __name__ == "__main__":
    unittest.main()
