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

## Pipeline

```
texto ─léxico─▶ tokens ─sintático─▶ AST ─semântico─▶ AST anotada + tabela de símbolos
                                                        ├─▶ interpretador  (padrão: executa)
                                                        ├─▶ TAC            (--ir)
                                                        └─▶ Python         (--python · --esp32)
```

| Etapa | Documento |
|---|---|
| léxico | [docs/tokens.md](docs/tokens.md) |
| sintático | [docs/gramatica.md](docs/gramatica.md) |
| semântico: tabela de símbolos, tipos, erros | [docs/semantica.md](docs/semantica.md) |
| interpretador | [docs/interpretador.md](docs/interpretador.md) |
| código de três endereços | [docs/codigo-intermediario.md](docs/codigo-intermediario.md) |
| Python e MicroPython (ESP32) | [docs/geracao-de-codigo.md](docs/geracao-de-codigo.md) |
| ESP32 na bancada: compras, montagem, gravação, Wokwi | [docs/esp32.md](docs/esp32.md) |
| vídeo tutorial (mudo): roteiro cena a cena e legendas | [docs/roteiro-video.md](docs/roteiro-video.md) · [docs/legendas-video.srt](docs/legendas-video.srt) |

## Rodar

Só precisa de Python 3.10+. Nenhuma dependência.

```bash
python -m grove examples/fatorial.cj              # confere e executa → 120
python -m grove examples/fatorial.cj --tokens     # só a tabela de tokens
python -m grove examples/fatorial.cj --ast        # só a AST
python -m grove examples/fatorial.cj --simbolos   # só a tabela de símbolos
python -m grove examples/fatorial.cj --ir         # só o código de três endereços
python -m grove examples/fatorial.cj --python     # o programa traduzido para Python
python -m grove examples/fatorial.cj --python | python3   # … e rodando
python -m grove examples/procurado.cj --esp32 > main.py   # MicroPython: estrelas piscam o LED
python -m unittest                                # testes
```

As flags combinam (`--tokens --ast` mostra as duas). Erro léxico, sintático, semântico ou de execução sai com código 1. `examples/erro_semantico.cj` mostra quatro erros semânticos de uma vez.

## Playground

O compilador inteiro no navegador, sem instalar nada: editor, etapas e abas com tokens, AST, tabela de símbolos, TAC, Python e a saída. É Python de verdade rodando no navegador (Pyodide).

- Publicado: <https://fernandomcrsilva.github.io/grove-language/playground/> (com o GitHub Pages ativo: *Settings → Pages → Deploy from a branch → `main` / root*)
- Local: `python -m http.server` na raiz do repositório e abrir <http://localhost:8000/playground/>
- Sem internet (apresentação numa rede que bloqueia o CDN): baixe o Pyodide uma vez e abra com `?pyodide=pyodide/`

  ```bash
  npm pack pyodide@314.0.7 && tar xzf pyodide-314.0.7.tgz && mv package playground/pyodide && rm pyodide-314.0.7.tgz
  python -m http.server        # e abrir http://localhost:8000/playground/?pyodide=pyodide/
  ```

## Colab

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fernandomcrsilva/grove-language/blob/main/colab/grove.ipynb)

O notebook tem o front-end do AP1 (léxico + sintático) em duas células: a primeira é o compilador, a segunda roda um exemplo e mostra a tabela de tokens e a AST em árvore. É gerado a partir de [colab/grove.py](colab/grove.py) e [colab/exemplo_grove.py](colab/exemplo_grove.py).

## Falas do jogo

Ao rodar, o Grove toca um clipe do jogo: "MISSION PASSED" quando dá certo, "WASTED" em erro léxico, Big Smoke ("follow the damn train, CJ!") em erro sintático, "BUSTED" em erro semântico, CJ ("Ah shit, here we go again") em erro de execução. Os `.wav` não vêm no repositório; veja [assets/README.md](assets/README.md) para os nomes. Sem arquivo, fica em silêncio.

## Estrutura

```
grove/tokens.py    tipos de token + tabela cheat → token
grove/lexer.py     análise léxica  (texto → tokens)
grove/ast.py       nós da AST + impressão
grove/parser.py    análise sintática (tokens → AST), descida recursiva
grove/semantic.py  análise semântica: tabela de símbolos, tipos, todos os erros de uma vez
grove/interpreter.py  executa a AST (tree-walking)
grove/ir.py        código de três endereços (AST → TAC) + executor de TAC
grove/codegen_py.py   gera Python / MicroPython para o ESP32 (AST → .py)
grove/sounds.py    toca assets/<evento>.wav ao compilar ou dar erro
grove/__main__.py  linha de comando
playground/        o compilador no navegador (Pyodide)
assets/            clipes .wav (não versionados)
docs/              entregáveis: tokens, gramática, semântica, interpretador, TAC, geração de código, pitch
examples/          programas de exemplo (.cj)
colab/             front-end em arquivo único + notebook do Colab (grove.ipynb, gerado por gerar_notebook.py)
tests/             unittest
```
