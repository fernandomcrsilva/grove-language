"""Otimização do código de três endereços.

Passadas simples e seguras, repetidas até nada mudar (docs/codigo-intermediario.md):

- constantes calculadas na compilação: t1 = 2 + 3 vira t1 = 5
- propagação de constantes e de cópias dentro de cada bloco básico: x = 5; t2 = x * 2 vira t2 = 5 * 2,
  e t1 = x; print t1 vira print x
- simplificação algébrica: x + 0, x - 0, x * 1, x / 1 viram x; x * 0 e x % 1 viram 0
- desvios resolvidos: ifFalse FULLCLIP goto L some; ifFalse GHOSTTOWN goto L vira goto L
- instruções mortas: depois de um goto até o próximo rótulo, goto para o rótulo logo abaixo,
  rótulos que ninguém usa e temporários que ninguém lê

Divisão ou resto por zero nunca é calculado nem removido: continua sendo erro de execução, no mesmo ponto.
O código original não muda; otimizar() devolve uma lista nova.
"""
from dataclasses import replace

from .ir import OPERACOES, Const, Quad
from .semantic import Analise

DESVIOS = ("goto", "if", "iffalse")
SEM_DESTINO = ("label", "print", *DESVIOS)  # instruções cujo result não é uma variável escrita
ROTULOS = {
    "calculadas": ("conta calculada na compilação", "contas calculadas na compilação"),
    "propagadas": ("valor propagado", "valores propagados"),
    "simplificadas": ("simplificação algébrica", "simplificações algébricas"),
    "desvios": ("desvio resolvido", "desvios resolvidos"),
    "mortas": ("instrução morta removida", "instruções mortas removidas"),
}


def _tem_efeito(q: Quad) -> bool:
    """Instrução que não pode ser apagada nem calculada em tempo de compilação.

    Divisão ou resto que pode estourar, e a leitura do CJPHONEHOME, que consome
    uma linha da entrada mesmo quando ninguém usa o valor.
    """
    if q.op == "read":
        return True
    return q.op in ("/", "%") and not (isinstance(q.arg2, Const) and q.arg2.value != 0)


def _calcular(code, conta):
    novo = []
    for q in code:
        a, b = q.arg1, q.arg2
        if q.op in OPERACOES and isinstance(a, Const) and isinstance(b, Const) and not _tem_efeito(q):
            q = Quad("=", Const(OPERACOES[q.op](a.value, b.value)), result=q.result)
            conta["calculadas"] += 1
        elif q.op in ("!", "neg") and isinstance(a, Const):
            q = Quad("=", Const(not a.value if q.op == "!" else -a.value), result=q.result)
            conta["calculadas"] += 1
        novo.append(q)
    return novo


def _propagar(code, temporarios, conta):
    """Troca leituras de nomes cujo valor é conhecido: uma constante, ou a variável copiada para
    um temporário. O que se sabe zera a cada rótulo, e some quando o nome (ou o copiado) é reescrito."""
    novo, conhecidos = [], {}
    for q in code:
        if q.op == "label":
            conhecidos = {}
        elif q.op != "goto":
            trocas = {}
            for campo in ("arg1", "arg2"):
                valor = getattr(q, campo)
                if isinstance(valor, str) and valor in conhecidos:
                    trocas[campo] = conhecidos[valor]
            if trocas:
                q = replace(q, **trocas)
                conta["propagadas"] += len(trocas)
            if q.op not in SEM_DESTINO:
                d = q.result
                conhecidos = {k: v for k, v in conhecidos.items() if k != d and v != d}
                if q.op == "=" and (isinstance(q.arg1, Const) or d in temporarios and q.arg1 != d):
                    conhecidos[d] = q.arg1
        novo.append(q)
    return novo


def _simplificar(code, conta):
    def neutro(x, v):
        return isinstance(x, Const) and type(x.value) is int and x.value == v

    novo = []
    for q in code:
        a, b, simples = q.arg1, q.arg2, None
        if q.op == "+" and neutro(b, 0) or q.op in ("-", "/") and neutro(b, 0 if q.op == "-" else 1) or q.op == "*" and neutro(b, 1):
            simples = a
        elif q.op in ("+", "*") and neutro(a, 0 if q.op == "+" else 1):
            simples = b
        elif q.op == "*" and (neutro(a, 0) or neutro(b, 0)) or q.op == "%" and neutro(b, 1):
            simples = Const(0)
        if simples is not None:
            q = Quad("=", simples, result=q.result)
            conta["simplificadas"] += 1
        novo.append(q)
    return novo


def _resolver_desvios(code, conta):
    novo = []
    for q in code:
        if q.op in ("if", "iffalse") and isinstance(q.arg1, Const):
            conta["desvios"] += 1
            if bool(q.arg1.value) == (q.op == "if"):  # sempre desvia
                novo.append(Quad("goto", result=q.result))
            continue  # nunca desvia: some
        novo.append(q)
    return novo


def _remover_mortas(code, temporarios, conta):
    # depois de um goto, até o próximo rótulo, nada roda
    vivo, novo = True, []
    for q in code:
        if q.op == "label":
            vivo = True
        if vivo:
            novo.append(q)
        else:
            conta["mortas"] += 1
        if q.op == "goto":
            vivo = False
    code = novo
    # goto para um rótulo que vem logo em seguida (pulando só rótulos)
    novo = []
    for i, q in enumerate(code):
        if q.op == "goto":
            seguintes = []
            for r in code[i + 1:]:
                if r.op != "label":
                    break
                seguintes.append(r.result)
            if q.result in seguintes:
                conta["mortas"] += 1
                continue
        novo.append(q)
    code = novo
    # rótulos que nenhum desvio usa
    usados = {q.result for q in code if q.op in DESVIOS}
    novo = [q for q in code if q.op != "label" or q.result in usados]
    conta["mortas"] += len(code) - len(novo)
    code = novo
    # temporários escritos e nunca lidos (ou escritos de novo antes de qualquer leitura)
    novo = []
    for i, q in enumerate(code):
        if q.op not in SEM_DESTINO and q.result in temporarios and not _tem_efeito(q) and not _lido_depois(code, i):
            conta["mortas"] += 1
            continue
        novo.append(q)
    return novo


def _lido_depois(code, i) -> bool:
    t = code[i].result
    for j in range(i + 1, len(code)):
        q = code[j]
        if t in (q.arg1, q.arg2):
            return True
        if q.op in ("label", *DESVIOS):  # outro caminho pode chegar ou sair daqui: só vale se ninguém mais lê
            return any(t in (r.arg1, r.arg2) for r in code)
        if q.op not in SEM_DESTINO and q.result == t:  # reescrito antes de ser lido
            return False
    return False


def otimizar(code: list[Quad], analise: Analise) -> tuple[list[Quad], dict[str, int]]:
    """TAC otimizada (lista nova) e quantas vezes cada passada mudou alguma coisa."""
    temporarios = {q.result for q in code if q.op not in SEM_DESTINO} - {s.unico for s in analise.simbolos}
    conta = dict.fromkeys(ROTULOS, 0)
    for _ in range(50):  # cada volta só encolhe ou simplifica; 50 é folga de sobra
        antes = (list(code), dict(conta))
        code = _calcular(code, conta)
        code = _propagar(code, temporarios, conta)
        code = _simplificar(code, conta)
        code = _calcular(code, conta)
        code = _resolver_desvios(code, conta)
        code = _remover_mortas(code, temporarios, conta)
        if code == antes[0]:
            conta = antes[1]  # a volta que não mudou nada não conta
            break
    return code, conta


def resumo(antes: list[Quad], depois: list[Quad], conta: dict[str, int]) -> str:
    """Uma linha: 15 → 4 instruções · 3 contas calculadas na compilação · …"""
    partes = [f"{len(antes)} → {len(depois)} instruções"]
    for chave, (um, varios) in ROTULOS.items():
        if conta[chave]:
            partes.append(f"{conta[chave]} {um if conta[chave] == 1 else varios}")
    return " · ".join(partes) if len(partes) > 1 else f"{len(antes)} instruções: nada a otimizar"
