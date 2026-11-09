"""O catálogo de docs/erros.md é a fonte da verdade: cada linha da tabela é um teste.

Assim a página não envelhece calada — se uma mensagem do compilador mudar e o
catálogo não, a suíte quebra aqui.
"""
import io
import re
import unittest
from pathlib import Path
from unittest import mock

from tests.test_semantic import cli

RAIZ = Path(__file__).resolve().parent.parent
ERROS = RAIZ / "examples" / "erros"
CATALOGO = RAIZ / "docs" / "erros.md"

# os dois exemplos de CJPHONEHOME: o que a entrada entrega antes de acabar
ENTRADAS = {"execucao_entrada_nao_inteira.cj": "abc\n"}

# | descrição | [`arquivo.cj`](caminho) | `mensagem` |
LINHA = re.compile(r"^\|[^|]+\|[^|]*\[`(?P<arquivo>[\w.]+\.cj)`\][^|]*\|\s*`(?P<mensagem>[^`]+)`\s*\|")


def catalogo():
    """[(arquivo, mensagem esperada)] lido da tabela de docs/erros.md."""
    return [(m["arquivo"], m["mensagem"]) for m in map(LINHA.match, CATALOGO.read_text().splitlines()) if m]


class CatalogoDeErrosTest(unittest.TestCase):
    def test_cada_exemplo_da_a_mensagem_do_catalogo(self):
        for arquivo, mensagem in catalogo():
            with self.subTest(arquivo):
                with mock.patch("sys.stdin", io.StringIO(ENTRADAS.get(arquivo, ""))):
                    codigo, _, err = cli(str(ERROS / arquivo))
                self.assertEqual(codigo, 1, f"{arquivo} devia sair com 1")
                self.assertIn(f"erro: {mensagem}", err)

    def test_um_diagnostico_por_arquivo(self):
        """Um erro, e nenhum aviso junto: a mensagem do catálogo é tudo o que sai."""
        for arquivo, _ in catalogo():
            with self.subTest(arquivo):
                with mock.patch("sys.stdin", io.StringIO(ENTRADAS.get(arquivo, ""))):
                    _, _, err = cli(str(ERROS / arquivo))
                self.assertEqual(err.count("erro: "), 1, f"{arquivo} devia provocar um erro só:\n{err}")
                self.assertNotIn("aviso:", err, f"{arquivo} não devia vir com aviso junto:\n{err}")

    def test_catalogo_cobre_todos_os_exemplos(self):
        self.assertEqual(sorted(a for a, _ in catalogo()), sorted(p.name for p in ERROS.glob("*.cj")))


if __name__ == "__main__":
    unittest.main()
