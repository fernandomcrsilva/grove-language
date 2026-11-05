import unittest
from pathlib import Path

from grove.interpreter import RuntimeError_
from grove.ir import emit_ir, execute, format_ir
from grove.otimizador import otimizar, resumo

from tests.test_ir import compilar, programas, saida_interpretador
from tests.test_semantic import cli

EXEMPLOS = Path(__file__).resolve().parent.parent / "examples"


def tac(src):
    prog, analise = compilar(src)
    return emit_ir(prog, analise), analise


def otimizado(src):
    code, analise = tac(src)
    return [str(q) for q in otimizar(code, analise)[0]]


def rodar(code):
    saida = []
    try:
        execute(code, saida.append)
    except RuntimeError_ as e:
        saida.append(f"erro: {e}")
    return saida


class OtimizadorTest(unittest.TestCase):
    def test_exemplo_encolhe(self):
        code, analise = tac((EXEMPLOS / "otimizacao.cj").read_text())
        novo, conta = otimizar(code, analise)
        self.assertEqual([str(q) for q in novo], ["segundos = 3600", "dobro = 7200", "print 7200", 'print "uma vez"'])
        self.assertEqual(resumo(code, novo, conta).split(" · ")[0], "13 → 4 instruções")

    def test_contas_com_constantes(self):
        self.assertEqual(otimizado("HELLOLADIES 2 + 3 * 4;"), ["print 14"])
        self.assertEqual(otimizado("HELLOLADIES -7 / 2; HELLOLADIES -7 % 2;"), ["print -4", "print 1"])
        self.assertEqual(otimizado('HELLOLADIES "Grove" + " Street";'), ['print "Grove Street"'])
        self.assertEqual(otimizado("HELLOLADIES !(1 < 2) || 3 == 3;"), ["print FULLCLIP"])

    def test_propaga_ate_o_proximo_rotulo(self):
        self.assertEqual(otimizado("HESOYAM a = 5; HESOYAM b = a * 2; HELLOLADIES b;"), ["a = 5", "b = 10", "print 10"])
        # dentro do laço a variável muda: nada é propagado para lá
        self.assertEqual(otimizado((EXEMPLOS / "fatorial.cj").read_text()),
                         [str(q) for q in tac((EXEMPLOS / "fatorial.cj").read_text())[0]])

    def test_simplificacoes(self):
        self.assertEqual(otimizado("HESOYAM x = 3; KANGAROO (x > 0) { HELLOLADIES x + 0; HELLOLADIES x * 1; HELLOLADIES x * 0; x = x - 1; }")[3:7],
                         ["ifFalse t1 goto L2", "print x", "print x", "print 0"])

    def test_desvios_constantes(self):
        self.assertEqual(otimizado("TURNUPTHEHEAT (GHOSTTOWN) { HELLOLADIES 1; } HELLOLADIES 2;"), ["print 2"])
        self.assertEqual(otimizado("TURNUPTHEHEAT (FULLCLIP) { HELLOLADIES 1; } TURNDOWNTHEHEAT { HELLOLADIES 2; }"), ["print 1"])
        procurado = otimizado((EXEMPLOS / "procurado.cj").read_text())
        self.assertNotIn("ifFalse FULLCLIP goto L4", procurado)
        self.assertEqual(len(procurado), 15)

    def test_curto_circuito_com_constante(self):
        self.assertEqual(otimizado("HESOYAM p = FULLCLIP; HELLOLADIES p && GHOSTTOWN;"), ["p = FULLCLIP", "print GHOSTTOWN"])

    def test_divisao_por_zero_continua_erro(self):
        for src in ("HELLOLADIES 1 / 0;", "HESOYAM z = 0; HELLOLADIES 1 % z == 1;", "HELLOLADIES 1; HELLOLADIES 1 / 0;"):
            with self.subTest(src=src):
                code, analise = tac(src)
                novo, _ = otimizar(code, analise)
                self.assertEqual(rodar(novo), rodar(code))
                self.assertTrue(rodar(novo)[-1].startswith("erro: divisão por zero"))

    def test_nao_muda_o_original(self):
        code, analise = tac((EXEMPLOS / "otimizacao.cj").read_text())
        antes = format_ir(code)
        otimizar(code, analise)
        self.assertEqual(format_ir(code), antes)

    def test_mesma_saida_em_todos_os_programas(self):
        for nome, src in programas():
            with self.subTest(nome):
                prog, analise = compilar(src)
                code = emit_ir(prog, analise)
                self.assertEqual(rodar(otimizar(code, analise)[0]), rodar(code))
                self.assertEqual(rodar(code), saida_interpretador(prog))

    def test_cli(self):
        codigo, out, _ = cli(str(EXEMPLOS / "otimizacao.cj"), "--otimizar")
        self.assertEqual(codigo, 0)
        self.assertIn("print 7200", out)
        self.assertIn("# 13 → 4 instruções", out)


if __name__ == "__main__":
    unittest.main()
