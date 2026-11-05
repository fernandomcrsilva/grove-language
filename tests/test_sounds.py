import unittest
from unittest import mock

from grove import sounds


class SoundsTest(unittest.TestCase):
    def test_sem_arquivo_fica_em_silencio(self):
        with mock.patch.object(sounds, "ASSETS", sounds.ASSETS / "inexistente"):
            self.assertFalse(sounds.play("passed"))

    def test_com_arquivo_dispara_player(self):
        with mock.patch.object(sounds.Path, "is_file", return_value=True), \
             mock.patch.object(sounds.shutil, "which", side_effect=lambda exe: exe == "aplay"), \
             mock.patch.object(sounds.subprocess, "Popen") as popen:
            self.assertTrue(sounds.play("lex_error"))
            cmd = popen.call_args.args[0]
            self.assertEqual(cmd[0], "aplay")
            self.assertTrue(cmd[-1].endswith("assets/lex_error.wav"))

    def test_eventos_conhecidos(self):
        self.assertEqual(set(sounds.EVENTOS), {"passed", "lex_error", "parse_error", "semantic_error", "runtime_error"})


if __name__ == "__main__":
    unittest.main()
