# Pitch — storyboard (10 min)

Apresentação técnica da Grove. Uma linha por cena: o que está na tela, o que se fala, quem fala. Tempos são acumulados. Fala em tópicos, não decore texto.

Antes de começar: terminal aberto na raiz do repo, fonte grande, `.wav` na pasta `assets/` (sem eles a demo roda em silêncio, não quebra).

| # | Até | Na tela | Fala | Quem |
|---|---|---|---|---|
| 1 | 0:30 | Slide: **Grove** + nomes do grupo | Linguagem de programação em que as palavras-chave são os cheats de GTA San Andreas. Extensão `.cj` (Carl Johnson). Python puro, sem dependências. | |
| 2 | 1:30 | Print do jogo com o cheat `HESOYAM` sendo digitado | Por que cheats: todo mundo da sala já digitou HESOYAM; é um vocabulário que o público conhece. Um tema lúdico obriga a fazer o pipeline inteiro do mesmo jeito. Decisão de design: a primeira versão usava os botões do PS2 (△ ○ ×) como pontuação; trocamos por sintaxe C (`{ } ;`) para o foco ficar nos cheats e no compilador, não em digitar Unicode. | |
| 3 | 2:30 | Tabela cheat → significado (README) e `examples/fatorial.cj` ao lado | Nove palavras reservadas: `HESOYAM` declara, `TURNUPTHEHEAT` / `BRINGITON` / `TURNDOWNTHEHEAT` são if / else if / else, `KANGAROO` é while, `GOODBYECRUELWORLD` é break, `HELLOLADIES` imprime, `FULLCLIP` / `GHOSTTOWN` são true / false. Cada uma tem relação com o efeito no jogo (KANGAROO pula de novo, GOODBYECRUELWORLD mata o CJ). O resto é C: bloco, `;`, parênteses, `! && \|\|`. | |
| 4 | 3:00 | Diagrama: `texto → lexer → tokens → parser → AST → interpretador → saída` | Três estágios, um arquivo cada: `lexer.py`, `parser.py`, `interpreter.py`. A CLI para em qualquer estágio com `--tokens` ou `--ast`. | |
| 5 | 4:30 | Terminal: `python -m grove examples/fatorial.cj --tokens`; depois `python -m grove examples/erro_lexico.cj` (toca "WASTED") | Léxico: cada token tem tipo, lexema, linha e coluna. Classes: cheats (tabela de palavras), pontuação e operadores (tabela de símbolos), número, string, identificador. Detalhe: operadores de dois caracteres são testados antes dos de um, senão `!=` viraria `!` seguido de `=`. Erro léxico aponta linha e coluna. | |
| 6 | 6:30 | Slide com a EBNF de `docs/gramatica.md`; terminal: `python -m grove examples/fatorial.cj --ast`; depois `python -m grove examples/erro_sintatico.cj` (toca Big Smoke) | Sintático: descida recursiva, um método por regra da gramática. LL(1): cada regra decide olhando só o próximo token. Precedência vem da cadeia de regras (`ou → e → igualdade → comparação → termo → fator → unário → primário`), tudo associativo à esquerda por um único método genérico `binary`. Sem ambiguidade de else porque bloco é sempre `{ }`. `BRINGITON` é açúcar: vira um `If` aninhado no `orelse`. Erro sintático diz o que esperava e o que achou. | |
| 7 | 8:00 | Trecho de `grove/interpreter.py` (`exec_Block`, `eval_Binary`); terminal: `python -m grove examples/erro_execucao.cj` (toca CJ) | Interpretador tree-walking: um método `exec_`/`eval_` por nó da AST, sem código intermediário. Escopo: cada bloco cria um dicionário encadeado ao pai; sombra funciona. Tipos: inteiro, string, booleano, sem conversão implícita (`1 + "a"` é erro, `if` exige booleano). `&&` e `\|\|` com curto-circuito. `break` é uma exceção interna capturada pelo laço mais interno. Erros de execução: variável não declarada, redeclaração, divisão por zero, break fora de laço. | |
| 8 | 9:30 | Terminal: `python -m grove examples/fizzbuzz.cj` e `python -m grove examples/procurado.cj` (toca "MISSION PASSED") | Demo completa. FizzBuzz mostra if / else if / else e `%`. Procurado mostra `while` infinito com `break`, `!` e `\|\|`. Mostrar o arquivo fonte antes de rodar. | |
| 9 | 10:00 | Slide: fase 2 | Próximos passos: análise semântica separada do interpretador com tabela de erros, geração de código Python a partir da AST, MicroPython no ESP32, playground web. Perguntas. | |

## Comandos da demo, na ordem

Todos a partir da raiz do repo. Saída esperada abaixo de cada um.

```bash
python -m grove examples/fatorial.cj --tokens
```
```
LINHA:COL	TIPO	LEXEMA
2:1	VAR	HESOYAM
2:9	IDENT	n
2:11	ASSIGN	=
2:13	NUMBER	5
2:14	SEMI	;
…
```

```bash
python -m grove examples/erro_lexico.cj
```
```
erro: linha 2, coluna 13: caractere inesperado '$'
```

```bash
python -m grove examples/fatorial.cj --ast
```
Árvore indentada, um campo por linha (ver exemplo em `docs/gramatica.md`).

```bash
python -m grove examples/erro_sintatico.cj
```
```
erro: linha 3, coluna 1: esperado ; (fim de instrução), encontrado 'HELLOLADIES'
```

```bash
python -m grove examples/erro_execucao.cj
```
```
erro: divisão por zero
```

```bash
python -m grove examples/fizzbuzz.cj
```
```
1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz   (um por linha)
```

```bash
python -m grove examples/procurado.cj
```
```
1 2 3 4 5 6 fim:   (um por linha)
```

Todo erro sai com código 1; sucesso com 0 e "MISSION PASSED".

## Se algo der errado

- Som não toca: ignora, a fala não depende dele.
- Terminal travou: `python -m unittest` roda os 24 testes em menos de 1 s e prova que tudo funciona.
- Perguntaram algo da fase 2: "está planejado, ainda não implementado".
