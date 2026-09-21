import unittest

from grove.lexer import LexError, tokenize
from grove.tokens import TokenType as T

FATORIAL = """\
# fatorial de 5
HESOYAM n = 5;
HESOYAM r = 1;
KANGAROO (n > 1) {
    r = r * n;
    n = n - 1;
}
HELLOLADIES r;
"""


class LexerTest(unittest.TestCase):
    def types(self, src):
        return [t.type for t in tokenize(src)]

    def test_fatorial_sequencia_de_tokens(self):
        self.assertEqual(
            self.types(FATORIAL),
            [T.VAR, T.IDENT, T.ASSIGN, T.NUMBER, T.SEMI,
             T.VAR, T.IDENT, T.ASSIGN, T.NUMBER, T.SEMI,
             T.WHILE, T.LPAREN, T.IDENT, T.GT, T.NUMBER, T.RPAREN, T.LBRACE,
             T.IDENT, T.ASSIGN, T.IDENT, T.STAR, T.IDENT, T.SEMI,
             T.IDENT, T.ASSIGN, T.IDENT, T.MINUS, T.NUMBER, T.SEMI,
             T.RBRACE,
             T.PRINT, T.IDENT, T.SEMI,
             T.EOF],
        )

    def test_linha_e_coluna(self):
        toks = tokenize(FATORIAL)
        n = toks[1]
        self.assertEqual((n.lexeme, n.line, n.col), ("n", 2, 9))
        self.assertEqual((toks[10].lexeme, toks[10].line, toks[10].col), ("KANGAROO", 4, 1))

    def test_literais(self):
        toks = tokenize('HESOYAM s = "oi mundo"; HESOYAM b = FULLCLIP;')
        self.assertEqual(toks[3].type, T.STRING)
        self.assertEqual(toks[3].value, "oi mundo")
        self.assertEqual(toks[8].type, T.TRUE)
        self.assertEqual(tokenize("42")[0].value, 42)

    def test_operadores_de_dois_caracteres(self):
        self.assertEqual(self.types("== != <= >= && || ! %")[:-1],
                         [T.EQ, T.NE, T.LE, T.GE, T.AND, T.OR, T.NOT, T.MOD])

    def test_pontuacao(self):
        self.assertEqual(self.types("{ } ; ( ) ! != x")[:-1],
                         [T.LBRACE, T.RBRACE, T.SEMI, T.LPAREN, T.RPAREN, T.NOT, T.NE, T.IDENT])

    def test_comentario_e_ignorado(self):
        self.assertEqual(self.types("# so comentario\n"), [T.EOF])

    def test_caractere_invalido(self):
        with self.assertRaises(LexError) as cm:
            tokenize("HESOYAM x = $;")
        self.assertIn("linha 1", str(cm.exception))
        self.assertIn("'$'", str(cm.exception))

    def test_string_sem_fechar(self):
        with self.assertRaises(LexError):
            tokenize('"aberta')


if __name__ == "__main__":
    unittest.main()
