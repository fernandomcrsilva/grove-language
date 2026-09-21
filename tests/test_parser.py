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

    def test_dump(self):
        texto = dump(p("HESOYAM x = 1;"))
        self.assertIn("Program", texto)
        self.assertIn("VarDecl", texto)
        self.assertIn("name: 'x'", texto)


if __name__ == "__main__":
    unittest.main()
