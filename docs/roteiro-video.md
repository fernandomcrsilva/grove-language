# Vídeo tutorial — roteiro

Roteiro do vídeo tutorial da Grove, cena a cena. O vídeo é **mudo**: a informação está nas telas gravadas e nas legendas. São cerca de 4 min 36 s. Os comandos e as saídas são os reais do repositório. As legendas, já cronometradas, também estão em [legendas-video.srt](legendas-video.srt), pronto para importar no editor (CapCut, DaVinci Resolve, Premiere, Clipchamp).

> **Para o grupo:** as telas precisam ser gravações de verdade (terminal, Grove Online e a placa). Um gerador de vídeo inventaria a interface e os resultados. Use o Gemini para montar a edição, ajustar as legendas ou sugerir cortes, não para "imaginar" as telas.

---

## Instruções para o Gemini

Você vai ajudar a editar um vídeo tutorial mudo de cerca de 4 min 36 s sobre a Grove, um projeto da disciplina de Compiladores. Regras:

- **O vídeo não tem narração.** Toda a informação está nas telas gravadas e nas legendas abaixo.
- **Não invente** comandos, saídas, telas, números ou recursos. Tudo o que o vídeo mostra está escrito aqui; o que não estiver, fica de fora.
- Português do Brasil, tom de colega mostrando o projeto para a turma: direto, sem exagero de marketing.
- Uma legenda por vez, no máximo duas linhas de uns 45 caracteres, cada uma por pelo menos 3 segundos.
- Os tempos são uma sugestão: se uma tela precisa de mais tempo para ser lida, estique a cena, não corte a legenda.

**Fatos do projeto:**
- Grove é uma linguagem de programação em que as 9 palavras reservadas são cheats de GTA San Andreas. O resto da sintaxe é de C (`{ }`, `;`, `( )`, `! && ||`). Extensão `.cj`, de Carl Johnson, o protagonista.
- `HESOYAM` declara variável · `TURNUPTHEHEAT` é if · `BRINGITON` é else if · `TURNDOWNTHEHEAT` é else · `KANGAROO` é while · `GOODBYECRUELWORLD` é break · `HELLOLADIES` imprime · `FULLCLIP` é verdadeiro · `GHOSTTOWN` é falso.
- O compilador é Python puro, sem dependências (Python 3.10+). Etapas: análise léxica → sintática (descida recursiva) → semântica (tabela de símbolos e tipos) → código de três endereços (TAC) → Python. Três formas de executar: interpretador, TAC e Python gerado.
- Grove Online, o app: um compilador online no estilo do Programiz, com o tema de GTA San Andreas. Editor com realce, painel de cheats, console, abas Tokens, AST, Símbolos, TAC e Python. No canto, como o HUD do jogo: uma estrela de procurado por erro e $250.000 por missão cumprida. Cada execução termina com "Mission passed!", "Wasted", "Busted" ou "Mission failed!".
- ESP32: o compilador gera MicroPython; a variável `estrelas` faz um LED vermelho piscar mais rápido quanto maior o nível de procurado (0 a 6 estrelas).
- 78 testes automatizados; interpretador, TAC, TAC otimizada e Python deram a mesma saída em 15.000 programas aleatórios.
- O compilador mostra todos os erros sintáticos de uma vez e sugere o cheat certo quando um é digitado errado ("você quis dizer HESOYAM?"), e otimiza o código de três endereços (o exemplo otimizacao.cj vai de 13 para 4 instruções).
- Grupo: Gabriel Lacerda, Gabriel Mendonça e Fernando Mendonça. Repositório: github.com/fernandomcrsilva/grove-language

**Visual:** a marca do grupo, não a de GTA. Cores: Pinho `#12372A` (fundo das cartelas), Missão `#B7E46C` (destaque, as chaves de `{grove}`), Concreto `#F4F1E8` (texto claro), Alerta `#D95D39` (só para erros). Fonte sem serifa (Helvetica Neue, Inter ou Arial). Legenda em branco ou Concreto sobre uma faixa Pinho semitransparente, na parte de baixo.

---

## Cena 1 — Abertura · 0:00–0:12

**Na tela:** cartela em fundo Pinho, sem gravação.

**Cartela:**
- `0:00–0:03` {grove}
- `0:03–0:07` Uma linguagem com os cheats de GTA San Andreas
- `0:07–0:12` Projeto de Compiladores · Gabriel Lacerda, Gabriel Mendonça e Fernando Mendonça

## Cena 2 — A linguagem · 0:12–0:44

**Na tela:** a tabela de palavras reservadas do README; a partir de 0:30, `examples/fatorial.cj` aberto no editor.

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

**Legendas:**
- `0:12–0:16` 9 palavras reservadas, todas cheats do jogo
- `0:16–0:21` HESOYAM declara variável (no jogo, dá vida e $250.000)
- `0:21–0:26` KANGAROO é o laço (no jogo, o pulo gigante)
- `0:26–0:30` HELLOLADIES imprime na tela
- `0:30–0:36` O resto é sintaxe de C: { } delimita bloco, ; termina instrução
- `0:36–0:44` Este programa calcula o fatorial de 5

## Cena 3 — Rodando · 0:44–1:04

**Na tela:** terminal na raiz do repositório.

```bash
git clone https://github.com/fernandomcrsilva/grove-language
cd grove-language
python -m grove examples/fatorial.cj
```
```
120
```

**Legendas:**
- `0:44–0:50` Só precisa de Python 3.10 ou mais novo, sem instalar nada
- `0:50–0:56` python -m grove executa o programa
- `0:56–1:04` Saída: 120, o fatorial de 5

## Cena 4 — Por dentro: tokens, AST e símbolos · 1:04–1:48

**Na tela:** os três comandos, um depois do outro, com a saída de cada um parada na tela.

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

**Legendas:**
- `1:04–1:09` O compilador pode parar em cada etapa
- `1:09–1:20` 1. Léxico (--tokens): o texto vira tokens, com tipo, linha e coluna
- `1:20–1:32` 2. Sintático (--ast): os tokens viram a árvore do programa
- `1:32–1:48` 3. Semântico (--simbolos): cada variável, o tipo dela e onde foi declarada

## Cena 5 — Erros · 1:48–2:18

**Na tela:** `examples/erro_semantico.cj` aberto; a partir de 1:54, o terminal.

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

**Legendas:**
- `1:48–1:54` Este arquivo tem 4 erros
- `1:54–2:02` A análise semântica acha os 4 de uma vez, antes de executar
- `2:02–2:10` Cada erro vem com linha e coluna
- `2:10–2:18` String em variável inteira · condição inteira · variável inexistente · break fora de laço

## Cena 6 — Código de três endereços · 2:18–2:44

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

**Legendas:**
- `2:18–2:25` Código intermediário de três endereços (--ir)
- `2:25–2:33` No máximo uma operação por instrução
- `2:33–2:44` O KANGAROO virou rótulo + teste + goto

## Cena 7 — Python gerado · 2:44–3:10

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

**Legendas:**
- `2:44–2:51` A Grove também vira Python (--python)
- `2:51–2:58` E o Python gerado roda direto: 120 de novo
- `2:58–3:10` Interpretador, TAC e Python: a mesma saída em 15.000 programas aleatórios

## Cena 8 — Grove Online, o app · 3:10–3:52

**Na tela:** o navegador abrindo `fernandomcrsilva.github.io/grove-language/playground/`. Mostrar, nesta ordem:
1. O fatorial já rodado: `120`, "MISSION PASSED! Respect +" e o dinheiro do HUD subindo para $00250000.
2. Clicar em **KANGAROO** no painel de cheats: o laço entra no código com "condição" selecionada.
3. No menu Exemplos, `erro_semantico.cj`: os 4 erros no console, as linhas marcadas, **4 estrelas de procurado** acesas, "BUSTED", e o clique num erro levando o cursor até a linha.
4. As abas Tokens, AST, Símbolos, TAC e Python, uma por uma.
5. Clicar em **Compartilhar** ("Link copiado").

**Legendas:**
- `3:10–3:16` Grove Online: o compilador no navegador, sem instalar nada
- `3:16–3:26` Escreva, aperte Executar e veja a saída; os cheats ficam na lateral
- `3:26–3:36` Cada erro acende uma estrela de procurado; um clique leva até a linha
- `3:36–3:52` Por dentro: tokens, AST, símbolos, TAC e Python. E um link compartilha o código

## Cena 9 — ESP32 · 3:52–4:22

**Na tela:** `examples/procurado.cj`; o terminal gerando e gravando o programa; depois **filmagem da placa** com o LED piscando cada vez mais rápido e o monitor serial mostrando 1, 2, 3, 4, 5, 6. Sem a placa, a mesma cena gravada no Wokwi (ver [esp32.md](esp32.md#2-enquanto-a-placa-não-chega-wokwi)).

```bash
python -m grove examples/procurado.cj --esp32 > main.py
mpremote cp main.py :main.py
mpremote reset
```

**Legendas:**
- `3:52–3:58` E numa placa ESP32
- `3:58–4:05` --esp32 gera MicroPython para a placa
- `4:05–4:14` A variável estrelas comanda o LED: mais estrelas, pisca mais rápido
- `4:14–4:22` O mesmo procurado.cj, sem mudar uma linha

## Cena 10 — Encerramento · 4:22–4:36

**Na tela:** `python -m unittest` rodando por 3 s; depois a cartela em fundo Pinho.

```
Ran 78 tests in 0.327s

OK
```

**Cartela:**
- `4:22–4:28` 78 testes automáticos · Python puro, sem dependências
- `4:28–4:36` github.com/fernandomcrsilva/grove-language · MISSION PASSED

---

## Como gravar

- **Terminal:** fonte de 20 pt ou mais, tema escuro, janela em tela cheia, na raiz do repositório. Cole os comandos em vez de digitar, e deixe cada saída parada na tela pelo tempo da legenda.
- **Editor:** `examples/fatorial.cj` e `examples/erro_semantico.cj` abertos, com fonte grande.
- **Navegador:** o Grove Online publicado, com zoom de 125% e a janela em 1920×1080.
- **Placa:** filmagem de perto do LED, com o monitor serial visível no mesmo quadro, ou em tela dividida.
- **Som:** mudo, ou uma música de fundo sem direitos autorais (por exemplo, da Biblioteca de áudio do YouTube). Os áudios do jogo são da Rockstar: evite-os se o vídeo for publicado.

## O que gravar

- [ ] Terminal: cenas 3 a 7 e 10
- [ ] Editor com `fatorial.cj` e `erro_semantico.cj`: cenas 2 e 5
- [ ] Grove Online, na ordem da cena 8
- [ ] Placa ou Wokwi: LED acelerando + monitor serial (cena 9)
- [ ] Cartelas de abertura e encerramento (cenas 1 e 10)
