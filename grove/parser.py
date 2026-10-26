"""Análise sintática por descida recursiva: lista de Token → AST.

Gramática em docs/gramatica.md. Cada método corresponde a uma regra.
"""
from .ast import Assign, Binary, Block, Break, If, Literal, Print, Program, Unary, Var, VarDecl, While
from .tokens import Token, TokenType as T


class ParseError(Exception):
    pass


def at(node, tok: Token):
    """Grava no nó a posição do token; a análise semântica usa nas mensagens."""
    node.line, node.col = tok.line, tok.col
    return node


NOMES = {  # como descrever cada token numa mensagem de erro
    T.SEMI: "; (fim de instrução)", T.LBRACE: "{ (abre bloco)", T.RBRACE: "} (fecha bloco)",
    T.LPAREN: "(", T.RPAREN: ")", T.IDENT: "identificador", T.ASSIGN: "=",
}


class Parser:
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

    def expect(self, tt: T) -> Token:
        if self.check(tt):
            return self.advance()
        tok = self.peek()
        achado = "fim do arquivo" if tok.type is T.EOF else repr(tok.lexeme)
        raise ParseError(
            f"linha {tok.line}, coluna {tok.col}: esperado {NOMES.get(tt, tt.name)}, encontrado {achado}"
        )

    # ---- regras ----
    def program(self) -> Program:
        body = []
        while not self.check(T.EOF):
            body.append(self.declaration())
        return Program(body)

    def declaration(self):
        if self.match(T.VAR):
            name = self.expect(T.IDENT)
            self.expect(T.ASSIGN)
            value = self.expression()
            self.expect(T.SEMI)
            return at(VarDecl(name.lexeme, value), name)
        return self.statement()

    def statement(self):
        if (kw := self.match(T.IF)):
            return self.if_stmt(kw)
        if (kw := self.match(T.WHILE)):
            self.expect(T.LPAREN)
            cond = self.expression()
            self.expect(T.RPAREN)
            return at(While(cond, self.block()), kw)
        if (kw := self.match(T.PRINT)):
            value = self.expression()
            self.expect(T.SEMI)
            return at(Print(value), kw)
        if (kw := self.match(T.BREAK)):
            self.expect(T.SEMI)
            return at(Break(), kw)
        if self.check(T.LBRACE):
            return self.block()
        name = self.expect(T.IDENT)
        self.expect(T.ASSIGN)
        value = self.expression()
        self.expect(T.SEMI)
        return at(Assign(name.lexeme, value), name)

    def if_stmt(self, kw: Token) -> If:
        self.expect(T.LPAREN)
        cond = self.expression()
        self.expect(T.RPAREN)
        then = self.block()
        orelse = None
        if (elif_ := self.match(T.ELIF)):
            orelse = self.if_stmt(elif_)
        elif self.match(T.ELSE):
            if_ = self.match(T.IF)
            orelse = self.if_stmt(if_) if if_ else self.block()
        return at(If(cond, then, orelse), kw)

    def block(self) -> Block:
        brace = self.expect(T.LBRACE)
        stmts = []
        while not self.check(T.RBRACE, T.EOF):
            stmts.append(self.declaration())
        self.expect(T.RBRACE)
        return at(Block(stmts), brace)

    # ---- expressões, da menor para a maior precedência ----
    def expression(self):
        return self.binary(self.logic_and, T.OR)

    def logic_and(self):
        return self.binary(self.equality, T.AND)

    def equality(self):
        return self.binary(self.comparison, T.EQ, T.NE)

    def comparison(self):
        return self.binary(self.term, T.LT, T.GT, T.LE, T.GE)

    def term(self):
        return self.binary(self.factor, T.PLUS, T.MINUS)

    def factor(self):
        return self.binary(self.unary, T.STAR, T.SLASH, T.MOD)

    def binary(self, operand, *ops):
        """Regra genérica `operand { op operand }`, associativa à esquerda."""
        left = operand()
        while (op := self.match(*ops)):
            left = at(Binary(left, op.lexeme, operand()), op)
        return left

    def unary(self):
        if (op := self.match(T.NOT, T.MINUS)):
            return at(Unary(op.lexeme, self.unary()), op)
        return self.primary()

    def primary(self):
        tok = self.advance()
        if tok.type is T.NUMBER or tok.type is T.STRING:
            return at(Literal(tok.value), tok)
        if tok.type is T.TRUE:
            return at(Literal(True), tok)
        if tok.type is T.FALSE:
            return at(Literal(False), tok)
        if tok.type is T.IDENT:
            return at(Var(tok.lexeme), tok)
        if tok.type is T.LPAREN:
            expr = self.expression()
            self.expect(T.RPAREN)
            return expr
        achado = "fim do arquivo" if tok.type is T.EOF else repr(tok.lexeme)
        raise ParseError(f"linha {tok.line}, coluna {tok.col}: esperado expressão, encontrado {achado}")


def parse(tokens: list[Token]) -> Program:
    return Parser(tokens).program()
