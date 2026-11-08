# -*- coding: utf-8 -*-
"""Desenha docs/img/montagem-hud.svg: a fiação do HUD, vista de cima.

    python hardware/gerar_montagem.py

Os pinos vêm de grove/codegen_ino.py, então mudar o código muda o desenho.
Desenho fora de escala: a placa é achatada para caber ao lado da protoboard.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)

from grove.codegen_ino import PINO_AZUL, PINO_PLACA, PINO_VERMELHO, PINOS_ESTRELAS  # noqa: E402

W, H = 1380, 820
LEDS = ([(p, f"estrela {i + 1}", "#e8c547") for i, p in enumerate(PINOS_ESTRELAS)]
        + [(PINO_VERMELHO, "giroflex vermelho", "#d55e00"), (PINO_AZUL, "giroflex azul", "#0072b2")])

# --- barra dupla do Mega: cada coluna tem um par (par embaixo, ímpar em cima) ---
PARES = [("GND", None), (52, 53), (50, 51), (48, 49), ("...", "..."), (32, 33)]
PAR_X = {0: 150, 1: 215, 2: 275, 3: 335, 4: 390, 5: 445}
Y_PAR, Y_IMPAR = 182, 152          # linhas da barra dupla
Y_PLACA, Y_PLACA_FIM = 64, 200

# --- protoboard ---
COL1_X, COL_PASSO = 110, 15
ANODOS = [3, 10, 17, 24, 31, 38, 45, 52]
BB_X, BB_Y, BB_FIM = 96, 336, 712
Y_UP = [398, 413, 428, 443, 458]
CANAL = (466, 486)
Y_LO = [494, 509, 524, 539, 554]   # E D C B A
Y_LINHA_AZUL, Y_FUROS_MENOS, Y_FUROS_MAIS, Y_LINHA_VERM = 578, 592, 610, 624

FIO, PRETO, CINZA, TINTA, RES, TEAL = "#0072b2", "#1a1a1a", "#9aa0a6", "#1a1a1a", "#d2b48c", "#0f6e68"


def COL(n):
    return COL1_X + (n - 1) * COL_PASSO


o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
  f'font-family="DejaVu Sans, Helvetica, Arial, sans-serif">')
a(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
a(f'<text x="24" y="32" font-size="19" font-weight="bold" fill="{TINTA}">Montagem do HUD, vista de cima</text>')
a(f'<text x="24" y="50" font-size="12" fill="#555">Os oito LEDs saem da barra dupla do Mega (a de 2×18, na ponta '
  f'oposta ao USB). O LED do pino D{PINO_PLACA} já vem soldado na placa.</text>')

# ---------- placa ----------
a(f'<rect x="{BB_X}" y="{Y_PLACA}" width="{PAR_X[5] + 120 - BB_X}" height="{Y_PLACA_FIM - Y_PLACA}" rx="8" '
  f'fill="{TEAL}"/>')
a(f'<text x="{BB_X + 20}" y="{Y_PLACA + 30}" font-size="16" font-weight="bold" fill="#ffffff">Arduino Mega 2560</text>')
a(f'<text x="{BB_X + 20}" y="{Y_PLACA + 50}" font-size="11" fill="#cfe9e6">barra dupla DIGITAL (22 a 53) · '
  'cada coluna tem dois pinos, um par e um ímpar</text>')
a(f'<rect x="{PAR_X[0] - 24}" y="{Y_IMPAR - 15}" width="{PAR_X[5] + 24 - PAR_X[0] + 24}" height="{Y_PAR + 15 - Y_IMPAR + 15}" '
  f'rx="3" fill="#15201f"/>')
usados = {p for p, _, _ in LEDS}
for i, (baixo, cima) in enumerate(PARES):
    x = PAR_X[i]
    for valor, y in ((cima, Y_IMPAR), (baixo, Y_PAR)):
        if valor is None:
            continue
        if valor == "...":
            a(f'<text x="{x}" y="{y + 5}" font-size="13" text-anchor="middle" fill="#8aa">…</text>')
            continue
        usado = valor in usados
        cor = "#f0c000" if usado else ("#ffffff" if valor == "GND" else "#55605f")
        larg = 34 if valor == "GND" else 18
        a(f'<rect x="{x - larg / 2}" y="{y - 9}" width="{larg}" height="18" rx="2" fill="{cor}" stroke="#0a0f0f"/>')
        a(f'<text x="{x}" y="{y + 4}" font-size="9" font-weight="bold" text-anchor="middle" '
          f'fill="{"#1a1a1a" if usado or valor == "GND" else "#9ab"}">{valor}</text>')
a(f'<text x="{PAR_X[5] + 40}" y="{Y_IMPAR + 5}" font-size="10" fill="#cfe9e6">ímpares</text>')
a(f'<text x="{PAR_X[5] + 40}" y="{Y_PAR + 5}" font-size="10" fill="#cfe9e6">pares</text>')

# ---------- protoboard ----------
bw = COL(63) - BB_X + 26
a(f'<rect x="{BB_X}" y="{BB_Y}" width="{bw}" height="{BB_FIM - BB_Y}" rx="6" fill="#f2f0eb" stroke="{CINZA}"/>')
for y, cor in ((BB_Y + 20, "#d55e00"), (BB_Y + 34, "#5b9bd5")):
    a(f'<line x1="{BB_X + 10}" y1="{y}" x2="{BB_X + bw - 10}" y2="{y}" stroke="{cor}" stroke-width="2" opacity="0.4"/>')
a(f'<text x="{BB_X + bw - 14}" y="{BB_Y + 50}" font-size="9" text-anchor="end" fill="#999">'
  'trilhos de cima: não usados</text>')
for y in Y_UP:
    for n in range(1, 64):
        a(f'<circle cx="{COL(n)}" cy="{y}" r="2" fill="#d7d3cb"/>')
a(f'<rect x="{BB_X + 10}" y="{CANAL[0]}" width="{bw - 20}" height="{CANAL[1] - CANAL[0]}" fill="#e4e0d8"/>')
for n in ANODOS:
    a(f'<text x="{COL(n) - 5}" y="{CANAL[0] + 15}" font-size="9" text-anchor="end" fill="#555">{n}</text>')
    a(f'<text x="{COL(n + 1) + 5}" y="{CANAL[0] + 15}" font-size="9" fill="#555">{n + 1}</text>')
for i, y in enumerate(Y_LO):
    a(f'<text x="{BB_X + 4}" y="{y + 4}" font-size="9" fill="#888">{"EDCBA"[i]}</text>')
    for n in range(1, 64):
        usada = n in ANODOS or (n - 1) in ANODOS
        a(f'<circle cx="{COL(n)}" cy="{y}" r="{2.6 if usada else 2}" fill="{"#6f6a60" if usada else "#d7d3cb"}"/>')

# as duas colunas do trilho de baixo, desenhadas separadas: é aí que mora o erro
a(f'<line x1="{BB_X + 10}" y1="{Y_LINHA_AZUL}" x2="{BB_X + bw - 10}" y2="{Y_LINHA_AZUL}" stroke="#5b9bd5" '
  f'stroke-width="2"/>')
a(f'<rect x="{BB_X + 10}" y="{Y_FUROS_MENOS - 9}" width="{bw - 20}" height="18" rx="4" fill="#e8f1fa" '
  f'stroke="#0072b2" stroke-width="1.6"/>')
for n in range(1, 64):
    a(f'<circle cx="{COL(n)}" cy="{Y_FUROS_MENOS}" r="2.6" fill="#6f6a60"/>')
    a(f'<circle cx="{COL(n)}" cy="{Y_FUROS_MAIS}" r="2" fill="#d7d3cb"/>')
a(f'<line x1="{BB_X + 10}" y1="{Y_LINHA_VERM}" x2="{BB_X + bw - 10}" y2="{Y_LINHA_VERM}" stroke="#d55e00" '
  f'stroke-width="2" opacity="0.5"/>')
a(f'<text x="{BB_X + 14}" y="{Y_FUROS_MENOS + 4}" font-size="10" font-weight="bold" fill="#0072b2">−</text>')
a(f'<text x="{BB_X + 14}" y="{Y_FUROS_MAIS + 4}" font-size="10" fill="#bbb">+</text>')

# ---------- jumpers, LEDs, resistores ----------
for (pino, rotulo, cor), n in zip(LEDS, ANODOS):
    i = [j for j, (b, c) in enumerate(PARES) if pino in (b, c)][0]
    xp = PAR_X[i]
    yp = Y_PAR if PARES[i][0] == pino else Y_IMPAR
    xa, xc = COL(n), COL(n + 1)
    a(f'<path d="M {xp} {yp} L {xp} {Y_PLACA_FIM + 26} L {xa} {Y_LO[0] - 46} L {xa} {Y_LO[0]}" '
      f'fill="none" stroke="{FIO}" stroke-width="2.4"/>')
    a(f'<circle cx="{xa}" cy="{Y_LO[0]}" r="3.2" fill="{FIO}"/>')
    yc = Y_LO[2]
    a(f'<line x1="{xa}" y1="{yc}" x2="{xa}" y2="{yc - 13}" stroke="{PRETO}" stroke-width="1.6"/>')
    a(f'<line x1="{xc}" y1="{yc}" x2="{xc}" y2="{yc - 9}" stroke="{PRETO}" stroke-width="1.6"/>')
    a(f'<circle cx="{(xa + xc) / 2}" cy="{yc - 17}" r="7.5" fill="{cor}" stroke="{PRETO}" stroke-width="1.2"/>')
    a(f'<text x="{xa - 6}" y="{yc - 2}" font-size="11" font-weight="bold" text-anchor="end" fill="#444">+</text>')
    # resistor: da linha A até a PRIMEIRA fileira de furos do trilho, a mesma do GND
    a(f'<line x1="{xc}" y1="{Y_LO[4]}" x2="{xc}" y2="{Y_FUROS_MENOS}" stroke="{PRETO}" stroke-width="1.6"/>')
    a(f'<rect x="{xc - 4.5}" y="{Y_LO[4] + 6}" width="9" height="20" rx="2" fill="{RES}" stroke="{PRETO}"/>')
    a(f'<circle cx="{xc}" cy="{Y_FUROS_MENOS}" r="3.2" fill="{PRETO}"/>')
    meio = (xa + xc) / 2
    a(f'<text x="{meio}" y="{BB_FIM + 28}" font-size="10.5" font-weight="bold" text-anchor="middle" '
      f'fill="{TINTA}">{rotulo}</text>')
    a(f'<text x="{meio}" y="{BB_FIM + 43}" font-size="9" text-anchor="middle" fill="#666">'
      f'D{pino} · col {n}-{n + 1}</text>')

# fio do GND, na MESMA fileira de furos dos resistores
xg = PAR_X[0]
a(f'<path d="M {xg} {Y_PAR} L {xg} {Y_PLACA_FIM + 14} L {BB_X + 30} {BB_Y - 14} L {BB_X + 30} {Y_FUROS_MENOS} '
  f'L {COL(1)} {Y_FUROS_MENOS}" fill="none" stroke="{PRETO}" stroke-width="2.6"/>')
a(f'<circle cx="{COL(1)}" cy="{Y_FUROS_MENOS}" r="3.4" fill="{PRETO}"/>')
a(f'<text x="{xg - 14}" y="{Y_PLACA_FIM + 34}" font-size="11" font-weight="bold" text-anchor="end" fill="{PRETO}">'
  'GND</text>')

# ---------- os dois avisos, na ordem em que mordem ----------
cx = BB_X + bw + 16
a(f'<rect x="{cx}" y="{Y_LO[0] - 84}" width="238" height="104" rx="6" fill="#fff6e5" stroke="#d55e00"/>')
a(f'<text x="{cx + 12}" y="{Y_LO[0] - 64}" font-size="12" font-weight="bold" fill="#a33">Polaridade: o erro nº 1</text>')
for k, linha in enumerate(["Perna LONGA (ânodo, +) na coluna",
                           "do jumper. Perna CURTA, do lado",
                           "chanfrado, na do resistor.",
                           "LED invertido não acende e não",
                           "queima: fica só apagado."]):
    a(f'<text x="{cx + 12}" y="{Y_LO[0] - 46 + k * 15}" font-size="11" fill="#444">{linha}</text>')

a(f'<rect x="{cx}" y="{Y_FUROS_MENOS - 40}" width="238" height="78" rx="6" fill="#eef4fb" stroke="#0072b2"/>')
a(f'<text x="{cx + 12}" y="{Y_FUROS_MENOS - 20}" font-size="12" font-weight="bold" fill="#05557f">'
  'O trilho tem DUAS fileiras</text>')
for k, linha in enumerate(["e elas não se tocam. Os oito",
                           "resistores e o fio de GND têm",
                           "que entrar todos na mesma."]):
    a(f'<text x="{cx + 12}" y="{Y_FUROS_MENOS - 2 + k * 15}" font-size="11" fill="#444">{linha}</text>')

a(f'<text x="{BB_X}" y="{H - 44}" font-size="12" font-weight="bold" fill="{TINTA}">O que ligar, na ordem</text>')
a(f'<text x="{BB_X}" y="{H - 26}" font-size="11" fill="#444">'
  '1. GND da placa → fileira de furos do trilho.   2. Para cada LED: perna longa na coluna do jumper, perna curta na '
  'coluna seguinte.</text>')
a(f'<text x="{BB_X}" y="{H - 10}" font-size="11" fill="#444">'
  '3. Resistor de 220 Ω dessa segunda coluna até a MESMA fileira do GND.   4. Jumper do pino da placa até a coluna da '
  'perna longa.</text>')
a('</svg>')

destino = os.path.join(RAIZ, "docs", "img", "montagem-hud.svg")
with open(destino, "w", encoding="utf-8") as f:
    f.write("\n".join(o))
print(f"{os.path.relpath(destino, RAIZ)}: {len(LEDS)} LEDs nos pinos "
      + ", ".join(str(p) for p, _, _ in LEDS))
