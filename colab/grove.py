"""
Grove — linguagem cujas palavras-chave são cheats de GTA San Andreas
(o resto da sintaxe é C: `{ } ;`, `( )`, `! && ||`).

Arquivo único, sem dependências: cole numa célula do Colab ou rode
`python3 grove.py` (o autoteste do final confere léxico, sintaxe e erros).

Conteúdo:
    1. Analisador léxico   — texto-fonte → tabela de tokens
    2. Nós da AST          — com impressão em árvore
    3. Analisador sintático — descida recursiva, um método por regra da gramática
"""
import enum
from dataclasses import dataclass
from typing import Any

# =====================================================================
# 1. ESPECIFICAÇÃO DE TOKENS (ANALISADOR LÉXICO)
# =====================================================================


class TokenType(enum.Enum):
    # Palavras-chave: os cheats
    VAR = "HESOYAM"                 # declaração de variável
    IF = "TURNUPTHEHEAT"            # se
    ELIF = "BRINGITON"              # senão se
    ELSE = "TURNDOWNTHEHEAT"        # senão
    WHILE = "KANGAROO"              # enquanto
    BREAK = "GOODBYECRUELWORLD"     # sai do laço
    PRINT = "HELLOLADIES"           # imprime
    TRUE = "FULLCLIP"               # verdadeiro
    FALSE = "GHOSTTOWN"             # falso

    # Operadores
    EQ = "=="
    NE = "!="
    LE = "<="
    GE = ">="
    AND = "&&"
    OR = "||"
    ASSIGN = "="
    LT = "<"
    GT = ">"
    NOT = "!"
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    MOD = "%"

    # Pontuação
    LBRACE = "{"
    RBRACE = "}"
    LPAREN = "("
    RPAREN = ")"
    SEMI = ";"

    # Literais, identificadores e fim
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENT = "IDENT"
    EOF = "EOF"


CHEATS = (TokenType.VAR, TokenType.IF, TokenType.ELIF, TokenType.ELSE, TokenType.WHILE,
          TokenType.BREAK, TokenType.PRINT, TokenType.TRUE, TokenType.FALSE)

SIMBOLOS = (TokenType.EQ, TokenType.NE, TokenType.LE, TokenType.GE, TokenType.AND, TokenType.OR,
            TokenType.ASSIGN, TokenType.LT, TokenType.GT, TokenType.NOT, TokenType.PLUS,
            TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.MOD, TokenType.LBRACE,
            TokenType.RBRACE, TokenType.LPAREN, TokenType.RPAREN, TokenType.SEMI)

WORDS = {t.value: t for t in CHEATS}        # "HESOYAM" → VAR
OPERATORS = {t.value: t for t in SIMBOLOS}  # os de dois caracteres são testados antes dos de um


@dataclass(frozen=True, repr=False)
class Token:
    type: TokenType
    lexeme: str
    line: int
    col: int
    value: Any = None  # int para NUMBER, str sem aspas para STRING

    def __repr__(self):
        extra = "" if self.value is None else f", valor={self.value!r}"
        lex = repr(self.lexeme) + ","
        return f"🌴 Token({self.type.name:<7}, lexema={lex:<21} linha={self.line}:{self.col}{extra})"


class LexError(Exception):
    pass


class LexerGrove:
    def __init__(self, source_code: str):
        self.src = source_code
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    def error(self, msg: str, col: int | None = None):
        raise LexError(f"💥 [Análise Léxica] linha {self.line}, coluna {col or self.col}: {msg}")

    def peek(self, offset: int = 1) -> str:
        return self.src[self.pos + offset] if self.pos + offset < len(self.src) else ""

    def advance(self, step: int = 1):
        self.pos += step
        self.col += step

    def tokenize(self) -> list[Token]:
        n = len(self.src)
        while self.pos < n:
            c = self.src[self.pos]

            # Espaços e quebras de linha
            if c == "\n":
                self.pos += 1
                self.line += 1
                self.col = 1
                continue
            if c.isspace():
                self.advance()
                continue

            # Comentário: # até o fim da linha
            if c == "#":
                while self.pos < n and self.src[self.pos] != "\n":
                    self.pos += 1
                continue

            start_col = self.col

            # Operadores e pontuação ("!=" antes de "!", senão vira "!" + "=")
            two = self.src[self.pos:self.pos + 2]
            if two in OPERATORS:
                self.tokens.append(Token(OPERATORS[two], two, self.line, start_col))
                self.advance(2)
                continue
            if c in OPERATORS:
                self.tokens.append(Token(OPERATORS[c], c, self.line, start_col))
                self.advance()
                continue

            # Números inteiros
            if c.isdigit():
                j = self.pos
                while j < n and self.src[j].isdigit():
                    j += 1
                texto = self.src[self.pos:j]
                self.tokens.append(Token(TokenType.NUMBER, texto, self.line, start_col, int(texto)))
                self.advance(j - self.pos)
                continue

            # Strings: "entre aspas", sem quebra de linha
            if c == '"':
                j = self.pos + 1
                while j < n and self.src[j] not in '"\n':
                    j += 1
                if j >= n or self.src[j] != '"':
                    self.error("string sem fechar (faltou a aspa)", start_col)
                bruto = self.src[self.pos:j + 1]
                self.tokens.append(Token(TokenType.STRING, bruto, self.line, start_col, bruto[1:-1]))
                self.advance(j + 1 - self.pos)
                continue

            # Identificadores e cheats
            if c.isalpha() or c == "_":
                j = self.pos
                while j < n and (self.src[j].isalnum() or self.src[j] == "_"):
                    j += 1
                palavra = self.src[self.pos:j]
                self.tokens.append(Token(WORDS.get(palavra, TokenType.IDENT), palavra, self.line, start_col))
                self.advance(j - self.pos)
                continue

            self.error(f"caractere fora do mapa: {c!r}")

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return self.tokens


# =====================================================================
# 2. NÓS DA AST (ÁRVORE DE SINTAXE ABSTRATA)
# =====================================================================


class No:
    """Nó da AST.

    `rotulo` é a linha impressa (atributo de classe ou property);
    `ramos()` devolve [(legenda ou None, filho)], onde filho é um No ou uma lista.
    """
    rotulo = "?"

    def ramos(self) -> list:
        return []

    def __str__(self):
        return arvore(self)


# ---- expressões ----
@dataclass
class Literal(No):
    value: object  # int | str | bool

    @property
    def rotulo(self):
        tipo = {bool: "BOOL", int: "NUMERO", str: "TEXTO"}[type(self.value)]
        return f"💎 LITERAL [{tipo}]: {self.value!r}"


@dataclass
class Var(No):
    name: str

    @property
    def rotulo(self):
        return f"🔑 IDENT: {self.name}"


@dataclass
class Unary(No):
    op: str        # "!" ou "-"
    operand: No

    @property
    def rotulo(self):
        return f"🔄 UNÁRIO ({self.op})"

    def ramos(self):
        return [(None, self.operand)]


@dataclass
class Binary(No):
    left: No
    op: str        # + - * / % == != < > <= >= && ||
    right: No

    @property
    def rotulo(self):
        return f"⚙️ BINÁRIO ({self.op})"

    def ramos(self):
        return [(None, self.left), (None, self.right)]


# ---- instruções ----
@dataclass
class VarDecl(No):
    name: str
    value: No

    @property
    def rotulo(self):
        return f"💵 HESOYAM (declara): {self.name}"

    def ramos(self):
        return [(None, self.value)]


@dataclass
class Assign(No):
    name: str
    value: No

    @property
    def rotulo(self):
        return f"📝 ATRIBUI (=): {self.name}"

    def ramos(self):
        return [(None, self.value)]


@dataclass
class Print(No):
    value: No
    rotulo = "📢 HELLOLADIES (imprime)"

    def ramos(self):
        return [(None, self.value)]


@dataclass
class Break(No):
    rotulo = "☠️ GOODBYECRUELWORLD (sai do laço)"


@dataclass
class Block(No):
    stmts: list
    rotulo = "🧱 BLOCO { }"

    def ramos(self):
        return [(None, self.stmts)]


@dataclass
class If(No):
    cond: No
    then: Block
    orelse: No | None = None  # Block, If (senão-se) ou None
    rotulo = "🔥 TURNUPTHEHEAT (se)"

    def ramos(self):
        r = [("❓ Condição:", self.cond), ("✅ Então:", self.then)]
        if self.orelse is not None:
            r.append(("🌧️ Senão:", self.orelse))
        return r


@dataclass
class While(No):
    cond: No
    body: Block
    rotulo = "🦘 KANGAROO (enquanto)"

    def ramos(self):
        return [("❓ Condição:", self.cond), ("🔁 Corpo:", self.body)]


@dataclass
class Program(No):
    body: list
    rotulo = "🌴 PROGRAMA GROVE"

    def ramos(self):
        return [(None, self.body)]


def _ramo(indent: str, ultimo: bool) -> tuple[str, str]:
    """(prefixo da linha deste nó, indentação dos filhos dele)."""
    return indent + ("└── " if ultimo else "├── "), indent + ("    " if ultimo else "│   ")


def _desenha(filho, indent: str, ultimo: bool) -> str:
    if isinstance(filho, list):
        return "".join(arvore(n, indent, ultimo and i == len(filho) - 1) for i, n in enumerate(filho))
    return arvore(filho, indent, ultimo)


def arvore(no: No, indent: str = "", ultimo: bool = True) -> str:
    """Desenha a AST com os galhos ├── └── │."""
    prefixo, dentro = _ramo(indent, ultimo)
    res = f"{prefixo}{no.rotulo}\n"
    ramos = no.ramos()
    for i, (legenda, filho) in enumerate(ramos):
        ult = i == len(ramos) - 1
        if legenda is None:
            res += _desenha(filho, dentro, ult)
        else:
            prefixo_legenda, sob_legenda = _ramo(dentro, ult)
            res += f"{prefixo_legenda}{legenda}\n" + _desenha(filho, sob_legenda, True)
    return res


# =====================================================================
# 3. ANALISADOR SINTÁTICO (PARSER)
# =====================================================================


class ParseError(Exception):
    pass


NOMES = {  # como descrever cada token numa mensagem de erro
    TokenType.SEMI: "; (fim de instrução)", TokenType.LBRACE: "{ (abre bloco)",
    TokenType.RBRACE: "} (fecha bloco)", TokenType.LPAREN: "(", TokenType.RPAREN: ")",
    TokenType.IDENT: "identificador", TokenType.ASSIGN: "=",
}
T = TokenType


class ParserGrove:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # ---- utilitários ----
    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type is not T.EOF:
            self.pos += 1
        return tok

    def check(self, *types) -> bool:
        return self.peek().type in types

    def match(self, *types) -> Token | None:
        return self.advance() if self.check(*types) else None

    def expect(self, tt: TokenType) -> Token:
        if self.check(tt):
            return self.advance()
        self.error(f"esperado {NOMES.get(tt, tt.name)}", self.peek())

    def error(self, msg: str, tok: Token):
        achado = "fim do arquivo" if tok.type is T.EOF else repr(tok.lexeme)
        raise ParseError(f"💥 [Análise Sintática] linha {tok.line}, coluna {tok.col}: {msg}, encontrado {achado}")

    # ---- regras da gramática (uma por método) ----
    def program(self) -> Program:
        body = []
        while not self.check(T.EOF):
            body.append(self.declaration())
        return Program(body)

    def declaration(self) -> No:
        if self.match(T.VAR):
            name = self.expect(T.IDENT).lexeme
            self.expect(T.ASSIGN)
            value = self.expression()
            self.expect(T.SEMI)
            return VarDecl(name, value)
        return self.statement()

    def statement(self) -> No:
        if self.match(T.IF):
            return self.if_stmt()
        if self.match(T.WHILE):
            self.expect(T.LPAREN)
            cond = self.expression()
            self.expect(T.RPAREN)
            return While(cond, self.block())
        if self.match(T.PRINT):
            value = self.expression()
            self.expect(T.SEMI)
            return Print(value)
        if self.match(T.BREAK):
            self.expect(T.SEMI)
            return Break()
        if self.check(T.LBRACE):
            return self.block()
        name = self.expect(T.IDENT).lexeme
        self.expect(T.ASSIGN)
        value = self.expression()
        self.expect(T.SEMI)
        return Assign(name, value)

    def if_stmt(self) -> If:
        self.expect(T.LPAREN)
        cond = self.expression()
        self.expect(T.RPAREN)
        then = self.block()
        orelse = None
        if self.match(T.ELIF):                 # BRINGITON: açúcar para senão-se
            orelse = self.if_stmt()
        elif self.match(T.ELSE):
            orelse = self.if_stmt() if self.match(T.IF) else self.block()
        return If(cond, then, orelse)

    def block(self) -> Block:
        self.expect(T.LBRACE)
        stmts = []
        while not self.check(T.RBRACE, T.EOF):
            stmts.append(self.declaration())
        self.expect(T.RBRACE)
        return Block(stmts)

    # ---- expressões, da menor para a maior precedência ----
    def expression(self) -> No:
        return self.binary(self.logic_and, T.OR)

    def logic_and(self) -> No:
        return self.binary(self.equality, T.AND)

    def equality(self) -> No:
        return self.binary(self.comparison, T.EQ, T.NE)

    def comparison(self) -> No:
        return self.binary(self.term, T.LT, T.GT, T.LE, T.GE)

    def term(self) -> No:
        return self.binary(self.factor, T.PLUS, T.MINUS)

    def factor(self) -> No:
        return self.binary(self.unary, T.STAR, T.SLASH, T.MOD)

    def binary(self, operand, *ops) -> No:
        """Regra genérica `operand { op operand }`, associativa à esquerda."""
        left = operand()
        while (op := self.match(*ops)):
            left = Binary(left, op.lexeme, operand())
        return left

    def unary(self) -> No:
        if (op := self.match(T.NOT, T.MINUS)):
            return Unary(op.lexeme, self.unary())
        return self.primary()

    def primary(self) -> No:
        tok = self.advance()
        if tok.type in (T.NUMBER, T.STRING):
            return Literal(tok.value)
        if tok.type is T.TRUE:
            return Literal(True)
        if tok.type is T.FALSE:
            return Literal(False)
        if tok.type is T.IDENT:
            return Var(tok.lexeme)
        if tok.type is T.LPAREN:
            expr = self.expression()
            self.expect(T.RPAREN)
            return expr
        self.error("esperado expressão", tok)


def analisar(src: str) -> Program:
    """Atalho: texto-fonte → AST (léxico + sintático)."""
    return ParserGrove(LexerGrove(src).tokenize()).program()


if __name__ == "__main__":
    # Autoteste: quebra alto se léxico, precedência ou erros pararem de funcionar.
    fonte = 'HESOYAM x = 2; KANGAROO (x < 10) { x = x * 2; HELLOLADIES x; }'
    toks = LexerGrove(fonte).tokenize()
    assert [t.type for t in toks[:4]] == [T.VAR, T.IDENT, T.ASSIGN, T.NUMBER]
    assert toks[-1].type is T.EOF

    ast = analisar(fonte)
    assert isinstance(ast.body[1], While) and isinstance(ast.body[1].body.stmts[0], Assign)

    expr = analisar("HELLOLADIES 1 + 2 * 3;").body[0].value  # vira 1 + (2 * 3)
    assert expr.op == "+" and expr.right.op == "*", "precedência quebrada"

    try:
        analisar("HESOYAM x = 1")  # faltou ';'
    except ParseError as e:
        assert "linha 1" in str(e)
    else:
        raise AssertionError("erro de ';' ausente não foi detectado")

    print(f"✅ autoteste ok: {len(toks)} tokens, {len(ast.body)} instruções no topo")
