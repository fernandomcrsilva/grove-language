# Vídeo tutorial — roteiro

Roteiro do vídeo tutorial da Grove, cena a cena: o que aparece na tela, a narração e o texto na tela. Os comandos e as saídas são os reais do repositório.

> **Para o grupo:** as telas precisam ser gravações de verdade (terminal, playground e a placa). Um gerador de vídeo inventaria a interface e os resultados. Use o Gemini para narrar, ajustar o texto ou montar a edição, não para "imaginar" as telas.

---

## Instruções para o Gemini

Você vai trabalhar com o roteiro abaixo de um vídeo tutorial de cerca de 6 minutos sobre a Grove, um projeto da disciplina de Compiladores. Regras:

- **Não invente** comandos, saídas, telas, números ou recursos. Tudo o que o vídeo mostra está escrito aqui; o que não estiver, fica de fora.
- Português do Brasil, tom de colega explicando para a turma: direto, sem exagero de marketing.
- A narração de cada cena cabe na duração indicada (cerca de 2,5 palavras por segundo).
- Os cheats se leem como as palavras em inglês que eles juntam: HELLOLADIES = "hello ladies", GOODBYECRUELWORLD = "goodbye cruel world", TURNUPTHEHEAT = "turn up the heat". HESOYAM não é palavra: lê-se de uma vez, como está escrito.

**Fatos do projeto:**
- Grove é uma linguagem de programação em que as 9 palavras reservadas são cheats de GTA San Andreas. O resto da sintaxe é de C (`{ }`, `;`, `( )`, `! && ||`). Extensão `.cj`, de Carl Johnson, o protagonista.
- `HESOYAM` declara variável · `TURNUPTHEHEAT` é if · `BRINGITON` é else if · `TURNDOWNTHEHEAT` é else · `KANGAROO` é while · `GOODBYECRUELWORLD` é break · `HELLOLADIES` imprime · `FULLCLIP` é verdadeiro · `GHOSTTOWN` é falso.
- O compilador é Python puro, sem dependências (Python 3.10+). Etapas: análise léxica → sintática (descida recursiva) → semântica (tabela de símbolos e tipos) → código de três endereços (TAC) → Python. Três formas de executar: interpretador, TAC e Python gerado.
- Playground web: o compilador inteiro no navegador, com abas Saída, Tokens, AST, Símbolos, TAC e Python.
- ESP32: o compilador gera MicroPython; a variável `estrelas` faz um LED vermelho piscar mais rápido quanto maior o nível de procurado (0 a 6 estrelas).
- 62 testes automatizados; interpretador, TAC e Python deram a mesma saída em 15.000 programas aleatórios.
- Grupo: Gabriel Lacerda, Gabriel Mendonça e Fernando Mendonça. Repositório: github.com/fernandomcrsilva/grove-language

---

## Cena 1 — Abertura · 0:00–0:25

**Na tela:** a marca `{grove}` sobre fundo verde-escuro; depois o nome dos três integrantes.

**Narração:** E aí! Essa é a Grove, uma linguagem de programação em que as palavras-chave são os cheats do GTA San Andreas. Neste vídeo a gente mostra como escrever um programa, como o compilador funciona por dentro, e como rodar tudo no navegador e numa placa ESP32.

**Texto na tela:** Grove · Projeto de Compiladores · Gabriel Lacerda, Gabriel Mendonça, Fernando Mendonça

## Cena 2 — A linguagem · 0:25–1:05

**Na tela:** a tabela de palavras reservadas do README; depois `examples/fatorial.cj` aberto no editor.

```
# fatorial de 5 → 120
HESOYAM n = 5;
HESOYAM r = 1;
KANGAROO (n > 1) {
    r = r * n;
    n = n - 1;
}
HELLOLADIES r;
```

**Narração:** São nove palavras reservadas, cada uma com a ver com o efeito do cheat no jogo. HESOYAM, que no jogo te dá vida e dinheiro, aqui dá um valor para a variável. KANGAROO, o pulo gigante, é o laço: pula de novo, de novo e de novo. HELLOLADIES imprime. O resto é igual a C: chaves, ponto e vírgula e parênteses. Esse programa calcula o fatorial de cinco.

**Texto na tela:** HESOYAM = declarar · KANGAROO = while · HELLOLADIES = print

## Cena 3 — Rodando · 1:05–1:35

**Na tela:** terminal na raiz do repositório.

```bash
git clone https://github.com/fernandomcrsilva/grove-language
cd grove-language
python -m grove examples/fatorial.cj
```
```
120
```

**Narração:** Para rodar, só precisa de Python 3.10 ou mais novo, sem instalar nenhuma biblioteca. Clona o repositório e chama python traço m grove com o arquivo. Saiu cento e vinte, o fatorial de cinco.

**Texto na tela:** Só Python 3.10+, sem dependências

## Cena 4 — Por dentro: tokens, AST e símbolos · 1:35–2:30

**Na tela:** os três comandos, um depois do outro, com pausa em cada saída.

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
python -m grove examples/fatorial.cj --ast
```
(árvore indentada: `Program`, `VarDecl`, `While`, `Binary`…)

```bash
python -m grove examples/fatorial.cj --simbolos
```
```
NOME	TIPO	ESCOPO	LINHA:COL	ÚNICO	LIDA
n	inteiro	0	2:9	n	sim
r	inteiro	0	3:9	r	sim
```

**Narração:** Dá para parar o compilador em qualquer etapa. Com traço traço tokens, vemos a análise léxica: cada pedaço do texto vira um token, com tipo, linha e coluna. Com traço traço ast, a análise sintática monta a árvore do programa. E com traço traço símbolos, a análise semântica mostra a tabela de símbolos: cada variável, o tipo dela e onde foi declarada.

**Texto na tela:** léxico → sintático → semântico

## Cena 5 — Erros · 2:30–3:10

**Na tela:** `examples/erro_semantico.cj` aberto; depois o terminal.

```bash
python -m grove examples/erro_semantico.cj
```
```
erro: linha 4, coluna 1: 'grana' é inteiro, não pode receber string
erro: linha 5, coluna 1: condição do TURNUPTHEHEAT exige booleano, recebeu inteiro
erro: linha 6, coluna 17: variável 'respeito' não declarada
erro: linha 8, coluna 1: GOODBYECRUELWORLD fora de laço
4 erros semânticos
```

**Narração:** A análise semântica confere o programa antes de executar. Esse arquivo tem quatro erros: uma string numa variável inteira, uma condição que não é verdadeiro ou falso, uma variável que não existe e um break fora de laço. O compilador mostra os quatro de uma vez, com linha e coluna, sem rodar nada. E toca o "BUSTED" do jogo.

**Texto na tela:** 4 erros, antes de executar

## Cena 6 — Código de três endereços · 3:10–3:45

**Na tela:**

```bash
python -m grove examples/fatorial.cj --ir
```
```
  1      n = 5
  2      r = 1
  3  L1:
  4      t1 = n > 1
  5      ifFalse t1 goto L2
  6      r = r * n
  7      n = n - 1
  8      goto L1
  9  L2:
 10      print r
```

**Narração:** Depois da análise, o compilador gera código intermediário de três endereços: instruções simples, com no máximo uma operação cada. O while virou um rótulo, um teste e um goto, que é como uma máquina de verdade faz laço.

**Texto na tela:** while = rótulo + teste + goto

## Cena 7 — Python gerado · 3:45–4:15

**Na tela:**

```bash
python -m grove examples/fatorial.cj --python
```
```python
# gerado pela Grove a partir de examples/fatorial.cj
n = 5
r = 1
while n > 1:
    r = r * n
    n = n - 1
print(r)
```
```bash
python -m grove examples/fatorial.cj --python | python3
```
```
120
```

**Narração:** E o compilador também traduz Grove para Python. O código sai legível e roda direto no Python: de novo, cento e vinte. Interpretador, código de três endereços e Python dão sempre a mesma saída, e os testes conferem isso em quinze mil programas aleatórios.

**Texto na tela:** mesma saída nos três executores

## Cena 8 — Playground · 4:15–5:05

**Na tela:** o navegador abrindo `fernandomcrsilva.github.io/grove-language/playground/`. Mostrar, nesta ordem:
1. O fatorial já rodado: "MISSION PASSED! Respect +" e `120`.
2. As abas Tokens, AST, Símbolos, TAC e Python, uma por uma.
3. No menu Exemplos, `erro_semantico.cj`: os 4 erros, as linhas marcadas em vermelho, e o clique num erro levando o cursor até a linha.
4. Digitar `KANGAROO (FULLCLIP) { }` e Executar: depois de 5 segundos, "tempo esgotado", e a página continua funcionando.

**Narração:** Tudo isso também roda no navegador, sem instalar nada. O playground mostra todas as etapas lado a lado: a saída, os tokens, a árvore, a tabela de símbolos, o código de três endereços e o Python. Os erros aparecem enquanto você digita, e um clique leva até a linha. E se alguém escrever um laço infinito, a página não trava: depois de cinco segundos o programa é interrompido.

**Texto na tela:** fernandomcrsilva.github.io/grove-language/playground

## Cena 9 — ESP32 · 5:05–5:45

**Na tela:** `examples/procurado.cj`; o terminal gerando e gravando o programa; depois **filmagem da placa** com o LED piscando cada vez mais rápido e o monitor serial mostrando 1, 2, 3, 4, 5, 6.

```bash
python -m grove examples/procurado.cj --esp32 > main.py
mpremote cp main.py :main.py
mpremote reset
```

**Narração:** Por último, o ESP32. Esse programa sobe o nível de procurado de zero a seis estrelas, como no jogo. Com traço traço esp32, o compilador gera MicroPython, e a variável estrelas comanda um LED vermelho: quanto mais estrelas, mais rápido ele pisca. É o mesmo programa, sem mudar uma linha.

**Texto na tela:** mais estrelas = pisca mais rápido

## Cena 10 — Encerramento · 5:45–6:05

**Na tela:** `python -m unittest` rodando; depois o endereço do repositório.

```
Ran 62 tests in 0.266s

OK
```

**Narração:** São sessenta e dois testes automáticos, e o código, os exemplos e a documentação de cada etapa estão no GitHub. Valeu, e MISSION PASSED!

**Texto na tela:** github.com/fernandomcrsilva/grove-language

---

## O que gravar

- [ ] Terminal com fonte grande, tema escuro, na raiz do repositório: cenas 3 a 7 e 10
- [ ] `examples/fatorial.cj` e `examples/erro_semantico.cj` abertos num editor: cenas 2 e 5
- [ ] Navegador no playground publicado, na ordem da cena 8
- [ ] A placa: LED piscando de perto + o monitor serial (cena 9) — só depois da montagem
- [ ] (opcional) os `.wav` em `assets/` para o "BUSTED" e o "MISSION PASSED" saírem no áudio
