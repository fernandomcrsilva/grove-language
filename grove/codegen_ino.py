"""Back-end: AST anotada → código Arduino (C++) para o Mega 2560.

Irmão do codegen_py.py: mesma travessia da AST, outra linguagem de saída.
Tradução em docs/geracao-de-codigo.md. O corpo do programa vai todo no
`setup()`, com o `loop()` vazio, porque um programa Grove roda uma vez.

Três coisas que o C não dá de graça e o prelúdio resolve:

* `/` e `%` no C cortam para o zero, e o interpretador arredonda para baixo
  (`-7 / 2` é -4 na Grove e -3 no C). `_div` e `_mod` acertam o sinal.
* dividir por zero é erro na Grove e silêncio no AVR: `_div` avisa e para.
* os inteiros da Grove viram `long`, de 32 bits, porque o `int` do AVR tem 16.
  Por isso todo literal sai com o sufixo `L`.
"""
from .ast import Assign, If, Input, Literal, Node, Program, Unary, Var, VarDecl
from .semantic import BOOLEANO, INTEIRO, STRING, Analise

# precedência em C, da menor para a maior; / e % viram chamada, então não entram
PRECEDENCIA = {
    "||": 1, "&&": 2,
    "==": 3, "!=": 3,
    "<": 4, ">": 4, "<=": 4, ">=": 4,
    "+": 5, "-": 5, "*": 6,
    "!": 7, "neg": 7,
}
ATOMO = 8
COMPARACOES = {"==", "!=", "<", ">", "<=", ">="}
CHAMADA = {"/": "_div", "%": "_mod"}  # precisam de sinal igual ao do interpretador

TIPO_C = {INTEIRO: "long", STRING: "String", BOOLEANO: "bool"}

# palavras que uma variável não pode ter no código gerado
RESERVADOS = {
    "alignas", "alignof", "asm", "auto", "bool", "break", "byte", "case", "catch", "char", "class", "const",
    "constexpr", "continue", "default", "delete", "do", "double", "else", "enum", "explicit", "export", "extern",
    "false", "float", "for", "friend", "goto", "if", "inline", "int", "long", "loop", "main", "mutable", "namespace",
    "new", "nullptr", "operator", "private", "protected", "public", "register", "return", "setup", "short", "signed",
    "sizeof", "static", "struct", "switch", "template", "this", "throw", "true", "try", "typedef", "typename", "union",
    "unsigned", "using", "virtual", "void", "volatile", "while",
    "String", "Serial", "HIGH", "LOW", "OUTPUT", "INPUT", "millis", "delay", "pinMode", "digitalWrite", "max", "exit",
    # o que o prelúdio declara fora das funções
    "_LED", "_ESTRELAS", "_VERMELHO", "_AZUL", "_GIROFLEX", "_parar", "_div", "_mod", "_inicializar", "_procurado",
    "_tique", "_linha", "_ledp", "_girop", "_aceso", "_fase", "_epoca", "_tled", "_tgiro",
}

# Mega 2560: a variável inteira `estrelas` comanda os LEDs, como o nível de procurado no jogo
ESTRELAS = "estrelas"
PINO_PLACA = 13  # LED que já vem soldado na placa
# a ordem é a da fiação montada, na barra dupla do Mega; D0 e D1 ficam livres, que são a serial da USB
PINOS_ESTRELAS = (52, 53, 50, 51, 49, 48)
PINO_VERMELHO, PINO_AZUL = 33, 32
GIROFLEX_A_PARTIR_DE = 4
MOSTRA_MS = 1500  # tempo parado em cada nível, para dar para ver

AJUDA_DIV = """\
void _parar(const char *msg) {
  Serial.print("erro: ");
  Serial.println(msg);
  Serial.flush();
  exit(1);
}

long _div(long a, long b) {  // divisão da Grove: arredonda para baixo, não para o zero
  if (b == 0) _parar("divisão por zero");
  long q = a / b;
  return (a % b != 0 && ((a < 0) != (b < 0))) ? q - 1 : q;
}

long _mod(long a, long b) { return a - _div(a, b) * b; }

"""

ESTADO = """\
const int _LED = {pino};  // LED da placa: pisca mais rápido a cada estrela
{constantes}
long _ledp = 0;  // ms entre as piscadas; 0 = parado
bool _aceso = false;
unsigned long _epoca = 0, _tled = 0;  // o ritmo recomeça a cada nível novo{estado_hud}

void _tique() {{  // chamado sem parar: faz piscar quem tiver período
  unsigned long _t = millis() - _epoca;
  if (_ledp && _t / _ledp != _tled) {{
    _tled = _t / _ledp;
    _aceso = !_aceso;
    digitalWrite(_LED, _aceso);
  }}{tique_hud}
}}

void _inicializar() {{
  pinMode(_LED, OUTPUT);{pinos}
}}

void _procurado(long n) {{{corpo}
  _ledp = n > 0 ? max(50L, 600L / n) : 0;{periodo_hud}
  _epoca = millis();
  _aceso = false;
  _tled = 0;
  digitalWrite(_LED, LOW);{apaga_hud}{pausa}
}}

"""
HUD_CONSTANTES = """const int _ESTRELAS[] = {{{estrelas}}};  // uma luz por estrela de procurado
const int _VERMELHO = {vermelho}, _AZUL = {azul};  // giroflex da polícia
const int _GIROFLEX = {giroflex};  // estrelas a partir das quais ele liga
"""
HUD_ESTADO = """
long _girop = 0;
bool _fase = false;
unsigned long _tgiro = 0;"""
HUD_TIQUE = """
  if (_girop && _t / _girop != _tgiro) {
    _tgiro = _t / _girop;
    _fase = !_fase;
    digitalWrite(_VERMELHO, _fase);
    digitalWrite(_AZUL, !_fase);
  }"""
HUD_PINOS = """
  for (int i = 0; i < {quantas}; i++) pinMode(_ESTRELAS[i], OUTPUT);
  pinMode(_VERMELHO, OUTPUT);
  pinMode(_AZUL, OUTPUT);"""
HUD_CORPO = """
  for (int i = 0; i < {quantas}; i++) digitalWrite(_ESTRELAS[i], i < n ? HIGH : LOW);  // acende as primeiras n
"""
HUD_PERIODO = """
  _girop = n >= _GIROFLEX ? max(100L, 300L - 50L * (n - _GIROFLEX)) : 0;  // a polícia chegou"""
HUD_APAGA = """
  _tgiro = 0;
  if (!_girop) {
    digitalWrite(_VERMELHO, LOW);
    digitalWrite(_AZUL, LOW);
  }"""


PAUSA = """
  while (millis() - _epoca < {mostra}) {{  // fica {mostra} ms em cada nível, para dar para ver
    _tique();
    delay(1);
  }}"""
LEITURA = """\
long _linha() {{  // CJPHONEHOME: espera uma linha inteira na serial e devolve o número
  char buf[8];
  byte i = 0;
  for (;;) {{
    while (Serial.available() == 0) {{{espera}}}
    char c = Serial.read();
    if (c == '\\n' || c == '\\r') {{
      if (i == 0) continue;  // fim de linha sem nada antes: ignora
      break;
    }}
    if (i < sizeof(buf) - 1) buf[i++] = c;
  }}
  buf[i] = '\\0';
  return atol(buf);
}}

"""
ESPERA_PISCANDO = """
      _tique();  // o pisca-pisca não para enquanto a linha não chega
    """


def tem_estrelas(analise: Analise) -> bool:
    return any(s.nome == ESTRELAS and s.tipo == INTEIRO for s in analise.simbolos)


def _nomes_c(analise: Analise) -> dict[str, str]:
    """nome único → nome em C; quem colide com um reservado ganha _ no fim."""
    usados = {s.unico for s in analise.simbolos}
    mapa = {}
    for s in analise.simbolos:
        nome = s.unico
        while nome in RESERVADOS or (nome != s.unico and nome in usados):
            nome += "_"
        usados.add(nome)
        mapa[s.unico] = nome
    return mapa


class InoGen:
    def __init__(self, analise: Analise, led=False):
        self.nomes = _nomes_c(analise)
        self.led = led
        self.usa_div = False      # só vale a pena emitir _div e _mod se o programa divide
        self.usa_entrada = False  # idem para _linha
        self.linhas: list[str] = []
        self.nivel = 1  # o corpo do programa já nasce dentro do setup()

    def linha(self, texto):
        self.linhas.append("  " * self.nivel + texto)

    def corpo(self, stmts):
        self.nivel += 1
        for stmt in stmts:
            self.gen(stmt)
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

    def gen_VarDecl(self, node: VarDecl):
        self.linha(f"{TIPO_C[node.simbolo.tipo]} {self.nome(node)} = {self.expr(node.value)[0]};")
        self.procurado(node)

    def gen_Assign(self, node: Assign):
        self.linha(f"{self.nome(node)} = {self.expr(node.value)[0]};")
        self.procurado(node)

    def procurado(self, node):
        """Depois de cada valor novo de `estrelas`, o hardware acompanha."""
        if self.led and node.simbolo.nome == ESTRELAS and node.simbolo.tipo == INTEIRO:
            self.linha(f"_procurado({self.nome(node)});")

    def gen_Print(self, node):
        texto = self.expr(node.value)[0]
        if node.value.tipo == BOOLEANO:  # o tipo estático decide como imprimir
            self.linha(f'Serial.println({texto} ? "FULLCLIP" : "GHOSTTOWN");')  # ?: é o mais fraco do C
        else:
            self.linha(f"Serial.println({texto});")

    def gen_If(self, node: If, palavra="if"):
        self.linha(f"{palavra} ({self.expr(node.cond)[0]}) {{")
        self.corpo(node.then.stmts)
        if isinstance(node.orelse, If):
            self.gen_If(node.orelse, "} else if")
        elif node.orelse is not None:
            self.linha("} else {")
            self.corpo(node.orelse.stmts)
            self.linha("}")
        else:
            self.linha("}")

    def gen_While(self, node):
        self.linha(f"while ({self.expr(node.cond)[0]}) {{")
        self.corpo(node.body.stmts)
        self.linha("}")

    def gen_Break(self, node):
        self.linha("break;")

    # ---- expressões: (texto, precedência) ----
    def expr(self, node) -> tuple[str, int]:
        if isinstance(node, Literal):
            v = node.value
            if isinstance(v, bool):  # antes de int: em Python, bool é int
                return ("true" if v else "false"), ATOMO
            if isinstance(v, str):  # string da Grove não tem " nem quebra de linha; só a \ precisa de escape
                return '"' + v.replace("\\", "\\\\") + '"', ATOMO
            return f"{v}L", ATOMO  # L porque o int do AVR tem 16 bits
        if isinstance(node, Input):
            self.usa_entrada = True
            return "_linha()", ATOMO
        if isinstance(node, Var):
            return self.nome(node), ATOMO
        if isinstance(node, Unary):
            simbolo = "!" if node.op == "!" else "-"
            texto = self.operando(node.operand, PRECEDENCIA["neg"])
            if simbolo == "-" and texto.startswith("-"):
                texto = f"({texto})"  # - -3 não pode virar --3, que no C é decremento
            return f"{simbolo}{texto}", PRECEDENCIA["neg"]
        if node.op in CHAMADA:  # / e % viram chamada: a conta do sinal não cabe num operador
            self.usa_div = True
            return f"{CHAMADA[node.op]}({self.expr(node.left)[0]}, {self.expr(node.right)[0]})", ATOMO
        p = PRECEDENCIA[node.op]
        esq = self.operando(node.left, p)  # associativo à esquerda
        dir = self.operando(node.right, p + 1)
        if node.op in ("==", "!="):  # comparação dentro de comparação: o compilador pede os parênteses
            esq, dir = (f"({t})" if self.comparacao(n) else t
                        for n, t in ((node.left, esq), (node.right, dir)))
        if node.left.tipo == STRING and isinstance(node.left, Literal):
            esq = f"String({esq})"  # dois literais: sem isto o C compara ou soma ponteiros
        return f"{esq} {node.op} {dir}", p

    def comparacao(self, node) -> bool:
        return not isinstance(node, Unary) and getattr(node, "op", None) in COMPARACOES

    def operando(self, node, minima: int) -> str:
        """Texto do operando, entre parênteses se a precedência dele for menor que a mínima."""
        texto, p = self.expr(node)
        return f"({texto})" if p < minima else texto


def _preludio_led(pino: int, hud: bool, entrada: bool) -> str:
    partes = dict(pino=pino, mostra=MOSTRA_MS, constantes="", estado_hud="", tique_hud="", pinos="", corpo="",
                  periodo_hud="", apaga_hud="",
                  # quem manda os níveis é a entrada: esperar aqui só atrasaria o LED
                  pausa="" if entrada else PAUSA.format(mostra=MOSTRA_MS))
    if hud:
        quantas = len(PINOS_ESTRELAS)
        partes.update(
            constantes=HUD_CONSTANTES.format(estrelas=", ".join(map(str, PINOS_ESTRELAS)), vermelho=PINO_VERMELHO,
                                             azul=PINO_AZUL, giroflex=GIROFLEX_A_PARTIR_DE),
            estado_hud=HUD_ESTADO, tique_hud=HUD_TIQUE, pinos=HUD_PINOS.format(quantas=quantas),
            corpo=HUD_CORPO.format(quantas=quantas), periodo_hud=HUD_PERIODO, apaga_hud=HUD_APAGA)
    return ESTADO.format(**partes)


def emit_ino(program: Program, analise: Analise, origem: str | None = None, pino=PINO_PLACA, hud=False) -> str:
    """Traduz a AST já conferida por check() para um sketch do Arduino.

    Se o programa tem uma variável inteira `estrelas`, cada valor novo dela
    muda o pisca-pisca do LED no pino `pino`. Com hud=True também acende uma
    luz por estrela (PINOS_ESTRELAS) e liga o giroflex vermelho e azul a
    partir de GIROFLEX_A_PARTIR_DE estrelas.
    """
    led = tem_estrelas(analise)
    g = InoGen(analise, led)
    g.gen(program)  # o corpo primeiro: é ele que diz se o prelúdio precisa de _div
    topo = [f"// gerado pela Grove a partir de {origem}" if origem else "// gerado pela Grove"]
    if led:
        alvo = (f"// Arduino Mega 2560, HUD de procurado: '{ESTRELAS}' acende as luzes nos pinos "
                f"{', '.join(map(str, PINOS_ESTRELAS))}, liga o giroflex nos pinos {PINO_VERMELHO} e {PINO_AZUL} "
                f"a partir de {GIROFLEX_A_PARTIR_DE} estrelas e pisca o LED no pino {pino}") if hud else (
                f"// Arduino Mega 2560: '{ESTRELAS}' pisca o LED no pino {pino}")
        topo.append(alvo)
    topo.append("// grave com: arduino-cli compile --fqbn arduino:avr:mega:cpu=atmega2560 <pasta> && arduino-cli upload …")
    topo.append("")
    if g.usa_div:
        topo.append(AJUDA_DIV.rstrip("\n"))
        topo.append("")
    if led:
        topo.append(_preludio_led(pino, hud, g.usa_entrada).rstrip("\n"))
        topo.append("")
    if g.usa_entrada:  # depois do prelúdio dos LEDs: _linha chama _tique
        topo.append(LEITURA.format(espera=ESPERA_PISCANDO if led else "").rstrip("\n"))
        topo.append("")
    topo.append("void setup() {\n  Serial.begin(115200);" + ("\n  _inicializar();" if led else ""))
    fim = ("void loop() {\n  _tique();  // o programa acabou, mas o último nível continua piscando\n  delay(1);\n}"
           if led else "void loop() {}  // o programa Grove roda uma vez, no setup")
    return "\n".join(topo + g.linhas + ["}", "", fim])
