"""Falas do jogo tocadas ao compilar ou ao dar erro.

Procura assets/<evento>.wav e toca com o primeiro player disponível no sistema.
Sem arquivo ou sem player, não faz nada: a CLI nunca falha por causa do som.
"""
import shutil
import subprocess
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

EVENTOS = {
    "passed": "MISSION PASSED! Respect +",
    "lex_error": "WASTED",
    "parse_error": "All you had to do was follow the damn train, CJ!",
    "semantic_error": "BUSTED",
    "runtime_error": "Ah shit, here we go again.",
}

# (executável, argumentos antes do arquivo); o primeiro que existir no PATH é usado
PLAYERS = [
    ("paplay", []),
    ("aplay", ["-q"]),
    ("afplay", []),
    ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
    ("powershell", ["-c", "(New-Object Media.SoundPlayer '{arquivo}').PlaySync()"]),
]


def arquivo_de(evento: str) -> Path:
    return ASSETS / f"{evento}.wav"


def play(evento: str) -> bool:
    """Toca o som do evento em segundo plano. Retorna True se disparou um player."""
    wav = arquivo_de(evento)
    if not wav.is_file():
        return False
    for exe, args in PLAYERS:
        if shutil.which(exe):
            cmd = [exe] + [a.format(arquivo=wav) for a in args]
            if exe != "powershell":
                cmd.append(str(wav))
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    return False
