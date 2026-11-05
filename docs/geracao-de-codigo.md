# Geração de código

`grove/codegen_py.py` traduz a AST anotada pela análise semântica ([semantica.md](semantica.md)) para **Python** legível; `grove/codegen_ino.py` traduz a mesma AST para o **C++ do Arduino**, com o LED do nível de procurado no Mega 2560.

```
AST anotada ──codegen_py──▶ Python         python -m grove arquivo.cj --python
                         └▶ Arduino (C++)  python -m grove arquivo.cj --mega [--pino N]
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
| `CJPHONEHOME` | `int(input())` |
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

## Arduino / Mega 2560

Com `--mega`, a saída é um sketch `.ino`. O corpo do programa vai todo dentro do `setup()`, porque um programa Grove roda uma vez; o `loop()` fica com o pisca-pisca. Se o programa tem uma variável **inteira** chamada `estrelas`, entra um prelúdio e cada valor novo dela muda o ritmo do LED, como o nível de procurado no jogo:

| `estrelas` | LED |
|---|---|
| 0 ou menos | apagado |
| 1 | troca a cada 600 ms |
| 2 | 300 ms |
| 3 | 200 ms |
| … | `600 / estrelas` ms, no mínimo 50 |
| 6 | 100 ms |

Depois de cada valor novo o programa espera 1,5 s, para dar tempo de ver o nível mudar. Sem essa pausa, `procurado.cj` chegaria a 6 estrelas em microssegundos. Quando o programa acaba, o `loop()` continua chamando `_tique()`, então o LED segue piscando no último nível até a placa ser reiniciada.

`CJPHONEHOME` vira `_linha()`, que espera uma linha inteira na serial, byte a byte num buffer fixo, e devolve o número. Duas consequências no prelúdio:

- **Some a pausa de 1,5 s por nível.** Ela existia para dar tempo de ver cada estrela quando o próprio programa inventava os níveis. Com alguém mandando de fora, quem dá o ritmo é a entrada.
- **O pisca-pisca não para durante a espera.** O laço que aguarda a serial chama `_tique()` a cada volta, então o LED e o giroflex continuam no ritmo do último nível enquanto a próxima linha não chega.

Um `.cj` que lê é o que liga o compilador ao GTA de verdade: ver [gta.md](gta.md).

A linguagem não muda: `examples/procurado.cj` roda na placa como está. `HELLOLADIES` sai pela serial, a 115200. Sem variável `estrelas`, a CLI avisa e sai um sketch sem prelúdio nenhum.

### O que o C não dá de graça

Três detalhes em que o alvo C++ não é uma tradução palavra por palavra do Python:

| Na Grove | No C | Por quê |
|---|---|---|
| inteiro | `long`, e todo literal leva `L` | o `int` do AVR tem 16 bits; `long` tem 32, como no alvo Python |
| `a / b`, `a % b` | `_div(a, b)`, `_mod(a, b)` | o `/` do C corta para o zero e o interpretador arredonda para baixo: `-7 / 2` é -4 na Grove e -3 no C |
| divisão por zero | `_parar("divisão por zero")` | no AVR dividir por zero é silêncio; o prelúdio avisa na serial e encerra |

`_parar`, `_div` e `_mod` só entram no sketch se o programa dividir. Strings viram `String` do Arduino, para `+` e `==` funcionarem; um literal que é operando de `+` ou `==` sai como `String("…")`, senão o C somaria ponteiros.

Trecho de `python -m grove examples/procurado.cj --mega`:

```cpp

const int _LED = 13;  // LED da placa: pisca mais rápido a cada estrela

long _ledp = 0;  // ms entre as piscadas; 0 = parado
bool _aceso = false;
unsigned long _epoca = 0, _tled = 0;  // o ritmo recomeça a cada nível novo

void _tique() {  // chamado sem parar: faz piscar quem tiver período
  unsigned long _t = millis() - _epoca;
  if (_ledp && _t / _ledp != _tled) {
    _tled = _t / _ledp;
    _aceso = !_aceso;
    digitalWrite(_LED, _aceso);
  }
}

void _inicializar() {
  pinMode(_LED, OUTPUT);
}

void _procurado(long n) {
  _ledp = n > 0 ? max(50L, 600L / n) : 0;
  _epoca = millis();
  _aceso = false;
  _tled = 0;
  digitalWrite(_LED, LOW);
  while (millis() - _epoca < 1500) {  // fica 1500 ms em cada nível, para dar para ver
    _tique();
    delay(1);
  }
}

void setup() {
  Serial.begin(115200);
  _inicializar();
  long estrelas = 0L;
  _procurado(estrelas);
  bool policia_ligada = true;
  while (true) {
    if (!policia_ligada || estrelas >= 6L) {
      break;
    }
    estrelas = estrelas + 1L;
    _procurado(estrelas);
    Serial.println(estrelas);
  }
  Serial.println("fim: ");
}

void loop() {
  _tique();  // o programa acabou, mas o último nível continua piscando
  delay(1);
}
```

Montagem, lista de compras, `arduino-cli`, simulação no Wokwi e problemas comuns: [mega2560.md](mega2560.md).

**HUD de procurado (`--hud`).** Com `--mega --hud`, o prelúdio também acende uma luz por estrela (pinos 52, 53, 50, 51, 49 e 48) e liga um giroflex vermelho e azul (pinos 33 e 32) a partir de 4 estrelas, que acelera a cada estrela. O LED da placa continua piscando. A linguagem não muda: é a mesma variável `estrelas`. Montagem e pinos em [mega2560.md](mega2560.md#7-upgrade-o-hud-de-procurado).

### Como foi testado

Em 05/11/2026 o sketch do `--mega --hud` foi gravado num Mega 2560 de verdade (clone com CH340) e a serial devolveu `1 2 3 4 5 6 fim:`, igual ao interpretador — o compilador chega à placa. Conferir os LEDs um a um ainda é olho humano. Nos testes automáticos (`tests/test_codegen.py`), o sketch é **compilado com o `g++`** contra um Arduino de mentira (`tests/arduino_falso.h`: relógio virtual, `digitalWrite` que vira log) e rodado no PC:

- **Mesma saída do interpretador** em todos os exemplos e trechos, e nos casos que separam os dois alvos: negativos em `/` e `%`, divisão por zero, soma e comparação de strings.
- **O hardware:** a sequência de períodos `[600, 300, 200, 150, 120, 100]` de `procurado.cj`, uma luz por estrela na ordem certa, o giroflex só a partir de 4 estrelas e com vermelho e azul sempre opostos.
- **Compila limpo:** `-Wall -Werror`, então parênteses faltando ou um `--3` saem como erro de teste.
