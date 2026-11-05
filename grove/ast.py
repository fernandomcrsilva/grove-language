"""Nós da árvore sintática abstrata (AST)."""
from dataclasses import dataclass, field, fields, is_dataclass


def anotacao(default=None):
    """Campo preenchido depois do parse: fica fora do ==, do repr e do dump."""
    return field(default=default, kw_only=True, compare=False, repr=False)


@dataclass
class Node:
    line: int = anotacao(0)  # posição no fonte, gravada pelo parser
    col: int = anotacao(0)


# ---- expressões ----
@dataclass
class Expr(Node):
    tipo: str | None = anotacao()  # "inteiro" | "string" | "booleano", gravado pela análise semântica


@dataclass
class Literal(Expr):
    value: object  # int | str | bool


@dataclass
class Var(Expr):
    name: str
    simbolo: object = anotacao()  # Simbolo da tabela, gravado pela análise semântica


@dataclass
class Input(Expr):
    """CJPHONEHOME: lê um inteiro da entrada. Sem campos: o valor vem de fora."""


@dataclass
class Unary(Expr):
    op: str        # "!" ou "-"
    operand: Node


@dataclass
class Binary(Expr):
    left: Node
    op: str        # "+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||"
    right: Node


# ---- instruções ----
@dataclass
class VarDecl(Node):
    name: str
    value: Node
    simbolo: object = anotacao()


@dataclass
class Assign(Node):
    name: str
    value: Node
    simbolo: object = anotacao()


@dataclass
class Print(Node):
    value: Node


@dataclass
class Break(Node):
    pass


@dataclass
class Block(Node):
    stmts: list


@dataclass
class If(Node):
    cond: Node
    then: Block
    orelse: Node | None = None  # Block, If (else-if) ou None


@dataclass
class While(Node):
    cond: Node
    body: Block


@dataclass
class Program(Node):
    body: list


def dump(node, indent: int = 0) -> str:
    """Imprime a AST indentada, um campo por linha."""
    pad = "  " * indent
    if isinstance(node, list):
        if not node:
            return f"{pad}[]"
        return "\n".join(dump(n, indent) for n in node)
    if not is_dataclass(node):
        return f"{pad}{node!r}"
    lines = [f"{pad}{type(node).__name__}"]
    for f in fields(node):
        if not f.repr:  # posição e anotações não fazem parte da árvore
            continue
        v = getattr(node, f.name)
        if isinstance(v, list) or is_dataclass(v):
            lines.append(f"{pad}  {f.name}:")
            lines.append(dump(v, indent + 2))
        else:
            lines.append(f"{pad}  {f.name}: {v!r}")
    return "\n".join(lines)
