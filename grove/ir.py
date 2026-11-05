"""Código intermediário: AST anotada → código de três endereços (TAC).

Esquema de tradução em docs/codigo-intermediario.md. Um método `gen_<Nó>` por
instrução, `expr` para expressões. Cada instrução é uma quádrupla
(op, arg1, arg2, result). Variáveis usam o nome único da tabela de símbolos,
porque a TAC não tem escopo de bloco.
"""
import operator
from dataclasses import dataclass

from .ast import Binary, If, Input, Literal, Node, Program, Unary, Var
from .interpreter import RuntimeError_, formatar
from .semantic import Analise


@dataclass(frozen=True)
class Const:
    value: object  # int | str | bool

    def __str__(self):
        return f'"{self.value}"' if isinstance(self.value, str) else formatar(self.value)


@dataclass
class Quad:
    op: str               # "=", "+", …, "!", "neg", "read", "print", "goto", "if", "iffalse", "label"
    arg1: object = None   # nome (variável ou temporário) ou Const
    arg2: object = None
    result: str | None = None  # destino; nos desvios e em "label", o rótulo

    def __str__(self):
        a, b, r = self.arg1, self.arg2, self.result
        match self.op:
            case "label":
                return f"{r}:"
            case "goto":
                return f"goto {r}"
            case "if":
                return f"if {a} goto {r}"
            case "iffalse":
                return f"ifFalse {a} goto {r}"
            case "print":
                return f"print {a}"
            case "=":
                return f"{r} = {a}"
            case "!":
                return f"{r} = !{a}"
            case "neg":
                return f"{r} = -{a}"
            case "read":
                return f"{r} = read"
        return f"{r} = {a} {self.op} {b}"


class Generator:
    def __init__(self, analise: Analise):
        self.code: list[Quad] = []
        self.variaveis = {s.unico for s in analise.simbolos}  # temporário não pode ter nome de variável
        self.temps = self.labels = 0
        self.loops: list[str] = []  # rótulo de saída de cada laço aberto, para o break

    def emit(self, op, arg1=None, arg2=None, result=None):
        self.code.append(Quad(op, arg1, arg2, result))

    def temp(self) -> str:
        self.temps += 1
        while f"t{self.temps}" in self.variaveis:
            self.temps += 1
        return f"t{self.temps}"

    def label(self) -> str:
        self.labels += 1
        return f"L{self.labels}"

    # ---- instruções ----
    def gen(self, node: Node):
        getattr(self, f"gen_{type(node).__name__}")(node)

    def gen_Program(self, node: Program):
        for stmt in node.body:
            self.gen(stmt)

    def gen_Block(self, node):
        for stmt in node.stmts:
            self.gen(stmt)

    def gen_VarDecl(self, node):
        self.expr(node.value, node.simbolo.unico)

    gen_Assign = gen_VarDecl

    def gen_Print(self, node):
        self.emit("print", self.expr(node.value))

    def gen_If(self, node: If, fim=None):
        """else-if encadeado reaproveita o rótulo de fim do primeiro TURNUPTHEHEAT."""
        proprio = fim is None
        fim = fim or self.label()
        senao = self.label() if node.orelse is not None else fim
        self.emit("iffalse", self.expr(node.cond), result=senao)
        self.gen(node.then)
        if node.orelse is not None:
            self.emit("goto", result=fim)
            self.emit("label", result=senao)
            if isinstance(node.orelse, If):
                self.gen_If(node.orelse, fim)
            else:
                self.gen(node.orelse)
        if proprio:
            self.emit("label", result=fim)

    def gen_While(self, node):
        inicio, fim = self.label(), self.label()
        self.emit("label", result=inicio)
        self.emit("iffalse", self.expr(node.cond), result=fim)
        self.loops.append(fim)
        self.gen(node.body)
        self.loops.pop()
        self.emit("goto", result=inicio)
        self.emit("label", result=fim)

    def gen_Break(self, node):
        self.emit("goto", result=self.loops[-1])

    # ---- expressões ----
    def expr(self, node, dest=None):
        """Gera o código da expressão e devolve onde está o valor (nome ou Const).

        Com `dest`, a última instrução já escreve lá: `r = r * n` em vez de
        `t1 = r * n; r = t1`.
        """
        if isinstance(node, (Literal, Var)):
            valor = Const(node.value) if isinstance(node, Literal) else node.simbolo.unico
            if dest is None:
                return valor
            self.emit("=", valor, result=dest)
            return dest
        if isinstance(node, Input):
            dest = dest or self.temp()
            self.emit("read", result=dest)  # efeito colateral: consome uma linha da entrada
            return dest
        if isinstance(node, Unary):
            a = self.expr(node.operand)
            dest = dest or self.temp()
            self.emit("!" if node.op == "!" else "neg", a, result=dest)
            return dest
        if node.op in ("&&", "||"):
            return self.curto_circuito(node, dest)
        a, b = self.expr(node.left), self.expr(node.right)
        dest = dest or self.temp()
        self.emit(node.op, a, b, dest)
        return dest

    def curto_circuito(self, node: Binary, dest):
        """a && b: só avalia b se a for verdadeiro (|| ao contrário).

        Usa um temporário mesmo com `dest`: escrever em dest antes de avaliar b
        quebraria `x = y && x`.
        """
        t, fim = self.temp(), self.label()
        self.expr(node.left, t)
        self.emit("iffalse" if node.op == "&&" else "if", t, result=fim)
        self.expr(node.right, t)
        self.emit("label", result=fim)
        if dest is None:
            return t
        self.emit("=", t, result=dest)
        return dest


def _renumerar_rotulos(code: list[Quad]) -> list[Quad]:
    """Rótulos numerados na ordem em que aparecem na listagem (L1, L2, …)."""
    novo = {}
    for q in code:
        if q.op == "label":
            novo[q.result] = f"L{len(novo) + 1}"
    for q in code:
        if q.op in ("label", "goto", "if", "iffalse"):
            q.result = novo[q.result]
    return code


def emit_ir(program: Program, analise: Analise) -> list[Quad]:
    """Traduz a AST já conferida por check() para TAC."""
    g = Generator(analise)
    g.gen(program)
    return _renumerar_rotulos(g.code)


def format_ir(code: list[Quad]) -> str:
    """Listagem numerada (saída de --ir): rótulos na margem, instruções recuadas."""
    return "\n".join(f"{i:>3}  {'' if q.op == 'label' else '    '}{q}" for i, q in enumerate(code, 1))


def _divisao(op):
    def f(a, b):
        if b == 0:
            raise RuntimeError_("divisão por zero")
        return op(a, b)
    return f


OPERACOES = {
    "+": operator.add, "-": operator.sub, "*": operator.mul,
    "/": _divisao(operator.floordiv), "%": _divisao(operator.mod),
    "==": operator.eq, "!=": operator.ne,
    "<": operator.lt, ">": operator.gt, "<=": operator.le, ">=": operator.ge,
}


def execute(code: list[Quad], out=print, entrada=input):
    """Executa a TAC: confere a tradução contra o interpretador nos testes."""
    alvos = {q.result: i for i, q in enumerate(code) if q.op == "label"}
    memoria: dict[str, object] = {}

    def valor(x):
        return x.value if isinstance(x, Const) else memoria[x]

    pc = 0
    while pc < len(code):
        q = code[pc]
        pc += 1
        match q.op:
            case "label":
                pass
            case "goto":
                pc = alvos[q.result]
            case "if" | "iffalse":
                if bool(valor(q.arg1)) == (q.op == "if"):
                    pc = alvos[q.result]
            case "print":
                out(formatar(valor(q.arg1)))
            case "=":
                memoria[q.result] = valor(q.arg1)
            case "!":
                memoria[q.result] = not valor(q.arg1)
            case "neg":
                memoria[q.result] = -valor(q.arg1)
            case "read":
                try:
                    linha = entrada()
                except EOFError:
                    raise RuntimeError_("CJPHONEHOME: a entrada acabou") from None
                try:
                    memoria[q.result] = int(linha)
                except ValueError:
                    raise RuntimeError_(f"CJPHONEHOME esperava um número inteiro, recebeu {linha!r}") from None
            case op:
                memoria[q.result] = OPERACOES[op](valor(q.arg1), valor(q.arg2))
