"""Nós da árvore sintática abstrata (AST)."""
from dataclasses import dataclass, fields, is_dataclass


@dataclass
class Node:
    pass


# ---- expressões ----
@dataclass
class Literal(Node):
    value: object  # int | str | bool


@dataclass
class Var(Node):
    name: str


@dataclass
class Unary(Node):
    op: str        # "!" ou "-"
    operand: Node


@dataclass
class Binary(Node):
    left: Node
    op: str        # "+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||"
    right: Node


# ---- instruções ----
@dataclass
class VarDecl(Node):
    name: str
    value: Node


@dataclass
class Assign(Node):
    name: str
    value: Node


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
        v = getattr(node, f.name)
        if isinstance(v, list) or is_dataclass(v):
            lines.append(f"{pad}  {f.name}:")
            lines.append(dump(v, indent + 2))
        else:
            lines.append(f"{pad}  {f.name}: {v!r}")
    return "\n".join(lines)
