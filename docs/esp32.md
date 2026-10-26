# ESP32 — guia de bancada

A implementação prática: `examples/procurado.cj` roda num ESP32 e o nível de procurado vira o pisca-pisca de um LED vermelho. Quanto mais estrelas, mais rápido ele pisca. Como o código é gerado, está em [geracao-de-codigo.md](geracao-de-codigo.md#esp32--micropython); aqui está como montar, gravar e conferir.

Ordem sugerida: [comprar](#1-lista-de-compras), testar no [Wokwi](#2-enquanto-a-placa-não-chega-wokwi) enquanto a placa não chega, depois [gravar o MicroPython](#3-gravar-o-micropython-na-placa), [montar](#4-montar-o-circuito) e [rodar](#5-rodar-o-programa).

## 1. Lista de compras

| Item | Qtd. | Observação |
|---|---|---|
| Placa **ESP32 DevKit V1** (ESP32-WROOM-32, 30 pinos) | 1 | tem um LED azul no GPIO 2: dá para testar antes de montar qualquer coisa |
| Cabo USB **de dados** | 1 | micro-USB na maioria das DevKit V1 (confira o conector). Cabo só de carga é o erro mais comum: a placa acende e o computador não a enxerga |
| LED vermelho 5 mm | 2–3 | um de reserva |
| Resistor 220 Ω (330 Ω também serve) | 2–3 | protege o LED e o pino |
| Protoboard (400 ou 830 furos) | 1 | a DevKit V1 é larga: numa protoboard comum sobra pouca fileira, então ligue a placa por jumpers se preciso |
| Jumpers macho-macho | 5–10 | |

Perto do conector USB da placa há um chip conversor, **CP2102** ou **CH340**. Anote qual é: se o computador não reconhecer a placa, é o driver dele que falta.

## 2. Enquanto a placa não chega: Wokwi

O [Wokwi](https://wokwi.com) simula ESP32 com MicroPython no navegador, com LED e resistor. Serve para ensaiar a demonstração e gravar o vídeo antes do hardware chegar.

1. Abra o template oficial: <https://wokwi.com/projects/new/micropython-esp32>. Ele já vem com a placa e o MicroPython configurados.
2. Gere o programa e cole no `main.py` do Wokwi, no lugar do que estiver lá:
   ```bash
   python -m grove examples/procurado.cj --esp32
   ```
   (ou copie da aba **Python → MicroPython · ESP32** do playground)
3. Na aba `diagram.json`, **mantenha a placa como o template criou** e acrescente o LED e o resistor. Em `"parts"`:
   ```json
   { "type": "wokwi-resistor", "id": "r1", "top": 20, "left": 180, "attrs": { "value": "220" } },
   { "type": "wokwi-led", "id": "led1", "top": -40, "left": 280, "attrs": { "color": "red" } }
   ```
   E em `"connections"`:
   ```json
   [ "esp:2", "r1:1", "green", [] ],
   [ "r1:2", "led1:A", "green", [] ],
   [ "led1:C", "esp:GND.1", "black", [] ]
   ```
   `esp` é o `id` da placa no template; se lá estiver outro, use o de lá. Os pinos `2` e `GND.1` são os da ESP32-DevKitC V4, a placa que o Wokwi usa nos templates de ESP32. Se o template trouxer a DevKit V1, o pino é `D2`. Depois de colar, dá para arrastar as peças no desenho.
4. Aperte ▶. No monitor serial saem `1` a `6` e `fim: `; o LED fica apagado por 1,5 s e depois pisca cada vez mais rápido.

> Não consegui abrir o site do Wokwi do ambiente onde este guia foi escrito. Os nomes de peças e pinos vêm da documentação oficial ([wokwi-docs](https://github.com/wokwi/wokwi-docs), [wokwi-boards](https://github.com/wokwi/wokwi-boards)). Se o Wokwi reclamar de alguma conexão, refaça as ligações arrastando os fios no desenho.

## 3. Gravar o MicroPython na placa

Uma vez por placa. O jeito mais simples é pelo **Thonny** ([thonny.org](https://thonny.org)):

1. Ligue a placa no USB.
2. *Ferramentas → Opções → Interpretador*: escolha **MicroPython (ESP32)** e a porta da placa.
3. Clique em **Instalar ou atualizar o MicroPython**, escolha a variante **ESP32 / WROOM** e instale.

Pela linha de comando, com o [firmware ESP32_GENERIC](https://micropython.org/download/ESP32_GENERIC/) baixado:

```bash
pip install esptool
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-<versão>.bin
```

No Windows a porta é `COM3`, `COM4`…; no macOS, `/dev/cu.usbserial-…`. Nas versões novas do esptool o comando se chama `esptool` e as opções aceitam hífen (`erase-flash`, `write-flash`).

**Teste rápido, sem circuito:** no terminal do Thonny (ou `mpremote repl`), digite

```python
from machine import Pin
Pin(2, Pin.OUT).value(1)
```

O LED azul da placa acende. `.value(0)` apaga.

## 4. Montar o circuito

```
GPIO 2 ──[ resistor 220 Ω ]──▶|── GND
                         LED vermelho
                     (perna longa no resistor)
```

- Na DevKit V1, o GPIO 2 está marcado como **D2** na placa.
- A perna **longa** do LED (anodo, +) vai para o lado do resistor; a curta (catodo, −), para o **GND**.
- O LED azul da própria placa também está no GPIO 2: os dois vão piscar juntos, e está tudo certo.
- Para usar outro pino: `python -m grove examples/procurado.cj --esp32 --pino 4` e ligue o resistor no GPIO 4.

## 5. Rodar o programa

```bash
python -m grove examples/procurado.cj --esp32 > main.py
pip install mpremote
mpremote cp main.py :main.py     # grava na placa
mpremote reset                   # reinicia: o main.py roda sozinho
mpremote repl                    # ver a serial; Ctrl+] para sair
```

No Thonny: abra o `main.py`, *Arquivo → Salvar como → Dispositivo MicroPython*, com o nome `main.py`, e aperte o botão **EN** (reset) da placa.

**O que tem que acontecer:**

| Tempo | LED | Serial |
|---|---|---|
| 0 s | apagado (0 estrelas) | |
| 1,5 s | 1 estrela: troca a cada 600 ms | |
| 3 s | 2 estrelas: 300 ms | `1` |
| 4,5 s | 3 estrelas: 200 ms | `2` |
| 6 s | 4 estrelas: 150 ms | `3` |
| 7,5 s | 5 estrelas: 120 ms | `4` |
| 9 s | 6 estrelas: 100 ms | `5` |
| 10,5 s | continua em 100 ms | `6`, depois `fim: ` |

Cada número sai na serial 1,5 s depois de o LED mudar: o programa espera logo depois de cada valor novo de `estrelas` e só então chega ao `HELLOLADIES`.

## 6. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| O computador não mostra porta nenhuma | cabo só de carga, ou driver faltando | troque o cabo; instale o driver CP210x ou CH340, conforme o chip da placa |
| `Failed to connect` / `Connecting....` sem fim ao gravar | a placa não entrou em modo de gravação | segure o botão **BOOT** enquanto aparece `Connecting...` |
| Programa roda, LED externo não acende | LED invertido, pino errado ou GND solto | vire o LED; confira D2 e GND; teste o LED com o código do teste rápido |
| LED da placa pisca, o externo não | o resistor ou o LED está numa fileira errada da protoboard | confira se as pernas estão em fileiras ligadas entre si |
| `ImportError: no module named 'machine'` | o `main.py` rodou no computador, não na placa | grave na placa (`mpremote cp`) em vez de rodar com `python` |
| Nada aparece na serial | outra janela usando a porta | feche o Thonny antes de usar o `mpremote`, e vice-versa |

## 7. Para a entrega

- [ ] Foto do circuito montado
- [ ] Vídeo curto do LED acelerando, com a serial na tela (é a cena 9 do [roteiro do vídeo](roteiro-video.md))
- [ ] Preencher no artigo o parágrafo "Teste na placa": modelo da placa, pino usado, se o LED se comportou como na tabela da seção 5
