"""Tabela de tokens da linguagem Grove.

Keywords são cheats de GTA San Andreas; pontuação e operadores são os de C.
"""
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # cheats
    VAR = auto()      # HESOYAM
    IF = auto()       # TURNUPTHEHEAT
    ELIF = auto()     # BRINGITON
    ELSE = auto()     # TURNDOWNTHEHEAT
    WHILE = auto()    # KANGAROO
    BREAK = auto()    # GOODBYECRUELWORLD
    PRINT = auto()    # HELLOLADIES
    TRUE = auto()     # FULLCLIP
    FALSE = auto()    # GHOSTTOWN
    # pontuação
    LBRACE = auto()   # {
    RBRACE = auto()   # }
    SEMI = auto()     # ;
    LPAREN = auto()   # (
    RPAREN = auto()   # )
    # operadores
    ASSIGN = auto()   # =
    EQ = auto()       # ==
    NE = auto()       # !=
    LT = auto()       # <
    GT = auto()       # >
    LE = auto()       # <=
    GE = auto()       # >=
    NOT = auto()      # !
    AND = auto()      # &&
    OR = auto()       # ||
    PLUS = auto()     # +
    MINUS = auto()    # -
    STAR = auto()     # *
    SLASH = auto()    # /
    MOD = auto()      # %
    # literais e fim
    NUMBER = auto()
    STRING = auto()
    IDENT = auto()
    EOF = auto()


# palavras reservadas: os cheats
WORDS = {
    "HESOYAM": TokenType.VAR,
    "TURNUPTHEHEAT": TokenType.IF,
    "BRINGITON": TokenType.ELIF,
    "TURNDOWNTHEHEAT": TokenType.ELSE,
    "KANGAROO": TokenType.WHILE,
    "GOODBYECRUELWORLD": TokenType.BREAK,
    "HELLOLADIES": TokenType.PRINT,
    "FULLCLIP": TokenType.TRUE,
    "GHOSTTOWN": TokenType.FALSE,
}

# operadores e pontuação: os de dois caracteres precisam ser testados antes dos de um
OPERATORS = {
    "==": TokenType.EQ,
    "!=": TokenType.NE,
    "<=": TokenType.LE,
    ">=": TokenType.GE,
    "&&": TokenType.AND,
    "||": TokenType.OR,
    "=": TokenType.ASSIGN,
    "<": TokenType.LT,
    ">": TokenType.GT,
    "!": TokenType.NOT,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "%": TokenType.MOD,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ";": TokenType.SEMI,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    col: int
    value: object = None  # int para NUMBER, str sem aspas para STRING

    def __str__(self):
        return f"{self.line}:{self.col}\t{self.type.name}\t{self.lexeme}"
