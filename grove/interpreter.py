"""Back-end: interpretador que percorre a AST e executa.

Semântica em docs/interpretador.md. Um método `exec_<Nó>` por tipo de nó.
"""
from .ast import Block, If, Node, Program


class RuntimeError_(Exception):
    """Erro semântico ou de execução (nome com _ para não sombrear o builtin)."""


class BreakSignal(Exception):
    """Sinaliza GOODBYECRUELWORLD; capturado pelo laço mais interno."""


class Environment:
    """Escopo léxico: um dicionário por bloco, encadeado ao escopo pai."""

    def __init__(self, parent=None):
        self.vars: dict[str, object] = {}
        self.parent = parent

    def declare(self, name, value):
        if name in self.vars:
            raise RuntimeError_(f"variável '{name}' já declarada neste escopo")
        self.vars[name] = value

    def lookup(self, name) -> "Environment":
        env = self
        while env is not None:
            if name in env.vars:
                return env
            env = env.parent
        raise RuntimeError_(f"variável '{name}' não declarada")

    def get(self, name):
        return self.lookup(name).vars[name]

    def assign(self, name, value):
        self.lookup(name).vars[name] = value


def formatar(value) -> str:
    if value is True:
        return "FULLCLIP"
    if value is False:
        return "GHOSTTOWN"
    return str(value)


def _bool(value, contexto):
    if not isinstance(value, bool):
        raise RuntimeError_(f"{contexto} exige booleano, recebeu {formatar(value)!r}")
    return value


def _int(a, b, op):
    # bool é subclasse de int em Python; aqui bool não é número
    if type(a) is not int or type(b) is not int:
        raise RuntimeError_(f"tipos incompatíveis para '{op}': {formatar(a)!r} e {formatar(b)!r}")


class Interpreter:
    def __init__(self, out=print):
        self.out = out
        self.env = Environment()
        self.loops = 0

    # ---- instruções ----
    def exec(self, node: Node):
        return getattr(self, f"exec_{type(node).__name__}")(node)

    def exec_Program(self, node: Program):
        for stmt in node.body:
            self.exec(stmt)

    def exec_Block(self, node: Block):
        self.env = Environment(self.env)
        try:
            for stmt in node.stmts:
                self.exec(stmt)
        finally:
            self.env = self.env.parent

    def exec_VarDecl(self, node):
        self.env.declare(node.name, self.eval(node.value))

    def exec_Assign(self, node):
        self.env.assign(node.name, self.eval(node.value))

    def exec_Print(self, node):
        self.out(formatar(self.eval(node.value)))

    def exec_If(self, node: If):
        if _bool(self.eval(node.cond), "condição do TURNUPTHEHEAT"):
            self.exec(node.then)
        elif node.orelse is not None:
            self.exec(node.orelse)

    def exec_While(self, node):
        self.loops += 1
        try:
            while _bool(self.eval(node.cond), "condição do KANGAROO"):
                self.exec(node.body)
        except BreakSignal:
            pass
        finally:
            self.loops -= 1

    def exec_Break(self, node):
        if self.loops == 0:
            raise RuntimeError_("GOODBYECRUELWORLD fora de laço")
        raise BreakSignal()

    # ---- expressões ----
    def eval(self, node: Node):
        return getattr(self, f"eval_{type(node).__name__}")(node)

    def eval_Literal(self, node):
        return node.value

    def eval_Var(self, node):
        return self.env.get(node.name)

    def eval_Unary(self, node):
        v = self.eval(node.operand)
        if node.op == "!":
            return not _bool(v, "!")
        _int(v, 0, "-")
        return -v

    def eval_Binary(self, node):
        op = node.op
        # curto-circuito: só avalia a direita se precisar
        if op == "&&":
            return _bool(self.eval(node.left), "&&") and _bool(self.eval(node.right), "&&")
        if op == "||":
            return _bool(self.eval(node.left), "||") or _bool(self.eval(node.right), "||")

        a, b = self.eval(node.left), self.eval(node.right)
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == "+" and isinstance(a, str) and isinstance(b, str):
            return a + b
        _int(a, b, op)
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op in ("/", "%"):
            if b == 0:
                raise RuntimeError_("divisão por zero")
            return a // b if op == "/" else a % b
        return {"<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[op]


def run(program: Program, out=print):
    Interpreter(out).exec(program)
