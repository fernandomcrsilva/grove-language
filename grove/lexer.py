"""Análise léxica: texto-fonte → lista de Token."""
from .tokens import OPERATORS, WORDS, Token, TokenType


class LexError(Exception):
    pass


def tokenize(src: str) -> list[Token]:
    tokens: list[Token] = []
    i, line, col = 0, 1, 1
    n = len(src)

    while i < n:
        c = src[i]

        if c == "\n":
            i, line, col = i + 1, line + 1, 1
            continue
        if c.isspace():
            i, col = i + 1, col + 1
            continue
        if c == "#":  # comentário até o fim da linha
            while i < n and src[i] != "\n":
                i += 1
            continue

        start_col = col

        two = src[i:i + 2]
        if two in OPERATORS:  # antes dos de um: "!=" não é "!" + "="
            tokens.append(Token(OPERATORS[two], two, line, start_col))
            i, col = i + 2, col + 2
            continue
        if c in OPERATORS:
            tokens.append(Token(OPERATORS[c], c, line, start_col))
            i, col = i + 1, col + 1
            continue

        if c.isdigit():
            j = i
            while j < n and src[j].isdigit():
                j += 1
            text = src[i:j]
            tokens.append(Token(TokenType.NUMBER, text, line, start_col, int(text)))
            col += j - i
            i = j
            continue

        if c == '"':
            j = i + 1
            while j < n and src[j] not in '"\n':
                j += 1
            if j >= n or src[j] != '"':
                raise LexError(f"linha {line}, coluna {start_col}: string sem fechar")
            raw = src[i:j + 1]
            tokens.append(Token(TokenType.STRING, raw, line, start_col, raw[1:-1]))
            col += j + 1 - i
            i = j + 1
            continue

        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            word = src[i:j]
            tokens.append(Token(WORDS.get(word, TokenType.IDENT), word, line, start_col))
            col += j - i
            i = j
            continue

        raise LexError(f"linha {line}, coluna {col}: caractere inesperado {c!r}")

    tokens.append(Token(TokenType.EOF, "", line, col))
    return tokens
