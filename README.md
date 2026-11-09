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
| `CJPHONEHOME` | lê um inteiro da entrada | CJ liga para casa |
| `FULLCLIP` | true | munição infinita |
| `GHOSTTOWN` | false | ruas vazias, sem carros e pedestres |

O resto é sintaxe estilo C: `{ }` delimita bloco, `;` termina instrução, `( )` agrupa, `! && ||` são os lógicos.

## Pipeline

```
texto ─léxico─▶ tokens ─sintático─▶ AST ─semântico─▶ AST anotada + tabela de símbolos
                                                        ├─▶ interpretador  (padrão: executa)
                                                        ├─▶ TAC            (--ir)
                                                        └─▶ Python         (--python · --mega)
```

| Etapa | Documento |
|---|---|
| léxico | [docs/tokens.md](docs/tokens.md) |
| sintático, recuperação de erros, "você quis dizer…?" | [docs/gramatica.md](docs/gramatica.md) |
| semântico: tabela de símbolos, tipos, erros | [docs/semantica.md](docs/semantica.md) |
| interpretador | [docs/interpretador.md](docs/interpretador.md) |
| catálogo de erros: um exemplo mínimo de cada um | [docs/erros.md](docs/erros.md) |
| artigo: o projeto inteiro em texto corrido | [docs/artigo.md](docs/artigo.md) |
| código de três endereços e otimização | [docs/codigo-intermediario.md](docs/codigo-intermediario.md) |
| Python e C++ do Arduino | [docs/geracao-de-codigo.md](docs/geracao-de-codigo.md) |
| O GTA acendendo os LEDs: o cheat `CJPHONEHOME`, o script CLEO, a ponte | [docs/gta.md](docs/gta.md) |
| Mega 2560 na bancada: compras, montagem, `arduino-cli`, Wokwi, o upgrade do HUD, simulação elétrica (ngspice e EasyEDA) | [docs/mega2560.md](docs/mega2560.md) |
| vídeo tutorial (mudo): o vídeo, o roteiro cena a cena e as legendas | [docs/video-tutorial.mp4](docs/video-tutorial.mp4) · [docs/roteiro-video.md](docs/roteiro-video.md) · [docs/legendas-video.srt](docs/legendas-video.srt) |

## Rodar

Só precisa de Python 3.10+. Nenhuma dependência.

```bash
python -m grove examples/fatorial.cj              # confere e executa → 120
python -m grove examples/fatorial.cj --tokens     # só a tabela de tokens
python -m grove examples/fatorial.cj --ast        # só a AST
python -m grove examples/fatorial.cj --simbolos   # só a tabela de símbolos
python -m grove examples/fatorial.cj --ir         # só o código de três endereços
python -m grove examples/otimizacao.cj --otimizar # a TAC otimizada: 13 → 4 instruções
python -m grove examples/fatorial.cj --python     # o programa traduzido para Python
python -m grove examples/fatorial.cj --python | python3   # … e rodando
python -m grove examples/procurado.cj --mega > hud/hud.ino   # Arduino: estrelas piscam o LED
python -m grove examples/procurado.cj --mega --hud > hud/hud.ino   # … e acendem 6 luzes + o giroflex
python -m unittest                                # testes
```

As flags combinam (`--tokens --ast` mostra as duas). Erro léxico, sintático, semântico ou de execução sai com código 1. `examples/erro_semantico.cj` mostra quatro erros semânticos de uma vez, e `examples/erro_digitacao.cj` mostra os erros sintáticos todos juntos, com o cheat certo sugerido ("você quis dizer HESOYAM?").

## Grove Online (o app)

Um compilador online da Grove, no estilo do Programiz e do OnlineGDB, com o tema de GTA San Andreas. Escreva, aperte **Executar** (ou Ctrl+Enter) e veja a saída; nada é instalado, porque o próprio compilador em Python roda no navegador (Pyodide).

- **Editor** com realce dos cheats, numeração de linhas, recuo automático e as linhas com erro marcadas. O código fica salvo no navegador.
- **Cheats** na lateral: um clique insere o cheat no código, com o trecho a preencher já selecionado.
- **Console** com a saída e os erros no formato `arquivo:linha:coluna`; um clique num erro leva até a linha. Cada execução termina como no jogo: "Mission passed!", "Wasted", "Busted" ou "Mission failed!".
- **HUD**: uma estrela de procurado por erro encontrado, e $250.000 a cada missão cumprida.
- **Falas do jogo**: cada execução toca o clipe do resultado (CJ no erro de execução, "BUSTED" no semântico…), se os áudios estiverem em `assets/`; o alto-falante no canto liga e desliga.
- **Por dentro do compilador**: abas com tokens, AST, tabela de símbolos, TAC, Python e o C++ do Arduino.
- **Arquivo**: Exemplos, Abrir e Baixar `.cj`, e Compartilhar, que copia um link com o código. Um laço infinito é interrompido em 5 s, ou antes, com **Parar**.

O código do app está em `playground/`: `index.html` (a página), `estilo.css` (o tema), `app.js` (a lógica), `editor.js` (o editor com realce) e `worker.js` (o Python, fora da página). A fonte dos títulos é a Passion One, sob a licença SIL OFL (`playground/fontes/OFL.txt`); o visual se inspira no HUD do jogo, sem logos nem imagens da Rockstar.

Onde abrir:

- No ar: <https://grove.heybrain.uk/>, na Cloudflare (ver abaixo)
- Local: `python -m http.server` na raiz do repositório e abrir <http://localhost:8000/playground/>
- Sem internet (apresentação numa rede que bloqueia o CDN): baixe o Pyodide uma vez e abra com `?pyodide=pyodide/`

  ```bash
  npm pack pyodide@314.0.7 && tar xzf pyodide-314.0.7.tgz && mv package playground/pyodide && rm pyodide-314.0.7.tgz
  python -m http.server        # e abrir http://localhost:8000/playground/?pyodide=pyodide/
  ```

### Publicar na Cloudflare

O repositório já vem com a configuração (`wrangler.jsonc` e `.assetsignore`): o site é um Worker que só serve arquivos estáticos, sem servidor, e o `.assetsignore` deixa de fora tudo o que não é do site (testes, slides, a linha de comando, os áudios). Com o Node.js instalado, na raiz do repositório:

```bash
npx wrangler@4.151.3 login     # só na primeira vez: abre o navegador para entrar na conta
npx wrangler@4.151.3 deploy
```

O site no ar, <https://grove.heybrain.uk/>, foi publicado pelo painel da Cloudflare (*Workers & Pages → Create → Upload your static files*), enviando a pasta do site com os áudios em `assets/`. Pelo `wrangler`, o endereço sai como `https://grove-online.<subdomínio-da-conta>.workers.dev/`. Para usar um domínio que já está na mesma conta da Cloudflare, edite a linha `routes` do `wrangler.jsonc` e rode o `deploy` de novo: a Cloudflare cria o registro de DNS e o certificado sozinha. Outra opção é ligar este repositório do GitHub no painel (*Workers & Pages → Create → Import a repository*), que publica de novo a cada push.

## Colab

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fernandomcrsilva/grove-language/blob/main/colab/grove.ipynb)

O notebook tem o front-end do AP1 (léxico + sintático) em duas células: a primeira é o compilador, a segunda roda um exemplo e mostra a tabela de tokens e a AST em árvore. É gerado a partir de [colab/grove.py](colab/grove.py) e [colab/exemplo_grove.py](colab/exemplo_grove.py).

## Falas do jogo

Ao rodar, na linha de comando e no Grove Online, o Grove toca um clipe do jogo: "MISSION PASSED" quando dá certo, "WASTED" em erro léxico, Big Smoke ("follow the damn train, CJ!") em erro sintático, "BUSTED" em erro semântico, CJ ("Ah shit, here we go again") em erro de execução. Os `.wav` não vêm no repositório; veja [assets/README.md](assets/README.md) para os nomes. Sem arquivo, fica em silêncio.

## Estrutura

```
grove/tokens.py    tipos de token + tabela cheat → token
grove/lexer.py     análise léxica  (texto → tokens)
grove/ast.py       nós da AST + impressão
grove/parser.py    análise sintática (tokens → AST), descida recursiva
grove/semantic.py  análise semântica: tabela de símbolos, tipos, todos os erros de uma vez
grove/sugestao.py  "você quis dizer…?": o cheat ou a variável mais parecida
grove/interpreter.py  executa a AST (tree-walking)
grove/ir.py        código de três endereços (AST → TAC) + executor de TAC
grove/otimizador.py   otimização da TAC: constantes, cópias, desvios, código morto
grove/codegen_py.py   gera Python (AST → .py)
grove/codegen_ino.py  gera o C++ do Arduino para o Mega 2560 (AST → .ino)
gta/               script CLEO do jogo e a ponte que manda o nível pela USB
grove/sounds.py    toca assets/<evento>.wav ao compilar ou dar erro
grove/__main__.py  linha de comando
playground/        Grove Online, o app: compilador online no navegador (Pyodide)
assets/            clipes .wav (não versionados)
docs/              entregáveis: tokens, gramática, semântica, interpretador, TAC, geração de código, pitch
examples/          programas de exemplo (.cj)
hardware/          o circuito do HUD em SPICE + teste do programa no circuito (ngspice)
colab/             front-end em arquivo único + notebook do Colab (grove.ipynb, gerado por gerar_notebook.py)
tests/             unittest
```
