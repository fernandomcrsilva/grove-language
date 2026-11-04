# Geração de código

`grove/codegen_py.py` traduz a AST anotada pela análise semântica ([semantica.md](semantica.md)) para **Python** legível, ou para **MicroPython** no ESP32, com o LED do nível de procurado.

```
AST anotada ──codegen_py──▶ Python         python -m grove arquivo.cj --python
                         └▶ MicroPython    python -m grove arquivo.cj --esp32 [--pino N]
```

## Por que a partir da AST e não da TAC

Python não tem `goto`. Partir da TAC ([codigo-intermediario.md](codigo-intermediario.md)) obrigaria a simular os desvios com um laço e uma variável de "próxima instrução", e o resultado seria ilegível. A AST ainda tem `if` e `while`, que viram `if` e `while` do Python. A TAC fica como representação de análise; o teste diferencial garante que as duas traduções fazem a mesma coisa.

## Correspondência

| Grove | Python |
|---|---|
| `HESOYAM x = e;` · `x = e;` | `x = e` (com o nome único da tabela de símbolos) |
| `TURNUPTHEHEAT` / `BRINGITON` / `TURNDOWNTHEHEAT` | `if` / `elif` / `else` |
| `KANGAROO (c) { … }` | `while c:` |
| `GOODBYECRUELWORLD;` | `break` |
| `HELLOLADIES e;` | `print(e)` |
| `HELLOLADIES e;` com `e` booleano | `print("FULLCLIP" if e else "GHOSTTOWN")` |
| `/` | `//` (divisão inteira, como no interpretador) |
| `&&` `\|\|` `!` | `and` `or` `not` |
| `FULLCLIP` `GHOSTTOWN` | `True` `False` |
| `"texto"` | `"texto"` |
| bloco vazio | `pass` |
| `{ … }` solto | as instruções no mesmo nível: os nomes já são únicos |

O `print` do booleano usa o **tipo estático**, gravado pela análise semântica: o gerador sabe, sem executar, que a expressão é booleana.

Variáveis com nome reservado do Python ganham `_` no fim: `if`, `None`, `print` e as outras palavras reservadas (`keyword.kwlist`). Grove aceita todas como identificador.

### Parênteses

`expr` devolve o texto e a precedência dele em Python, e um operando só ganha parênteses quando a precedência dele é menor do que o operador pede. A tabela de precedência é a do Python, não a da Grove, e as duas diferem em dois pontos:

| Grove | Python gerado | Por quê |
|---|---|---|
| `!a == b` | `(not a) == b` | em Python `not` é mais fraco que `==`: `not a == b` seria `not (a == b)` |
| `a == !b` | `a == (not b)` | `a == not b` é erro de sintaxe em Python |
| `1 == 2 == b` | `(1 == 2) == b` | Python encadeia comparação: `1 == 2 == b` seria `1 == 2 and 2 == b` |
| `10 - (4 - 3)` | `10 - (4 - 3)` | associativo à esquerda: parênteses só à direita |
| `2 + 3 * 4` | `2 + 3 * 4` | nenhum |

### Exemplo

Saída de `python -m grove examples/fizzbuzz.cj --python`:

```python
# gerado pela Grove a partir de examples/fizzbuzz.cj
i = 1
while i <= 15:
    if i % 15 == 0:
        print("FizzBuzz")
    elif i % 3 == 0:
        print("Fizz")
    elif i % 5 == 0:
        print("Buzz")
    else:
        print(i)
    i = i + 1
```

Roda direto: `python -m grove examples/fizzbuzz.cj --python | python3`.

**Diferença:** divisão por zero vira o `ZeroDivisionError` do Python, não a mensagem `divisão por zero` do interpretador.

## ESP32 / MicroPython

Com `--esp32`, a saída é MicroPython. Se o programa tem uma variável **inteira** chamada `estrelas`, entra um prelúdio com `machine.Pin` e `machine.Timer`, e cada valor novo de `estrelas` muda o pisca-pisca do LED, como o nível de procurado no jogo:

| `estrelas` | LED |
|---|---|
| 0 ou menos | apagado |
| 1 | troca a cada 600 ms |
| 2 | 300 ms |
| 3 | 200 ms |
| … | `600 // estrelas` ms, no mínimo 50 |
| 6 | 100 ms |

Depois de cada valor novo o programa espera 1,5 s, para dar tempo de ver o nível mudar. Sem essa pausa, `procurado.cj` chegaria a 6 estrelas em microssegundos. O programa não desliga o timer no fim, então o LED deve seguir piscando no último nível até a placa ser reiniciada.

A linguagem não muda: `examples/procurado.cj` roda na placa como está. `HELLOLADIES` sai pela serial. Sem variável `estrelas`, a CLI avisa e a saída é igual à do `--python`.

Trecho de `python -m grove examples/procurado.cj --esp32`:

```python
from machine import Pin, Timer
import time

_led = Pin(2, Pin.OUT)
_timer = Timer(0)


def _procurado(n):
    # 0 estrelas: LED apagado; cada estrela a mais, pisca mais rápido
    _timer.deinit()
    _led.value(0)
    if n > 0:
        _timer.init(period=max(50, 600 // n), mode=Timer.PERIODIC,
                    callback=lambda t: _led.value(not _led.value()))
    time.sleep_ms(1500)  # tempo para ver cada nível


estrelas = 0
_procurado(estrelas)
policia_ligada = True
while True:
    if not policia_ligada or estrelas >= 6:
        break
    estrelas = estrelas + 1
    _procurado(estrelas)
    print(estrelas)
print("fim: ")
```

Montagem, lista de compras, gravação na placa, simulação no Wokwi e problemas comuns: [esp32.md](esp32.md).

**HUD de procurado (`--hud`).** Com `--esp32 --hud`, o prelúdio também acende uma luz por estrela (GPIOs 32, 33, 25, 26, 27 e 14) e liga um giroflex vermelho e azul (GPIOs 18 e 19) a partir de 4 estrelas, num segundo timer que acelera a cada estrela. O LED da placa continua piscando. A linguagem não muda: é a mesma variável `estrelas`. Montagem e pinos em [esp32.md](esp32.md#7-upgrade-o-hud-de-procurado).

### Como foi testado

O ESP32 de verdade não foi testado: a validação na placa fica com o grupo. Nos testes automáticos (`tests/test_codegen.py`):

- **`machine` falso no CPython:** confere o pino, a sequência de períodos `[600, 300, 200, 150, 120, 100]` de `procurado.cj`, as pausas e a saída serial.
- **Porta unix do MicroPython**, quando está instalada (`apt install micropython`): roda o Python gerado de todos os exemplos e trechos e compara a saída com a do interpretador.
