"""Back-end: AST anotada → código Python ou MicroPython (ESP32).

Tradução em docs/geracao-de-codigo.md. Parte da AST, não da TAC: Python não tem
goto, e código estruturado sai legível. Um método `gen_<Nó>` por instrução,
`expr` para expressões, que devolve o texto e a precedência dele em Python
para pôr só os parênteses necessários.
"""
import keyword

from .ast import If, Literal, Node, Program, Unary, Var
from .semantic import BOOLEANO, INTEIRO, Analise

PY_OP = {"&&": "and", "||": "or", "/": "//"}  # os outros operadores são iguais em Python

# precedência em Python, da menor para a maior
COMPARACAO = 4
PRECEDENCIA = {
    "or": 1, "and": 2, "not": 3,
    **{op: COMPARACAO for op in ("==", "!=", "<", ">", "<=", ">=")},
    "+": 5, "-": 5, "*": 6, "//": 6, "%": 6,
    "neg": 7,
}
ATOMO = 8

# nomes que uma variável não pode ter no código gerado
RESERVADOS = set(keyword.kwlist) | {"print"}

# ESP32: a variável inteira `estrelas` comanda o LED, como o nível de procurado no jogo
ESTRELAS = "estrelas"
PRELUDIO_ESP32 = """\
from machine import Pin, Timer
import time

_led = Pin({pino}, Pin.OUT)
_timer = Timer(0)


def _procurado(n):
    # 0 estrelas: LED apagado; cada estrela a mais, pisca mais rápido
    _timer.deinit()
    _led.value(0)
    if n > 0:
        _timer.init(period=max(50, 600 // n), mode=Timer.PERIODIC,
                    callback=lambda t: _led.value(not _led.value()))
    time.sleep_ms(1500)  # tempo para ver cada nível

"""
RESERVADOS_ESP32 = RESERVADOS | {"Pin", "Timer", "time", "_led", "_timer", "_procurado"}


def tem_estrelas(analise: Analise) -> bool:
    return any(s.nome == ESTRELAS and s.tipo == INTEIRO for s in analise.simbolos)


def _nomes_python(analise: Analise, reservados: set[str]) -> dict[str, str]:
    """nome único → nome em Python; quem colide com um reservado ganha _ no fim."""
    usados = {s.unico for s in analise.simbolos}
    mapa = {}
    for s in analise.simbolos:
        nome = s.unico
        while nome in reservados or (nome != s.unico and nome in usados):
            nome += "_"
        usados.add(nome)
        mapa[s.unico] = nome
    return mapa


class PythonGen:
    def __init__(self, analise: Analise, esp32=False):
        self.nomes = _nomes_python(analise, RESERVADOS_ESP32 if esp32 else RESERVADOS)
        self.led = esp32 and tem_estrelas(analise)
        self.linhas: list[str] = []
        self.nivel = 0

    def linha(self, texto):
        self.linhas.append("    " * self.nivel + texto)

    def corpo(self, stmts):
        """Corpo recuado de if/while; vazio vira pass."""
        self.nivel += 1
        antes = len(self.linhas)
        for stmt in stmts:
            self.gen(stmt)
        if len(self.linhas) == antes:
            self.linha("pass")
        self.nivel -= 1

    def nome(self, node) -> str:
        return self.nomes[node.simbolo.unico]

    # ---- instruções ----
    def gen(self, node: Node):
        getattr(self, f"gen_{type(node).__name__}")(node)

    def gen_Program(self, node: Program):
        for stmt in node.body:
            self.gen(stmt)

    def gen_Block(self, node):
        # bloco solto: os nomes já são únicos, então as instruções ficam no mesmo nível
        for stmt in node.stmts:
            self.gen(stmt)

    def gen_VarDecl(self, node):
        self.linha(f"{self.nome(node)} = {self.expr(node.value)[0]}")
        if self.led and node.simbolo.nome == ESTRELAS and node.simbolo.tipo == INTEIRO:
            self.linha(f"_procurado({self.nome(node)})")

    gen_Assign = gen_VarDecl

    def gen_Print(self, node):
        texto = self.expr(node.value)[0]
        if node.value.tipo == BOOLEANO:  # o tipo estático decide como imprimir
            self.linha(f'print("FULLCLIP" if {texto} else "GHOSTTOWN")')
        else:
            self.linha(f"print({texto})")

    def gen_If(self, node: If, palavra="if"):
        self.linha(f"{palavra} {self.expr(node.cond)[0]}:")
        self.corpo(node.then.stmts)
        if isinstance(node.orelse, If):
            self.gen_If(node.orelse, "elif")
        elif node.orelse is not None:
            self.linha("else:")
            self.corpo(node.orelse.stmts)

    def gen_While(self, node):
        self.linha(f"while {self.expr(node.cond)[0]}:")
        self.corpo(node.body.stmts)

    def gen_Break(self, node):
        self.linha("break")

    # ---- expressões: (texto, precedência) ----
    def expr(self, node) -> tuple[str, int]:
        if isinstance(node, Literal):
            v = node.value
            if isinstance(v, str):  # string da Grove não tem " nem quebra de linha; só a \ precisa de escape
                return '"' + v.replace("\\", "\\\\") + '"', ATOMO
            return str(v), ATOMO  # str(True) == "True"
        if isinstance(node, Var):
            return self.nome(node), ATOMO
        if isinstance(node, Unary):
            if node.op == "!":
                return f"not {self.operando(node.operand, PRECEDENCIA['not'])}", PRECEDENCIA["not"]
            return f"-{self.operando(node.operand, PRECEDENCIA['neg'])}", PRECEDENCIA["neg"]
        op = PY_OP.get(node.op, node.op)
        p = PRECEDENCIA[op]
        # associativo à esquerda: o lado direito de mesma precedência precisa de parênteses;
        # comparação nunca encadeia (em Python, a == b == c é a == b and b == c)
        esq = self.operando(node.left, p + (p == COMPARACAO))
        dir = self.operando(node.right, p + 1)
        return f"{esq} {op} {dir}", p

    def operando(self, node, minima: int) -> str:
        """Texto do operando, entre parênteses se a precedência dele for menor que a mínima."""
        texto, p = self.expr(node)
        return f"({texto})" if p < minima else texto


def emit_python(program: Program, analise: Analise, origem: str | None = None, esp32=False, pino=2) -> str:
    """Traduz a AST já conferida por check() para Python.

    Com esp32=True sai MicroPython: se o programa tem uma variável inteira
    `estrelas`, cada valor novo dela muda o pisca-pisca do LED no GPIO `pino`.
    """
    g = PythonGen(analise, esp32)
    cabecalho = f"# gerado pela Grove a partir de {origem}" if origem else "# gerado pela Grove"
    if g.led:
        cabecalho += f"\n# MicroPython para ESP32: '{ESTRELAS}' pisca o LED no GPIO {pino}\n"
        cabecalho += PRELUDIO_ESP32.format(pino=pino)
    g.linhas.append(cabecalho)
    g.gen(program)
    return "\n".join(g.linhas)
