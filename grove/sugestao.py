"""Sugestões para nomes digitados errado: "você quis dizer HESOYAM?".

Os cheats são compridos (GOODBYECRUELWORLD tem 17 letras), então o erro mais
provável de quem escreve Grove é um cheat com uma letra a mais, a menos ou trocada.
"""
from .tokens import WORDS


def distancia(a: str, b: str) -> int:
    """Distância de edição contando inserção, remoção, troca e a inversão de duas letras vizinhas."""
    anterior, linha = None, list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        nova = [i]
        for j, cb in enumerate(b, 1):
            custo = min(linha[j] + 1, nova[j - 1] + 1, linha[j - 1] + (ca != cb))
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:  # HESOYMA → HESOYAM custa 1
                custo = min(custo, anterior[j - 2] + 1)
            nova.append(custo)
        anterior, linha = linha, nova
    return linha[-1]


def _mais_proximo(palavra: str, candidatos, folga) -> str | None:
    """O candidato mais próximo, se a diferença couber na folga que o tamanho dele permite."""
    melhor = min(candidatos, key=lambda c: (distancia(palavra, c), c), default=None)
    if melhor is None or melhor == palavra:
        return None
    return melhor if distancia(palavra, melhor) <= folga(melhor) else None


def cheat_parecido(palavra: str) -> str | None:
    """O cheat que a palavra provavelmente queria ser: hesoyam, HESOYM e HESOYMA dão HESOYAM."""
    if len(palavra) < 4 or palavra in WORDS:
        return None
    if palavra.upper() in WORDS:  # só a caixa está errada
        return palavra.upper()
    return _mais_proximo(palavra.upper(), WORDS, lambda c: max(1, len(c) // 4))


def mensagem_cheat(palavra: str, cheat: str) -> str:
    if palavra.upper() == cheat:
        return f"'{palavra}' não é um cheat da Grove: os cheats são em maiúsculas ({cheat})"
    return f"'{palavra}' não é um cheat da Grove; você quis dizer {cheat}?"


def nome_parecido(palavra: str, nomes) -> str | None:
    """A variável declarada que a palavra provavelmente queria ser (contdor → contador)."""
    if len(palavra) < 3:
        return None
    return _mais_proximo(palavra, nomes, lambda n: max(1, len(n) // 3))
