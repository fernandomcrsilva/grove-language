# -*- coding: utf-8 -*-
"""Desenha docs/img/esquema-hud.svg, o esquema elétrico do HUD de procurado.

    python hardware/gerar_esquema.py

Os pinos vêm de grove/codegen_ino.py, então mudar o código muda o desenho:
rode de novo depois de mexer em PINOS_ESTRELAS, PINO_VERMELHO ou PINO_AZUL.
As correntes são as do ponto de operação em hardware/testar_circuito.py.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)

from grove.codegen_ino import PINO_AZUL, PINO_PLACA, PINO_VERMELHO, PINOS_ESTRELAS  # noqa: E402

W, H = 1040, 530
X0, PASSO = 185, 95                      # primeira coluna e distância entre ramos
X_GND = X0 - 55                          # o ramo do terra fica à esquerda de todos
Y_PLACA, Y_PLACA_FIM = 58, 128           # caixa da placa
Y_PINO = 178                             # fim do rabicho do pino
Y_R, Y_R_FIM = 196, 246                  # corpo do resistor
Y_LED, Y_LED_FIM = 288, 326              # triângulo do LED
Y_TERRA = 376                            # trilho de terra

AMARELO, VERMELHO, AZUL = "#e8c547", "#d55e00", "#0072b2"
TINTA, CINZA, FIO = "#1a1a1a", "#777777", "#333333"

RAMOS = [(p, f"estrela {i + 1}", AMARELO, "13,4") for i, p in enumerate(PINOS_ESTRELAS)]
RAMOS.append((PINO_VERMELHO, "giroflex vermelho", VERMELHO, "13,8"))
RAMOS.append((PINO_AZUL, "giroflex azul", AZUL, "8,8"))

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
  f'font-family="DejaVu Sans, Helvetica, Arial, sans-serif">')
a(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
a(f'<text x="24" y="32" font-size="19" font-weight="bold" fill="{TINTA}">'
  'Esquema elétrico — HUD de procurado no Arduino Mega 2560</text>')
a(f'<text x="24" y="50" font-size="12" fill="#555">Saídas em 5 V · um resistor de 220 Ω por LED · '
  'cátodos no terra comum</text>')

# --- placa ---
a(f'<rect x="100" y="{Y_PLACA}" width="{X0 + 7 * PASSO + 40 - 100}" height="{Y_PLACA_FIM - Y_PLACA}" '
  f'rx="6" fill="none" stroke="{TINTA}" stroke-width="1.6"/>')
a(f'<text x="118" y="{Y_PLACA + 26}" font-size="14" font-weight="bold" fill="{TINTA}">Arduino Mega 2560</text>')
a(f'<text x="118" y="{Y_PLACA + 44}" font-size="10" fill="{CINZA}">ATmega2560 · cada saída em nível alto é a fonte de 5 V do seu ramo</text>')

# LED da placa, dentro da caixa: ele já vem soldado com resistor
xd = X0 + 5 * PASSO - 10
a(f'<rect x="{xd}" y="{Y_PLACA + 10}" width="212" height="50" rx="4" fill="none" stroke="{CINZA}" '
  f'stroke-dasharray="4 3"/>')
a(f'<text x="{xd + 10}" y="{Y_PLACA + 28}" font-size="11" font-weight="bold" fill="{TINTA}">'
  f'D{PINO_PLACA} → LED da placa</text>')
a(f'<text x="{xd + 10}" y="{Y_PLACA + 45}" font-size="10" fill="{CINZA}">já soldado, com resistor próprio</text>')
a(f'<text x="118" y="{Y_PLACA + 60}" font-size="10" fill="{CINZA}">'
  'o pino 5V da placa não entra neste circuito: nada aqui é alimentado por fora</text>')

# --- os oito ramos ---
for i, (pino, rotulo, cor, corrente) in enumerate(RAMOS):
    x = X0 + i * PASSO
    a(f'<line x1="{x}" y1="{Y_PLACA_FIM}" x2="{x}" y2="{Y_R}" stroke="{FIO}" stroke-width="1.6"/>')
    a(f'<circle cx="{x}" cy="{Y_PLACA_FIM}" r="3" fill="{FIO}"/>')
    largura = max(44, len(rotulo) * 5.3)
    a(f'<rect x="{x - largura / 2}" y="{Y_PINO - 44}" width="{largura}" height="30" fill="#ffffff"/>')
    a(f'<text x="{x}" y="{Y_PINO - 32}" font-size="12" font-weight="bold" text-anchor="middle" '
      f'fill="{TINTA}">D{pino}</text>')
    a(f'<text x="{x}" y="{Y_PINO - 19}" font-size="9.5" text-anchor="middle" fill="{CINZA}">{rotulo}</text>')
    # resistor (retângulo, padrão IEC/ABNT)
    a(f'<rect x="{x - 11}" y="{Y_R}" width="22" height="{Y_R_FIM - Y_R}" fill="#ffffff" stroke="{FIO}" '
      f'stroke-width="1.6"/>')
    a(f'<text x="{x + 17}" y="{Y_R + 29}" font-size="10" fill="{TINTA}">220 Ω</text>')
    a(f'<line x1="{x}" y1="{Y_R_FIM}" x2="{x}" y2="{Y_LED}" stroke="{FIO}" stroke-width="1.6"/>')
    # LED: triângulo (ânodo em cima) + barra do cátodo + duas setas de luz
    a(f'<polygon points="{x-13},{Y_LED} {x+13},{Y_LED} {x},{Y_LED_FIM}" fill="{cor}" stroke="{FIO}" '
      f'stroke-width="1.4"/>')
    a(f'<line x1="{x-13}" y1="{Y_LED_FIM}" x2="{x+13}" y2="{Y_LED_FIM}" stroke="{FIO}" stroke-width="2.2"/>')
    for k in (0, 1):
        bx, by = x + 15 + k * 9, Y_LED + 6 + k * 9
        a(f'<line x1="{bx}" y1="{by}" x2="{bx + 11}" y2="{by - 11}" stroke="{FIO}" stroke-width="1.2"/>')
        a(f'<polygon points="{bx+11},{by-11} {bx+5.5},{by-8} {bx+8},{by-5.5}" fill="{FIO}"/>')
    a(f'<text x="{x - 17}" y="{Y_LED + 12}" font-size="10" text-anchor="end" fill="{CINZA}">A</text>')
    a(f'<text x="{x - 17}" y="{Y_LED_FIM + 2}" font-size="10" text-anchor="end" fill="{CINZA}">K</text>')
    a(f'<line x1="{x}" y1="{Y_LED_FIM}" x2="{x}" y2="{Y_TERRA}" stroke="{FIO}" stroke-width="1.6"/>')
    a(f'<circle cx="{x}" cy="{Y_TERRA}" r="3" fill="{FIO}"/>')
    a(f'<text x="{x}" y="{Y_TERRA + 20}" font-size="10" text-anchor="middle" fill="{CINZA}">{corrente} mA</text>')

# --- terra comum ---
xf = X0 + 7 * PASSO
a(f'<line x1="{X_GND}" y1="{Y_TERRA}" x2="{xf + 30}" y2="{Y_TERRA}" stroke="{FIO}" stroke-width="2.2"/>')
a(f'<line x1="{X_GND}" y1="{Y_PLACA_FIM}" x2="{X_GND}" y2="{Y_TERRA}" stroke="{FIO}" stroke-width="1.6"/>')
a(f'<circle cx="{X_GND}" cy="{Y_PLACA_FIM}" r="3" fill="{FIO}"/>')
a(f'<rect x="{X_GND - 22}" y="{Y_PINO - 44}" width="44" height="16" fill="#ffffff"/>')
a(f'<text x="{X_GND}" y="{Y_PINO - 32}" font-size="12" font-weight="bold" text-anchor="middle" '
  f'fill="{TINTA}">GND</text>')
xg = (X_GND + xf + 30) / 2
a(f'<line x1="{xg}" y1="{Y_TERRA}" x2="{xg}" y2="{Y_TERRA + 46}" stroke="{FIO}" stroke-width="1.6"/>')
for k, meia in enumerate((20, 13, 6)):
    y = Y_TERRA + 46 + k * 6
    a(f'<line x1="{xg - meia}" y1="{y}" x2="{xg + meia}" y2="{y}" stroke="{FIO}" stroke-width="2"/>')

# --- rodapé ---
a(f'<text x="{X_GND}" y="{H - 28}" font-size="11" fill="{TINTA}">'
  'Corrente total: 80,1 mA com as seis estrelas acesas; no máximo 93,9 mA com o giroflex '
  '(vermelho e azul nunca conduzem juntos).</text>')
a(f'<text x="{X_GND}" y="{H - 12}" font-size="10" fill="{CINZA}">'
  'Valores do ponto de operação em hardware/hud.cir (ngspice), com os modelos de LED de hardware/leds.lib. '
  'A = ânodo (perna longa), K = cátodo.</text>')
a('</svg>')

destino = os.path.join(RAIZ, "docs", "img", "esquema-hud.svg")
with open(destino, "w", encoding="utf-8") as f:
    f.write("\n".join(o))
print(f"{os.path.relpath(destino, RAIZ)}: {len(RAMOS)} ramos, terra comum")
