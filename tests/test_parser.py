import unittest

from grove.ast import Assign, Binary, Block, If, Literal, Print, Program, Unary, Var, VarDecl, While, dump
from grove.lexer import tokenize
from grove.parser import ParseError, parse

from tests.test_lexer import FATORIAL


def p(src):
    return parse(tokenize(src))


class ParserTest(unittest.TestCase):
    def test_fatorial(self):
        prog = p(FATORIAL)
        self.assertIsInstance(prog, Program)
        self.assertEqual(len(prog.body), 4)
        decl, _, loop, out = prog.body
        self.assertEqual(decl, VarDecl("n", Literal(5)))
        self.assertIsInstance(loop, While)
        self.assertEqual(loop.cond, Binary(Var("n"), ">", Literal(1)))
        self.assertEqual(len(loop.body.stmts), 2)
        self.assertEqual(loop.body.stmts[0], Assign("r", Binary(Var("r"), "*", Var("n"))))
        self.assertEqual(out, Print(Var("r")))

    def test_precedencia(self):
        expr = p("HELLOLADIES 1 + 2 * 3;").body[0].value
        self.assertEqual(expr, Binary(Literal(1), "+", Binary(Literal(2), "*", Literal(3))))
        expr = p("HELLOLADIES (1 + 2) * 3;").body[0].value
        self.assertEqual(expr, Binary(Binary(Literal(1), "+", Literal(2)), "*", Literal(3)))

    def test_logicos_e_unario(self):
        expr = p("HELLOLADIES ! a && b || c;").body[0].value
        self.assertEqual(expr, Binary(Binary(Unary("!", Var("a")), "&&", Var("b")), "||", Var("c")))
        self.assertEqual(p("HELLOLADIES -1;").body[0].value, Unary("-", Literal(1)))

    def test_if_else(self):
        stmt = p("TURNUPTHEHEAT (x == 1) { HELLOLADIES FULLCLIP; } TURNDOWNTHEHEAT { HELLOLADIES GHOSTTOWN; }").body[0]
        self.assertIsInstance(stmt, If)
        self.assertEqual(stmt.then, Block([Print(Literal(True))]))
        self.assertEqual(stmt.orelse, Block([Print(Literal(False))]))

    def test_else_if_encadeado(self):
        stmt = p("TURNUPTHEHEAT (a) { } TURNDOWNTHEHEAT TURNUPTHEHEAT (b) { }").body[0]
        self.assertIsInstance(stmt.orelse, If)

    def test_bringiton_e_atalho_de_else_if(self):
        longo = p("TURNUPTHEHEAT (a) { } TURNDOWNTHEHEAT TURNUPTHEHEAT (b) { } TURNDOWNTHEHEAT { }").body[0]
        curto = p("TURNUPTHEHEAT (a) { } BRINGITON (b) { } TURNDOWNTHEHEAT { }").body[0]
        self.assertEqual(curto, longo)

    def test_erro_sintatico_aponta_posicao(self):
        with self.assertRaises(ParseError) as cm:
            p("HESOYAM x = 5\nHELLOLADIES x;")
        self.assertIn("linha 2", str(cm.exception))
        self.assertIn(";", str(cm.exception))

    def test_junta_todos_os_erros_sintaticos(self):
        src = (
            "HESOYM vida = 100;\n"                  # 1: cheat digitado errado
            "HESOYAM grana = 250000;\n"
            "TURNUPTHEHEET (grana > 0) {\n"         # 3: cheat digitado errado
            "    HELLOLADIES grana;\n"
            "}\n"
            "hesoyam x = 1;\n"                       # 6: cheat em minúsculas
            "KANGAROO (grana > ) {\n"                # 7: falta a expressão
            "    HELLOLADIES 1;\n"
            "}\n"
            "TURNDOWNTHEHEAT { }\n"                  # 10: else sem if
            "HESOYAM y = 5\n"
            "HELLOLADIES y;\n"                       # 12: faltou o ; da linha 11
        )
        with self.assertRaises(ParseError) as cm:
            p(src)
        self.assertEqual([int(e.split(",")[0].split()[1]) for e in cm.exception.erros], [1, 3, 6, 7, 10, 12])

    def test_sugere_o_cheat_certo(self):
        casos = {
            "HESOYM x = 1;": "'HESOYM' não é um cheat da Grove; você quis dizer HESOYAM?",
            "HESOYMA x = 1;": "você quis dizer HESOYAM?",
            "TURNUPTHEHEET (FULLCLIP) { }": "você quis dizer TURNUPTHEHEAT?",
            "KANGARO (FULLCLIP) { }": "você quis dizer KANGAROO?",
            "HELLOLADYS 1;": "você quis dizer HELLOLADIES?",
            "GOODBYECRUELWRLD;": "você quis dizer GOODBYECRUELWORLD?",
            "hesoyam x = 1;": "os cheats são em maiúsculas (HESOYAM)",
        }
        for src, trecho in casos.items():
            with self.subTest(src=src), self.assertRaises(ParseError) as cm:
                p(src)
            self.assertIn(trecho, str(cm.exception))
            self.assertIn("linha 1, coluna 1:", str(cm.exception))

    def test_nome_comum_nao_vira_sugestao(self):
        with self.assertRaises(ParseError) as cm:
            p("nome x = 1;")
        self.assertIn("esperado =", str(cm.exception))
        self.assertNotIn("quis dizer", str(cm.exception))

    def test_recuperacao_sem_cascata(self):
        for src in ("TURNUPTHEHEAT (x > ) { HELLOLADIES 1; HELLOLADIES 2; }",
                    "HESOYAM a = (1 + 2; HELLOLADIES a; HELLOLADIES a;",
                    "KANGAROO (FULLCLIP) {"):
            with self.subTest(src=src), self.assertRaises(ParseError) as cm:
                p(src)
            self.assertEqual(len(cm.exception.erros), 1, cm.exception.erros)

    def test_else_sem_if(self):
        with self.assertRaises(ParseError) as cm:
            p("BRINGITON (FULLCLIP) { }")
        self.assertIn("BRINGITON sem um TURNUPTHEHEAT antes", str(cm.exception))

    def test_dump(self):
        texto = dump(p("HESOYAM x = 1;"))
        self.assertIn("Program", texto)
        self.assertIn("VarDecl", texto)
        self.assertIn("name: 'x'", texto)


if __name__ == "__main__":
    unittest.main()
