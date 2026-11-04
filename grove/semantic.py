"""Análise semântica: confere a AST antes de executar ou gerar código.

Regras em docs/semantica.md. Um método `visit_<Nó>` por instrução e `tipo_<Nó>`
por expressão, como no interpretador. Não para no primeiro erro: junta todos e
levanta SemanticError no fim. Anota a AST: cada expressão ganha `tipo`; cada
VarDecl, Assign e Var ganha `simbolo`, a entrada da tabela de símbolos que usa.
"""
from dataclasses import dataclass, fields

from .ast import Assign, Literal, Node, Program, Var, VarDecl
from .sugestao import cheat_parecido, nome_parecido

INTEIRO, STRING, BOOLEANO = "inteiro", "string", "booleano"
ERRO = "erro"  # tipo de uma expressão que já deu erro: aceita tudo, para não gerar erro em cascata

# operador → (tipos aceitos, iguais dos dois lados; tipo do resultado, None = o dos operandos)
REGRAS = {
    "+": ({INTEIRO, STRING}, None),
    **{op: ({INTEIRO}, INTEIRO) for op in ("-", "*", "/", "%")},
    **{op: ({INTEIRO}, BOOLEANO) for op in ("<", ">", "<=", ">=")},
    **{op: ({INTEIRO, STRING, BOOLEANO}, BOOLEANO) for op in ("==", "!=")},
    **{op: ({BOOLEANO}, BOOLEANO) for op in ("&&", "||")},
}


@dataclass
class Simbolo:
    nome: str
    tipo: str
    escopo: int    # profundidade do bloco: 0 = global
    linha: int
    coluna: int
    unico: str     # nome sem colisão entre escopos, usado pela TAC e pelo Python gerado
    lido: bool = False


@dataclass
class Diagnostico:
    linha: int
    coluna: int
    mensagem: str

    def __str__(self):
        return f"linha {self.linha}, coluna {self.coluna}: {self.mensagem}"


class SemanticError(Exception):
    """Todos os erros semânticos do programa, em ordem de posição."""

    def __init__(self, erros: list[Diagnostico]):
        super().__init__("\n".join(map(str, erros)))
        self.erros = erros


@dataclass
class Analise:
    simbolos: list[Simbolo]   # na ordem de declaração
    avisos: list[Diagnostico]


def _nomes(node):
    """Todos os identificadores que aparecem no programa."""
    if isinstance(node, list):
        for n in node:
            yield from _nomes(n)
    elif isinstance(node, Node):
        if isinstance(node, (Var, VarDecl, Assign)):
            yield node.name
        for f in fields(node):
            if f.repr:
                yield from _nomes(getattr(node, f.name))


def _posicao(d: Diagnostico):
    return d.linha, d.coluna


class Checker:
    def __init__(self, program: Program):
        self.escopos: list[dict[str, Simbolo]] = []
        self.simbolos: list[Simbolo] = []
        self.erros: list[Diagnostico] = []
        self.avisos: list[Diagnostico] = []
        self.loops = 0
        self.do_fonte = set(_nomes(program))  # um nome único novo não pode colidir com eles
        self.unicos: set[str] = set()

    def erro(self, node, msg):
        self.erros.append(Diagnostico(node.line, node.col, msg))

    def aviso(self, node, msg):
        self.avisos.append(Diagnostico(node.line, node.col, msg))

    # ---- escopo ----
    def abrir(self):
        self.escopos.append({})

    def fechar(self):
        for s in self.escopos.pop().values():
            if not s.lido:
                self.avisos.append(Diagnostico(s.linha, s.coluna, f"variável '{s.nome}' declarada e nunca lida"))

    def lookup(self, node, name) -> Simbolo | None:
        for escopo in reversed(self.escopos):
            if name in escopo:
                return escopo[name]
        visiveis = {n for escopo in self.escopos for n in escopo}
        if (cheat := cheat_parecido(name)):
            dica = f"; você quis dizer o cheat {cheat}?"
        elif (outro := nome_parecido(name, visiveis)):
            dica = f"; você quis dizer '{outro}'?"
        else:
            dica = ""
        self.erro(node, f"variável '{name}' não declarada{dica}")
        return None

    def unico(self, nome):
        """A primeira declaração de um nome fica com ele; as outras viram nome_1, nome_2, …"""
        candidato, n = nome, 0
        while candidato in self.unicos or (n > 0 and candidato in self.do_fonte):
            n += 1
            candidato = f"{nome}_{n}"
        self.unicos.add(candidato)
        return candidato

    # ---- instruções ----
    def visit(self, node: Node):
        return getattr(self, f"visit_{type(node).__name__}")(node)

    def visit_Program(self, node: Program):
        self.abrir()
        for stmt in node.body:
            self.visit(stmt)
        self.fechar()

    def visit_Block(self, node):
        self.abrir()
        for stmt in node.stmts:
            self.visit(stmt)
        self.fechar()

    def visit_VarDecl(self, node):
        tipo = self.tipo(node.value)  # antes de declarar: em HESOYAM x = x; o x da direita é o de fora
        escopo = self.escopos[-1]
        if node.name in escopo:
            primeira = escopo[node.name]
            self.erro(node, f"variável '{node.name}' já declarada neste escopo (linha {primeira.linha})")
            node.simbolo = primeira
            return
        sim = Simbolo(node.name, tipo, len(self.escopos) - 1, node.line, node.col, self.unico(node.name))
        escopo[node.name] = sim
        self.simbolos.append(sim)
        node.simbolo = sim

    def visit_Assign(self, node):
        tipo = self.tipo(node.value)
        sim = self.lookup(node, node.name)
        if sim is None:
            return
        node.simbolo = sim
        if ERRO not in (tipo, sim.tipo) and tipo != sim.tipo:
            self.erro(node, f"'{node.name}' é {sim.tipo}, não pode receber {tipo}")

    def visit_Print(self, node):
        self.tipo(node.value)

    def visit_If(self, node):
        self.condicao(node, "TURNUPTHEHEAT")
        self.visit(node.then)
        if node.orelse is not None:
            self.visit(node.orelse)

    def visit_While(self, node):
        self.condicao(node, "KANGAROO")
        self.loops += 1
        self.visit(node.body)
        self.loops -= 1

    def visit_Break(self, node):
        if self.loops == 0:
            self.erro(node, "GOODBYECRUELWORLD fora de laço")

    def condicao(self, node, cheat):
        tipo = self.tipo(node.cond)
        if tipo not in (BOOLEANO, ERRO):
            self.erro(node, f"condição do {cheat} exige booleano, recebeu {tipo}")

    # ---- expressões: devolvem o tipo e o gravam no nó ----
    def tipo(self, node) -> str:
        node.tipo = getattr(self, f"tipo_{type(node).__name__}")(node)
        return node.tipo

    def tipo_Literal(self, node):
        if isinstance(node.value, bool):  # antes de int: bool é subclasse de int em Python
            return BOOLEANO
        return INTEIRO if isinstance(node.value, int) else STRING

    def tipo_Var(self, node):
        sim = self.lookup(node, node.name)
        if sim is None:
            return ERRO
        sim.lido = True
        node.simbolo = sim
        return sim.tipo

    def tipo_Unary(self, node):
        tipo = self.tipo(node.operand)
        esperado = BOOLEANO if node.op == "!" else INTEIRO
        if tipo not in (esperado, ERRO):
            self.erro(node, f"'{node.op}' exige {esperado}, recebeu {tipo}")
        return esperado

    def tipo_Binary(self, node):
        a, b = self.tipo(node.left), self.tipo(node.right)
        aceitos, resultado = REGRAS[node.op]
        if ERRO in (a, b):
            return resultado or ERRO
        if a != b:
            self.erro(node, f"tipos incompatíveis para '{node.op}': {a} e {b}")
            return resultado or ERRO
        if a not in aceitos:
            self.erro(node, f"'{node.op}' não se aplica a {a}")
            return resultado or ERRO
        if node.op in ("/", "%") and isinstance(node.right, Literal) and node.right.value == 0:
            self.aviso(node, "divisão por zero")
        return resultado or a


def check(program: Program) -> Analise:
    """Confere e anota a AST. Levanta SemanticError com todos os erros encontrados."""
    c = Checker(program)
    c.visit(program)
    if c.erros:
        raise SemanticError(sorted(c.erros, key=_posicao))
    return Analise(c.simbolos, sorted(c.avisos, key=_posicao))


def format_symbols(analise: Analise) -> str:
    """Tabela de símbolos, uma linha por declaração (saída de --simbolos)."""
    linhas = ["NOME\tTIPO\tESCOPO\tLINHA:COL\tÚNICO\tLIDA"]
    for s in analise.simbolos:
        linhas.append(f"{s.nome}\t{s.tipo}\t{s.escopo}\t{s.linha}:{s.coluna}\t{s.unico}\t{'sim' if s.lido else 'não'}")
    return "\n".join(linhas)
