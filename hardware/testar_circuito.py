"""Testes elétricos do HUD de procurado no ngspice (o motor de simulação do EasyEDA).

    python hardware/testar_circuito.py [programa.cj] [--figura arquivo.png]

1. Ponto de operação: a corrente de cada LED com 3,3 V no pino e no pior caso
   (pino a 3,0 V, resistor 5% acima, LED que pede mais tensão), para ver se
   acende e se fica dentro do que o pino e o LED aguentam.
2. Programa e circuito juntos: roda o MicroPython gerado com --esp32 --hud numa
   placa de mentira com relógio virtual (os timers disparam no tempo certo),
   transforma o que cada pino fez em fontes PWL e simula o circuito no tempo.
   Confere, em cada nível de procurado, quantos LEDs amarelos conduzem e o
   ritmo do giroflex, medidos na corrente dos LEDs.

Precisa do ngspice (apt install ngspice). A figura usa matplotlib, se houver.
Sai com código 1 se alguma conferência falhar.
"""

import argparse
import bisect
import os
import shutil
import subprocess
import sys
import tempfile
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))

from grove import check, emit_python, parse, tokenize  # noqa: E402
from grove.codegen_py import GIROFLEX_A_PARTIR_DE, PINO_AZUL, PINO_VERMELHO, PINOS_ESTRELAS  # noqa: E402

VPINO = 3.3
VPINO_MIN = 3.0  # pino em nível alto com carga, com folga
VISIVEL = 1e-3  # corrente mínima para enxergar bem o LED numa sala
ACESO = VISIVEL  # abaixo disso o LED conta como apagado
LIMITE_PINO = 20e-3  # força padrão do pino da ESP32 e corrente nominal do LED de 5 mm
SUBIDA = 1e-6  # tempo de subida das bordas nas fontes PWL

# pino -> (nome, resistor, modelo)
LEDS = {p: (f"estrela {i + 1}", 220, "LED_AMARELO") for i, p in enumerate(PINOS_ESTRELAS)}
LEDS[PINO_VERMELHO] = ("giroflex vermelho", 220, "LED_VERMELHO")
LEDS[PINO_AZUL] = ("giroflex azul", 100, "LED_AZUL")


# --- ngspice -------------------------------------------------------------------

def ngspice(netlist: str, saidas: list[str]) -> dict[str, list[float]]:
    """Roda o netlist e devolve os vetores pedidos (o tempo vem em 'tempo')."""
    with tempfile.TemporaryDirectory() as pasta:
        arquivo = os.path.join(pasta, "circuito.cir")
        dados = os.path.join(pasta, "dados.txt")
        controle = f".control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {dados} {' '.join(saidas)}\n.endc\n"
        with open(arquivo, "w") as f:
            f.write(netlist.replace(".end\n", controle + ".end\n"))
        r = subprocess.run(["ngspice", "-b", arquivo], capture_output=True, text=True, cwd=AQUI)
        if r.returncode != 0 or not os.path.exists(dados):
            sys.exit("o ngspice falhou:\n" + r.stdout + r.stderr)
        with open(dados) as f:
            linhas = f.read().split("\n")
    colunas = linhas[0].split()
    valores = [list(map(float, l.split())) for l in linhas[1:] if l.strip()]
    vetores = {nome: [v[i] for v in valores] for i, nome in enumerate(colunas)}
    if "time" in vetores:
        vetores["tempo"] = vetores.pop("time")
    return vetores


def cabecalho() -> str:
    return f"* gerado por hardware/testar_circuito.py\n.include {os.path.join(AQUI, 'leds.lib')}\n"


# --- 1. ponto de operação --------------------------------------------------------

CASOS = [  # (rótulo, resistor, modelo típico, modelo alto)
    ("amarelo", 220, "LED_AMARELO", "LED_AMARELO_ALTO"),
    ("vermelho", 220, "LED_VERMELHO", "LED_VERMELHO_ALTO"),
    ("azul", 100, "LED_AZUL", "LED_AZUL_ALTO"),
    ("azul com 220 Ω", 220, "LED_AZUL", "LED_AZUL_ALTO"),  # por que o azul leva 100 Ω
]


def ponto_de_operacao() -> tuple[list[tuple], bool]:
    linhas, saidas = [cabecalho()], []
    for i, (_, r, tipico, alto) in enumerate(CASOS):
        for caso, v, resistor, modelo in (("t", VPINO, r, tipico),
                                          ("min", VPINO_MIN, r * 1.05, alto),
                                          ("max", VPINO, r * 0.95, tipico)):
            n = f"{i}{caso}"
            linhas.append(f"V{n} g{n} 0 {v}\nR{n} g{n} a{n} {resistor}\nD{n} a{n} 0 {modelo}\n")
            saidas += [f"i(V{n})", f"v(a{n})"]
    vetores = ngspice("".join(linhas) + ".op\n.end\n", saidas)
    tabela, ok = [], True
    for i, (rotulo, r, _, _) in enumerate(CASOS):
        corrente = {c: -vetores[f"i(V{i}{c})"][0] for c in ("t", "min", "max")}
        vf = vetores[f"v(a{i}t)"][0]
        potencia = corrente["max"] ** 2 * r * 0.95
        passou = corrente["min"] >= VISIVEL and corrente["max"] <= LIMITE_PINO
        if r == 100 or rotulo != "azul com 220 Ω":
            ok &= passou
        tabela.append((rotulo, r, vf, corrente["t"], corrente["min"], corrente["max"], potencia, passou))
    return tabela, ok


# --- 2. placa de mentira com relógio virtual -------------------------------------

class Placa:
    def __init__(self):
        self.agora = 0  # ms
        self.timers = []
        self.eventos = {}  # pino -> {ms: valor}
        self.janelas = []  # (início, duração, estrelas)
        self.serial = []

    def registrar(self, pino, valor):
        self.eventos.setdefault(pino, {})[self.agora] = valor

    def avancar(self, ms):
        fim = self.agora + ms
        while True:
            ativos = [t for t in self.timers if t.ativo and t.proximo <= fim]
            if not ativos:
                break
            t = min(ativos, key=lambda t: (t.proximo, t.id))
            self.agora = t.proximo
            t.proximo += t.periodo
            t.callback(t)
        self.agora = fim

    def modulos(self):
        placa = self

        class Pin:
            OUT = 1

            def __init__(self, numero, modo=None):
                self.numero, self.v = numero, 0
                placa.registrar(numero, 0)

            def value(self, v=None):
                if v is None:
                    return self.v
                self.v = 1 if v else 0
                placa.registrar(self.numero, self.v)

        class Timer:
            PERIODIC = 1

            def __init__(self, id):
                self.id, self.ativo = id, False
                placa.timers.append(self)

            def init(self, period, mode, callback):
                self.periodo, self.proximo, self.callback, self.ativo = period, placa.agora + period, callback, True

            def deinit(self):
                self.ativo = False

        def sleep_ms(ms):
            quem = sys._getframe(1)
            if quem.f_code.co_name == "_procurado":
                placa.janelas.append((placa.agora, ms, quem.f_locals["n"]))
            placa.avancar(ms)

        machine = types.ModuleType("machine")
        machine.Pin, machine.Timer = Pin, Timer
        tempo = types.ModuleType("time")
        tempo.sleep_ms = sleep_ms
        return {"machine": machine, "time": tempo}


def rodar_na_placa(codigo: str, depois: int) -> Placa:
    placa = Placa()
    antigos = {nome: sys.modules.get(nome) for nome in ("machine", "time")}
    sys.modules.update(placa.modulos())
    try:
        def serial(*args):
            placa.serial.append((placa.agora, " ".join(map(str, args))))
        exec(compile(codigo, "main.py", "exec"), {"__name__": "__main__", "print": serial})
        placa.janelas.append((placa.agora, depois, None))  # o programa acabou; os timers seguem
        placa.avancar(depois)
    finally:
        for nome, modulo in antigos.items():
            if modulo is None:
                sys.modules.pop(nome, None)
            else:
                sys.modules[nome] = modulo
    return placa


def pwl(eventos: dict[int, int]) -> str:
    anterior = eventos.get(0, 0)  # um pino pode já sair ligado no instante zero
    pontos = [f"0 {anterior * VPINO}"]
    for ms in sorted(eventos):
        v = eventos[ms]
        if ms > 0 and v != anterior:
            t = ms / 1000
            pontos += [f"{t:.6f} {anterior * VPINO}", f"{t + SUBIDA:.7f} {v * VPINO}"]
            anterior = v
    return "PWL(" + "\n+ ".join(pontos) + ")"


def simular_no_tempo(placa: Placa) -> dict[str, list[float]]:
    fim = placa.agora / 1000
    linhas = [cabecalho()]
    for pino, (_, r, modelo) in LEDS.items():
        linhas.append(f"V{pino} g{pino} 0 {pwl(placa.eventos.get(pino, {}))}\n"
                      f"R{pino} g{pino} a{pino} {r}\nD{pino} a{pino} 0 {modelo}\n")
    linhas.append(f".tran 1m {fim} 0 1m\n.end\n")
    vetores = ngspice("".join(linhas), [f"i(V{p})" for p in LEDS])
    return {"tempo": vetores["tempo"], **{p: [-i for i in vetores[f"i(V{p})"]] for p in LEDS}}


def amostra(vetores, pino, t):
    tempo = vetores["tempo"]
    k = bisect.bisect_left(tempo, t)
    if k == 0:
        return vetores[pino][0]
    if k >= len(tempo):
        return vetores[pino][-1]
    t0, t1 = tempo[k - 1], tempo[k]
    y0, y1 = vetores[pino][k - 1], vetores[pino][k]
    return y0 + (y1 - y0) * (t - t0) / (t1 - t0) if t1 > t0 else y1


def bordas(vetores, pino, inicio, fim):
    """Instantes em que a corrente do LED cruza o limiar de aceso."""
    corrente, tempo = vetores[pino], vetores["tempo"]
    meio = ACESO
    cruzamentos = []
    for k in range(1, len(tempo)):
        if not inicio < tempo[k] < fim:
            continue
        a, b = corrente[k - 1] - meio, corrente[k] - meio
        if a * b < 0:
            cruzamentos.append(tempo[k - 1] + (tempo[k] - tempo[k - 1]) * a / (a - b))
    return cruzamentos


def conferir_no_tempo(placa, vetores):
    resultados, ok = [], True
    amarelos = list(PINOS_ESTRELAS)
    for inicio, duracao, n in placa.janelas:
        a, b = inicio / 1000, (inicio + duracao) / 1000
        grade = [a + (k + 0.5) / 1000 for k in range(1, duracao - 1)]  # meio de cada ms, longe das bordas
        depois_do_fim = n is None
        if depois_do_fim:  # o programa acabou: tudo segue como o último nível deixou
            n = placa.janelas[-2][2] if len(placa.janelas) > 1 else 0
        esperado = max(0, min(n, len(amarelos)))
        acesos = [sum(amostra(vetores, p, t) > ACESO for p in amarelos) for t in grade]
        certos = all(c == esperado for c in acesos) and all(
            (amostra(vetores, p, t) > ACESO) == (i < esperado) for t in grade[::50] for i, p in enumerate(amarelos))
        juntos = any(amostra(vetores, PINO_VERMELHO, t) > ACESO and amostra(vetores, PINO_AZUL, t) > ACESO
                     for t in grade)
        if n >= GIROFLEX_A_PARTIR_DE:
            periodo = max(100, 300 - 50 * (n - GIROFLEX_A_PARTIR_DE))
            medidos, parados = [], []
            for p in (PINO_VERMELHO, PINO_AZUL):
                ts = bordas(vetores, p, a, b - 0.0005)
                if len(ts) < 2:
                    parados.append(LEDS[p][0].split()[-1])
                medidos += [(t1 - t0) * 1000 for t0, t1 in zip(ts, ts[1:])]
            giro_ok = not parados and all(abs(m - periodo) < 0.5 for m in medidos) and not juntos
            if parados:
                giro = " e ".join(parados) + " não pisca" + ("m" if len(parados) > 1 else "")
            else:
                menor, maior = round(min(medidos)), round(max(medidos))
                faixa = f"{menor}" if menor == maior else f"{menor} a {maior}"
                giro = f"alterna a cada {faixa} ms (esperado {periodo})"
        else:
            periodo = None
            parado = all(amostra(vetores, p, t) < 1e-6 for p in (PINO_VERMELHO, PINO_AZUL) for t in grade)
            giro_ok, giro = parado, ("apagado" if parado else "aceso, e devia estar apagado")
        total = max(sum(amostra(vetores, p, t) for p in LEDS) for t in grade)
        passou = certos and giro_ok
        ok &= passou
        resultados.append((inicio, None if depois_do_fim else n, esperado, sorted(set(acesos)), giro, juntos, total,
                           passou))
    return resultados, ok


# --- figura ----------------------------------------------------------------------

def figura(placa, vetores, caminho):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(f"(sem matplotlib: a figura {caminho} não foi gerada)")
        return
    passo = 0.002
    grade = [k * passo for k in range(int(vetores["tempo"][-1] / passo))]
    cores = {p: "#e2a529" for p in PINOS_ESTRELAS} | {PINO_VERMELHO: "#d0342c", PINO_AZUL: "#2f6fd6"}
    fig, (luzes, soma) = plt.subplots(2, 1, figsize=(10, 5.6), sharex=True,
                                      gridspec_kw={"height_ratios": [3, 1.2]})
    ordem = list(LEDS)[::-1]
    for faixa, p in enumerate(ordem):
        corrente = [amostra(vetores, p, t) * 1000 for t in grade]
        base = faixa * 8
        luzes.fill_between(grade, base, [base + c for c in corrente], step="post", color=cores[p], linewidth=0)
        luzes.axhline(base, color="#999", linewidth=0.4)
    luzes.set_yticks([f * 8 + 3 for f in range(len(ordem))])
    luzes.set_yticklabels([f"GPIO {p} · {LEDS[p][0]}" for p in ordem], fontsize=8)
    luzes.set_ylim(-1, len(ordem) * 8)
    for inicio, _, n in placa.janelas:
        luzes.axvline(inicio / 1000, color="#555", linewidth=0.6, linestyle=":")
        rotulo = f"{n}★" if n is not None else "fim"
        luzes.text(inicio / 1000 + 0.05, len(ordem) * 8 - 0.5, rotulo, fontsize=8, va="top")
    luzes.set_title("HUD de procurado: corrente em cada LED (cada faixa vai de 0 a 8 mA)", fontsize=10)
    total = [sum(amostra(vetores, p, t) for p in LEDS) * 1000 for t in grade]
    soma.fill_between(grade, 0, total, step="post", color="#555", linewidth=0)
    soma.set_ylabel("total (mA)", fontsize=8)
    soma.set_xlabel("tempo (s)", fontsize=8)
    soma.set_ylim(0, 50)
    for eixo in (luzes, soma):
        eixo.tick_params(labelsize=8)
        eixo.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    print(f"figura: {caminho}")


# --- linha de comando ------------------------------------------------------------

def br(x, formato):
    return format(x, formato).replace(".", ",")


def mA(i):
    return br(i * 1000, ".2f")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("arquivo", nargs="?", default=os.path.join(os.path.dirname(AQUI), "examples", "procurado.cj"))
    ap.add_argument("--figura", help="salva o gráfico das correntes (PNG)")
    ap.add_argument("--depois", type=int, default=2000, help="ms simulados depois do fim do programa")
    args = ap.parse_args(argv)
    if not shutil.which("ngspice"):
        sys.exit("precisa do ngspice: apt install ngspice (ou baixe em ngspice.sourceforge.io)")

    print("== 1. Ponto de operação: um LED aceso ==")
    print(f"típico: pino a {br(VPINO, 'g')} V · mínimo: pino a {br(VPINO_MIN, '.1f')} V, resistor +5%,"
          f" LED que pede mais tensão · máximo: {br(VPINO, 'g')} V, resistor -5%\n")
    print(f"{'LED':<16}{'resistor':>9}{'Vf':>7}{'típico':>9}{'mínimo':>9}{'máximo':>9}{'potência':>10}")
    tabela, ok1 = ponto_de_operacao()
    for rotulo, r, vf, t, mn, mx, pot, passou in tabela:
        marca = "ok" if passou else ("fraco" if mn < VISIVEL else "alto")
        print(f"{rotulo:<16}{r:>7} Ω{br(vf, '>6.2f')} V{mA(t):>6} mA{mA(mn):>6} mA{mA(mx):>6} mA"
              f"{br(pot * 1000, '>7.1f')} mW  {marca}")
    print(f"\ncritério: no mínimo {VISIVEL * 1000:g} mA (aceso e visível), no máximo {LIMITE_PINO * 1000:g} mA"
          " (pino e LED). A linha do azul com 220 Ω é só a comparação.")

    with open(args.arquivo, encoding="utf-8") as f:
        programa = parse(tokenize(f.read()))
    codigo = emit_python(programa, check(programa), origem=args.arquivo, esp32=True, hud=True)
    placa = rodar_na_placa(codigo, args.depois)
    vetores = simular_no_tempo(placa)
    print(f"\n== 2. {os.path.basename(args.arquivo)} no circuito: {br(placa.agora / 1000, 'g')} s simulados ==\n")
    resultados, ok2 = conferir_no_tempo(placa, vetores)
    for inicio, n, esperado, acesos, giro, juntos, total, passou in resultados:
        nivel = f"{n}★" if n is not None else "fim"
        luzes = f"{acesos[0]} amarelo(s) aceso(s)" if len(acesos) == 1 else f"oscila entre {acesos}"
        print(f"{br(inicio / 1000, '5.1f')} s  {nivel:<4} {luzes} (esperado {esperado}) · giroflex {giro}"
              f"{' · VERMELHO E AZUL JUNTOS' if juntos else ''} · pico {mA(total)} mA  {'ok' if passou else 'FALHOU'}")
    pico = max(r[6] for r in resultados)
    print(f"\ncorrente total máxima nos LEDs externos: {mA(pico)} mA")
    print("serial: " + " · ".join(texto for _, texto in placa.serial))
    if args.figura:
        figura(placa, vetores, args.figura)
    ok = ok1 and ok2
    print("\ntudo certo" if ok else "\nalguma conferência falhou")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
