# Grove

Linguagem de programação em que as palavras-chave são os cheats de **GTA San Andreas**. Projeto da disciplina de Compiladores.

```
# fatorial de 5
HESOYAM n = 5;
HESOYAM r = 1;
KANGAROO (n > 1) {
    r = r * n;
    n = n - 1;
}
HELLOLADIES r;
```

| Você escreve | Significa | O cheat no jogo |
|---|---|---|
| `HESOYAM x = 1;` | declara `x` | vida e colete cheios + $250.000 |
| `TURNUPTHEHEAT (cond) { … }` | if | +2 estrelas de procurado |
| `BRINGITON (cond) { … }` | else if | 6 estrelas de procurado |
| `TURNDOWNTHEHEAT { … }` | else | zera o nível de procurado |
| `KANGAROO (cond) { … }` | while | pulo gigante |
| `GOODBYECRUELWORLD;` | break | CJ morre na hora |
| `HELLOLADIES expr;` | print | sex appeal no máximo |
| `FULLCLIP` | true | munição infinita |
| `GHOSTTOWN` | false | ruas vazias, sem carros e pedestres |

O resto é sintaxe estilo C: `{ }` delimita bloco, `;` termina instrução, `( )` agrupa, `! && ||` são os lógicos.

Tabela completa em [docs/tokens.md](docs/tokens.md); gramática em [docs/gramatica.md](docs/gramatica.md); semântica em [docs/interpretador.md](docs/interpretador.md).

## Rodar

Só precisa de Python 3.10+. Nenhuma dependência.

```bash
python -m grove examples/fatorial.cj            # executa → 120
python -m grove examples/fatorial.cj --tokens   # só a tabela de tokens
python -m grove examples/fatorial.cj --ast      # só a AST
python -m unittest                              # testes
```

Sem instalar nada: [colab/grove.py](colab/grove.py) e [colab/exemplo_grove.py](colab/exemplo_grove.py) são o mesmo front-end (léxico + sintático) em arquivo único. Cole um em cada célula do [Google Colab](https://colab.research.google.com/) e rode: sai a tabela de tokens e a AST desenhada em árvore.

## Falas do jogo

Ao rodar, o Grove toca um clipe do jogo: "MISSION PASSED" quando dá certo, "WASTED" em erro léxico, Big Smoke ("follow the damn train, CJ!") em erro sintático, CJ ("Ah shit, here we go again") em erro de execução. Os `.wav` não vêm no repositório; veja [assets/README.md](assets/README.md) para os nomes. Sem arquivo, fica em silêncio.

## Estrutura

```
grove/tokens.py    tipos de token + tabela cheat → token
grove/lexer.py     análise léxica  (texto → tokens)
grove/ast.py       nós da AST + impressão
grove/parser.py    análise sintática (tokens → AST), descida recursiva
grove/interpreter.py  back-end: executa a AST (tree-walking)
grove/sounds.py    toca assets/<evento>.wav ao compilar ou dar erro
grove/__main__.py  linha de comando
assets/            clipes .wav (não versionados)
docs/              entregáveis: tabela de tokens, gramática, semântica, storyboard do pitch
examples/          programas de exemplo (.cj)
colab/             mesmo front-end em arquivo único (grove.py + exemplo_grove.py), para colar no Colab
tests/             unittest
```
