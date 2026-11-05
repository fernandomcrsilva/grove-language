"""A leitura de memória da ponte (gta/ponte.py --memoria), contra um processo filho no papel do jogo.

O filho guarda o nível num inteiro de 32 bits e troca o valor quando recebe uma linha.
Ler a memória de um filho não precisa de sudo, mesmo com o ptrace_scope em 1.
"""
import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location("ponte", Path(__file__).parent.parent / "gta" / "ponte.py")
ponte = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ponte)

JOGO_FALSO = r"""
import ctypes, sys
nivel = ctypes.c_int32(int(sys.argv[1]))
print(ctypes.addressof(nivel), flush=True)
for linha in sys.stdin:
    nivel.value = int(linha)
    print("ok", flush=True)
"""


@unittest.skipUnless(sys.platform.startswith("linux"), "lê /proc/<pid>/mem")
class MemoriaTest(unittest.TestCase):
    def setUp(self):
        self.jogo = subprocess.Popen([sys.executable, "-c", JOGO_FALSO, "2"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.endereco = int(self.jogo.stdout.readline())
        self.mem = ponte.abrir_memoria(self.jogo.pid)
        self.atual = 2

    def tearDown(self):
        os.close(self.mem)
        self.jogo.kill()
        self.jogo.communicate()

    def mudar(self, n):
        self.jogo.stdin.write(f"{n}\n")
        self.jogo.stdin.flush()
        self.jogo.stdout.readline()
        self.atual = n

    def calibrar(self, respostas):
        """Calibra como o jogador faria: muda o nível no jogo e digita o número."""
        respostas = iter(respostas)

        def perguntar(_):
            n = next(respostas)
            if n != self.atual:
                self.mudar(n)
            return str(n)

        # o filho é um processo de 64 bits: o nível dele fica acima dos 4 GB
        with contextlib.redirect_stdout(io.StringIO()):
            return ponte.calibrar(self.mem, self.jogo.pid, perguntar, limite=None)

    def test_varredura_acha_o_nivel(self):
        self.assertIn(self.endereco, ponte.varrer(self.mem, self.jogo.pid, 2, limite=None))

    def test_calibra_e_acompanha_o_jogo(self):
        endereco = self.calibrar([2, 5, 1, 4, 0, 3, 6, 2, 5, 1])
        for n in (4, 0, 6, 3):
            self.mudar(n)
            self.assertEqual(ponte.nivel_da_memoria(self.mem, endereco), n)

    def test_resposta_repetida_nao_conta_como_mudanca(self):
        # sem a checagem, o 5 repetido "não eliminaria ninguém" e a calibração pararia cedo
        endereco = self.calibrar([2, 5, 5, 1, 4, 0, 3, 6, 2, 5, 1])
        self.mudar(4)
        self.assertEqual(ponte.nivel_da_memoria(self.mem, endereco), 4)

    def test_leitura_fora_da_memoria(self):
        with self.assertRaises(OSError):
            ponte.ler(self.mem, 0)


if __name__ == "__main__":
    unittest.main()
