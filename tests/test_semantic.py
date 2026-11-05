import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from grove.__main__ import main
from grove.lexer import tokenize
from grove.parser import parse
from grove.semantic import BOOLEANO, INTEIRO, STRING, SemanticError, check, format_symbols

from tests.test_lexer import FATORIAL

EXEMPLOS = Path(__file__).resolve().parent.parent / "examples"


def analisar(src):
    return check(parse(tokenize(src)))


def erros(src):
    try:
        analisar(src)
    except SemanticError as e:
        return [str(d) for d in e.erros]
    raise AssertionError(f"esperado erro semântico em {src!r}")


class SemanticTest(unittest.TestCase):
    def test_programa_valido_gera_tabela_de_simbolos(self):
        a = analisar(FATORIAL)
        self.assertEqual([(s.nome, s.tipo, s.escopo, s.linha, s.coluna) for s in a.simbolos],
                         [("n", INTEIRO, 0, 2, 9), ("r", INTEIRO, 0, 3, 9)])
        self.assertEqual(a.avisos, [])
        self.assertIn("n\tinteiro\t0\t2:9\tn\tsim", format_symbols(a))

    def test_exemplos_validos_passam(self):
        for nome in ("fatorial", "fizzbuzz", "procurado", "erro_execucao"):
            with self.subTest(nome):
                analisar((EXEMPLOS / f"{nome}.cj").read_text())

    def test_cada_erro_com_posicao(self):
        casos = {
            "HELLOLADIES y;": "linha 1, coluna 13: variável 'y' não declarada",
            "y = 1;": "linha 1, coluna 1: variável 'y' não declarada",
            "HESOYAM a = 1;\nHESOYAM a = 2;": "linha 2, coluna 9: variável 'a' já declarada neste escopo (linha 1)",
            'HELLOLADIES 1 + "a";': "linha 1, coluna 15: tipos incompatíveis para '+': inteiro e string",
            'HELLOLADIES "a" * "b";': "'*' não se aplica a string",
            "HELLOLADIES -FULLCLIP;": "'-' exige inteiro, recebeu booleano",
            "HELLOLADIES !1;": "'!' exige booleano, recebeu inteiro",
            'HESOYAM x = 1; x = "a";': "linha 1, coluna 16: 'x' é inteiro, não pode receber string",
            "TURNUPTHEHEAT (1) { }": "linha 1, coluna 1: condição do TURNUPTHEHEAT exige booleano, recebeu inteiro",
            'KANGAROO ("a") { }': "condição do KANGAROO exige booleano, recebeu string",
            "GOODBYECRUELWORLD;": "linha 1, coluna 1: GOODBYECRUELWORLD fora de laço",
        }
        for src, esperado in casos.items():
            with self.subTest(src=src):
                self.assertEqual(len(erros(src)), 1)
                self.assertIn(esperado, erros(src)[0])

    def test_junta_todos_os_erros_em_ordem(self):
        achados = erros((EXEMPLOS / "erro_semantico.cj").read_text())
        self.assertEqual([e.split(":")[0] for e in achados],
                         ["linha 4, coluna 1", "linha 5, coluna 1", "linha 6, coluna 17", "linha 8, coluna 1"])

    def test_sem_erro_em_cascata(self):
        self.assertEqual(len(erros("HELLOLADIES y + 1 * 2;")), 1)
        self.assertEqual(len(erros("TURNUPTHEHEAT (!y) { }")), 1)
        self.assertEqual(len(erros("HESOYAM x = y; HELLOLADIES x + 1;")), 1)

    def test_anota_tipos_na_ast(self):
        prog = parse(tokenize('HELLOLADIES 1 + 2; HELLOLADIES "a" + "b"; HELLOLADIES 1 < 2 && FULLCLIP;'))
        check(prog)
        self.assertEqual([p.value.tipo for p in prog.body], [INTEIRO, STRING, BOOLEANO])

    def test_break_dentro_de_if_no_laco(self):
        analisar("KANGAROO (FULLCLIP) { TURNUPTHEHEAT (FULLCLIP) { GOODBYECRUELWORLD; } }")

    def test_inicializador_le_a_variavel_de_fora(self):
        prog = parse(tokenize("HESOYAM x = 1; { HESOYAM x = x + 1; HELLOLADIES x; }"))
        check(prog)
        externo, bloco = prog.body
        interno = bloco.stmts[0]
        self.assertIs(interno.value.left.simbolo, externo.simbolo)
        self.assertIsNot(interno.simbolo, externo.simbolo)

    def test_sombra_ganha_nome_unico_sem_colidir(self):
        a = analisar("HESOYAM x = 1; { HESOYAM x = 2; HELLOLADIES x; } HELLOLADIES x;")
        self.assertEqual([s.unico for s in a.simbolos], ["x", "x_1"])
        a = analisar("HESOYAM x = 1; { HESOYAM x = 2; HELLOLADIES x; } HESOYAM x_1 = 3; HELLOLADIES x + x_1;")
        self.assertEqual([s.unico for s in a.simbolos], ["x", "x_2", "x_1"])

    def test_mudancas_desde_o_ap1(self):
        # tipo fixo na declaração (o interpretador aceitava trocar)
        self.assertEqual(len(erros('HESOYAM y = 1; y = "a";')), 1)
        # FULLCLIP == 1 dava FULLCLIP (True == 1 em Python)
        self.assertEqual(len(erros("HELLOLADIES FULLCLIP == 1;")), 1)
        # erro num ramo que nunca roda também é achado
        self.assertEqual(len(erros("TURNUPTHEHEAT (GHOSTTOWN) { HELLOLADIES z; }")), 1)

    def test_sugere_variavel_ou_cheat_parecido(self):
        self.assertEqual(erros("HESOYAM contador = 0; HELLOLADIES contdor;"),
                         ["linha 1, coluna 35: variável 'contdor' não declarada; você quis dizer 'contador'?"])
        self.assertIn("você quis dizer o cheat FULLCLIP?", erros("HELLOLADIES FULCLIP;")[0])
        self.assertIn("você quis dizer o cheat HESOYAM?", erros("HESOYM = 5;")[0])
        self.assertEqual(erros("HESOYAM x = 1; HELLOLADIES y;"), ["linha 1, coluna 28: variável 'y' não declarada"])

    def test_avisos_nao_impedem(self):
        a = analisar("HESOYAM x = 1; x = 2; HELLOLADIES 7 / 0; HELLOLADIES 7 % 0;")
        self.assertEqual([str(d) for d in a.avisos], [
            "linha 1, coluna 9: variável 'x' declarada e nunca lida",
            "linha 1, coluna 37: divisão por zero",
            "linha 1, coluna 56: divisão por zero",
        ])


def cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("grove.__main__.play"), redirect_stdout(out), redirect_stderr(err):
        codigo = main(list(args))
    return codigo, out.getvalue(), err.getvalue()


class LeituraSemanticaTest(unittest.TestCase):
    def test_cjphonehome_e_inteiro(self):
        a = analisar("HESOYAM n = CJPHONEHOME; HELLOLADIES n + 1;")
        self.assertEqual([(s.nome, s.tipo) for s in a.simbolos], [("n", INTEIRO)])

    def test_cjphonehome_nao_serve_de_condicao(self):
        with self.assertRaises(SemanticError) as e:
            analisar("KANGAROO (CJPHONEHOME) { }")
        self.assertIn("exige booleano, recebeu inteiro", str(e.exception))


class CliSemanticaTest(unittest.TestCase):
    def test_erro_semantico_lista_todos_e_sai_com_1(self):
        codigo, out, err = cli(str(EXEMPLOS / "erro_semantico.cj"))
        self.assertEqual(codigo, 1)
        self.assertEqual(out, "")
        self.assertEqual(err.count("erro: linha"), 4)
        self.assertIn("4 erros semânticos", err)

    def test_simbolos(self):
        codigo, out, _ = cli(str(EXEMPLOS / "procurado.cj"), "--simbolos")
        self.assertEqual(codigo, 0)
        self.assertIn("policia_ligada\tbooleano\t0\t3:9", out)

    def test_aviso_vai_para_stderr_e_executa(self):
        codigo, _, err = cli(str(EXEMPLOS / "erro_execucao.cj"))
        self.assertEqual(codigo, 1)
        self.assertIn("aviso: linha 2, coluna 15: divisão por zero", err)
        self.assertIn("erro: divisão por zero", err)

    def test_ast_nao_exige_semantica_valida(self):
        codigo, out, _ = cli(str(EXEMPLOS / "erro_semantico.cj"), "--ast")
        self.assertEqual(codigo, 0)
        self.assertTrue(out.startswith("Program"))


if __name__ == "__main__":
    unittest.main()
