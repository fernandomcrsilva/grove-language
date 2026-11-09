# Grove: uma linguagem de programação com os cheats de GTA San Andreas

Gabriel Lacerda · Gabriel Mendonça · Fernando Mendonça
Disciplina de Compiladores · 9 de novembro de 2026
Código: <https://github.com/fernandomcrsilva/grove-language> · App: <https://grove.heybrain.uk>

**Resumo.** Este artigo descreve a Grove, uma linguagem de programação cujas dez palavras reservadas são cheats de GTA San Andreas, e o compilador construído para ela. O compilador é escrito em Python, sem nenhuma dependência externa, e percorre o caminho completo: análise léxica, análise sintática por descida recursiva, análise semântica com tabela de símbolos, geração de código de três endereços, otimização e dois geradores de código final: Python e C++ para Arduino. O mesmo programa pode ser executado por um interpretador que percorre a árvore, pela máquina que executa o código de três endereços ou pelo Python gerado, e os três concordaram em 15.000 programas gerados aleatoriamente. O compilador também roda no navegador, por Pyodide, e o código gerado para o Arduino foi gravado num Mega 2560 ligado ao jogo, acendendo LEDs conforme o nível de procurado do jogador.

**Palavras-chave:** compiladores, análise léxica, análise sintática, análise semântica, código de três endereços, geração de código.

## 1. Introdução

Uma disciplina de Compiladores pede que o aluno percorra o pipeline inteiro, da primeira letra do arquivo-fonte até o código que a máquina executa. O conteúdo é o mesmo qualquer que seja a linguagem inventada para o exercício, mas a escolha do vocabulário muda quem consegue acompanhar: palavras-chave arbitrárias obrigam quem lê a decorar antes de entender.

A Grove troca esse vocabulário pelos cheats de GTA San Andreas. `HESOYAM`, que no jogo dá vida e $250.000, declara uma variável. `KANGAROO`, o pulo gigante, é o laço. `HELLOLADIES` imprime. Quem jogou já digitou essas palavras dezenas de vezes, então a linguagem se lê quase sem apresentação, e um tema lúdico não diminui o trabalho: o pipeline é feito do mesmo jeito. Os arquivos têm extensão `.cj`, de Carl Johnson, o protagonista do jogo.

O que foi construído:

- um compilador completo, em Python 3.10, com 2.041 linhas e **nenhuma dependência externa**, só a biblioteca padrão;
- três formas de executar o mesmo programa: interpretador sobre a árvore sintática, máquina de código de três endereços e o Python gerado;
- dois geradores de código: Python e C++ para Arduino;
- um ambiente web, o Grove Online, em que o compilador roda dentro do navegador;
- uma ponte com o jogo: o nível de procurado do GTA acende LEDs num Arduino Mega 2560.

As seções seguintes descrevem a linguagem (2), cada etapa do compilador (3), o que foi feito fora do terminal (4) e os resultados medidos (5).

## 2. A linguagem

A Grove tem dez palavras reservadas, todas cheats da versão de PC do jogo:

| Escreve-se | Significa | O cheat no jogo |
|---|---|---|
| `HESOYAM x = 1;` | declara `x` | vida e colete cheios + $250.000 |
| `TURNUPTHEHEAT (c) { }` | `if` | +2 estrelas de procurado |
| `BRINGITON (c) { }` | `else if` | 6 estrelas de procurado |
| `TURNDOWNTHEHEAT { }` | `else` | zera o nível de procurado |
| `KANGAROO (c) { }` | `while` | pulo gigante |
| `GOODBYECRUELWORLD;` | `break` | o personagem morre na hora |
| `HELLOLADIES expr;` | `print` | sex appeal no máximo |
| `CJPHONEHOME` | lê um inteiro da entrada | o personagem liga para casa |
| `FULLCLIP` | `true` | munição infinita |
| `GHOSTTOWN` | `false` | ruas vazias |

O resto da sintaxe é a do C: `{ }` delimita bloco, `;` termina instrução, `( )` agrupa, e `!`, `&&` e `||` são os operadores lógicos. Blocos são sempre obrigatórios, o que elimina a ambiguidade clássica do `else` pendente: não existe comando solto depois de um `if`.

São três tipos, inteiro, string e booleano, sem nenhuma conversão implícita. `1 + "a"` é erro, e a condição de um `if` ou de um `while` tem de ser booleana. Não há ponto flutuante, e a ausência é deliberada: o projeto mantém quatro executores obrigados a produzir a mesma saída, o que com inteiros é exato (`7 / 2` é 3 em todos) e com ponto flutuante deixaria de ser, porque o Python usa `double` de 64 bits e o microcontrolador AVR do Mega 2560 usa `float` de 32 bits emulado em software. Também não há funções definidas pelo usuário nem estruturas de dados: o escopo do trabalho é o pipeline de compilação, não a biblioteca da linguagem.

Um programa completo:

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

```
$ python -m grove examples/fatorial.cj
120
```

## 3. O compilador

O caminho do texto até a execução tem cinco etapas, uma por arquivo em `grove/`. Cada uma pode ser inspecionada pela linha de comando, com uma flag que faz o compilador parar ali e imprimir o resultado da etapa em vez de executar o programa.

### 3.1 Análise léxica

O analisador léxico (`lexer.py`, 75 linhas) transforma o texto em uma lista de tokens de cinco classes: cheat, pontuação e operador, número, string e identificador. As duas primeiras saem de tabelas; as outras, de varreduras simples. Cada token guarda linha e coluna, e é essa informação que permite a todas as etapas seguintes apontar o lugar exato de um erro.

Um detalhe de ordem importa: operadores de dois caracteres são tentados antes dos de um, senão `!=` seria lido como `!` seguido de `=`.

```
$ python -m grove examples/fatorial.cj --tokens
LINHA:COL   TIPO     LEXEMA
2:1         VAR      HESOYAM
2:9         IDENT    n
2:11        ASSIGN   =
2:13        NUMBER   5
2:14        SEMI     ;
```

### 3.2 Análise sintática

O analisador sintático (`parser.py`, 209 linhas) é uma descida recursiva direta, com um método por regra da gramática. A gramática é LL(1): cada regra decide qual alternativa seguir olhando apenas o próximo token, sem retrocesso.

A precedência dos operadores não está em tabela nenhuma: está na cadeia de regras `ou → e → igualdade → comparação → termo → fator → unário → primário`, e a associatividade à esquerda sai de um único método genérico que todas usam.

O parser **não para no primeiro erro**. Quando encontra um, anota a mensagem e entra em recuperação em modo pânico: avança até um ponto seguro (logo depois do próximo `;`, o início de outra instrução ou o `}` que fecha o bloco) e continua analisando. Parar no início da próxima instrução, e não só depois de um `;`, evita erros em cascata: um ponto e vírgula esquecido gera um erro, não dois.

Como os cheats são palavras compridas (`GOODBYECRUELWORLD` tem 17 letras), o erro mais provável de quem escreve Grove é digitar um cheat quase certo. O compilador trata esse caso: compara o identificador desconhecido com os cheats da linguagem por distância de edição de Damerau-Levenshtein, que conta inserção, remoção, substituição e também a inversão de duas letras vizinhas, e sugere o mais próximo, com uma folga proporcional ao tamanho da palavra.

```
$ python -m grove examples/erro_digitacao.cj
erro: linha 2, coluna 1: 'HESOYM' não é um cheat da Grove; você quis dizer HESOYAM?
erro: linha 4, coluna 1: 'TURNUPTHEHEET' não é um cheat da Grove; você quis dizer TURNUPTHEHEAT?
erro: linha 5, coluna 5: 'HELLOLADYS' não é um cheat da Grove; você quis dizer HELLOLADIES?
erro: linha 7, coluna 19: esperado expressão, encontrado ')'
4 erros sintáticos
```

### 3.3 Análise semântica

A análise semântica (`semantic.py`, 246 linhas) percorre a árvore antes de qualquer execução. A tabela de símbolos é uma pilha de escopos, um por bloco mais o global: declarar insere no topo, e ler ou atribuir procura do topo para baixo.

Como as representações seguintes, o código de três endereços e o Python gerado, não têm escopo de bloco, cada símbolo também recebe um **nome único**. A primeira declaração de um nome fica com ele; as seguintes, de blocos internos ou irmãos, viram `x_1`, `x_2`, e assim por diante. Sem isso, um `x` declarado dentro de um bloco sobrescreveria o `x` de fora ao virar Python.

```
$ python -m grove examples/fatorial.cj --simbolos
NOME   TIPO      ESCOPO  LINHA:COL  ÚNICO  LIDA
n      inteiro   0       2:9        n      sim
r      inteiro   0       3:9        r      sim
```

Como o parser, a análise semântica junta todos os erros antes de reclamar, em ordem de posição:

```
$ python -m grove examples/erro_semantico.cj
erro: linha 4, coluna 1: 'grana' é inteiro, não pode receber string
erro: linha 5, coluna 1: condição do TURNUPTHEHEAT exige booleano, recebeu inteiro
erro: linha 6, coluna 17: variável 'respeito' não declarada
erro: linha 8, coluna 1: GOODBYECRUELWORLD fora de laço
4 erros semânticos
```

Além de conferir, esta etapa **anota** a árvore: cada expressão ganha seu tipo e cada variável, seu símbolo. É dessa árvore anotada que partem as duas etapas seguintes.

### 3.4 Código intermediário e otimização

A representação intermediária (`ir.py`, 249 linhas) é código de três endereços em quádruplas `(operador, argumento 1, argumento 2, resultado)`: no máximo uma operação por instrução, com temporários `t1…tn` e rótulos `L1…Ln`. As estruturas de controle desaparecem, substituídas por desvios: `&&` e `||` viram desvios condicionais com curto-circuito explícito, e `GOODBYECRUELWORLD` vira um `goto` para o fim do laço.

O código de três endereços não é só impresso: ele **executa**, numa máquina própria. É isso que permite comparar o resultado dele com o do interpretador em qualquer programa.

O otimizador (`otimizador.py`, 193 linhas) aplica quatro transformações clássicas: dobra de constantes, propagação de cópias e constantes, simplificação algébrica e remoção de desvios resolvidos e de código morto. No exemplo escrito para exercitá-las, treze instruções viram quatro:

```
$ python -m grove examples/otimizacao.cj --otimizar
  1      segundos = 3600
  2      dobro = 7200
  3      print 7200
  4      print "uma vez"
# 13 → 4 instruções · 2 contas calculadas na compilação · 3 valores propagados ·
# 1 simplificação algébrica · 2 desvios resolvidos · 8 instruções mortas removidas
```

### 3.5 Geração de código

São dois alvos, e os dois partem da árvore anotada, não do código de três endereços. A razão é simples: nenhuma das duas linguagens de destino tem `goto` idiomático, e o `if`/`while` da árvore vira `if`/`while` direto, com estrutura legível.

O gerador de Python (`codegen_py.py`, 138 linhas) produz código que roda sem adaptação. A única sutileza é a divisão: `/` da Grove arredonda para baixo, então vira `//`.

```
$ python -m grove examples/fatorial.cj --python
# gerado pela Grove a partir de examples/fatorial.cj
n = 5
r = 1
while n > 1:
    r = r * n
    n = n - 1
print(r)

$ python -m grove examples/fatorial.cj --python | python3
120
```

O gerador de Arduino (`codegen_ino.py`, 342 linhas) produz C++ para o Mega 2560 e precisa resolver três diferenças da plataforma. Primeiro, o `int` do AVR tem 16 bits, então todo inteiro da Grove vira `long`. Segundo, o `/` e o `%` do C++ arredondam na direção do zero, e não para baixo como no Python, então o gerador emite funções `_div` e `_mod` próprias que corrigem o sinal. Terceiro, `CJPHONEHOME` precisa ler da serial, e a leitura não pode travar o resto: o sketch gerado chama uma rotina de tempo enquanto espera a linha chegar, para que os LEDs continuem piscando.

## 4. Fora do terminal

### 4.1 Grove Online

O mesmo compilador roda no navegador, em <https://grove.heybrain.uk>. Não há servidor compilando nada: o Pyodide, que é o CPython compilado para WebAssembly, carrega o pacote `grove` dentro da página. O editor tem realce dos cheats, numeração e marcação da linha com erro, e abas que mostram cada etapa do pipeline: tokens, árvore, tabela de símbolos, código de três endereços, Python e o C++ do Arduino.

O retorno ao usuário usa o vocabulário do jogo: cada erro encontrado acende uma estrela de procurado no canto da tela, e cada execução bem-sucedida soma $250.000.

### 4.2 Mega 2560 e a ponte com o jogo

A última etapa fecha o ciclo com o jogo que deu nome à linguagem. Um script CLEO dentro do GTA San Andreas lê o nível de procurado do jogador a cada 200 ms e grava num arquivo. No computador, `gta/ponte.py` lê esse arquivo (ou, com a opção `--memoria`, lê o valor direto da memória do processo do jogo, dispensando o CLEO) e envia o número pela porta serial a cada 100 ms. Na placa roda um programa Grove compilado para C++, que lê a linha com `CJPHONEHOME` e acende uma luz por estrela, mais um giroflex de polícia a partir de quatro estrelas.

O mesmo arquivo `.cj` serve aos dois lados: no computador, `CJPHONEHOME` lê do teclado; na placa, da serial. Medido na bancada, o LED reage em até 0,3 s depois de a estrela aparecer na tela do jogo: os 200 ms do CLEO mais os 100 ms da ponte.

## 5. Resultados

| Medida | Valor |
|---|---|
| Linhas de Python | 2.041 |
| Dependências externas | 0 |
| Testes automatizados | 100 |
| Programas aleatórios conferidos | 15.000 |
| Saídas do compilador | 4 (executa, TAC, Python, C++) |

**Concordância entre os executores.** O teste diferencial (`tests/test_aleatorio.py`) gera programas aleatórios bem tipados, com todos os operadores e com divisão por zero incluída, e compara quatro execuções: o interpretador, o código de três endereços, o código de três endereços otimizado e o Python gerado. Em 15.000 programas, as quatro saídas foram idênticas, incluindo as mensagens de erro de execução. A rodada completa leva menos de sete segundos.

**O código gerado para a placa.** O sketch produzido pelo gerador de Arduino é compilado nos testes com `g++ -Wall -Werror` contra um Arduino simulado (`tests/arduino_falso.h`, com relógio virtual e `digitalWrite` que apenas registra) e executado no computador, comparando a saída com a do interpretador. Os testes conferem também o comportamento de hardware: a sequência de períodos do pisca, uma luz por estrela na ordem correta e o giroflex ligando apenas a partir de quatro estrelas, sempre com vermelho e azul em oposição.

**Na placa de verdade.** Em 5 de novembro de 2026 o sketch foi gravado num Mega 2560 e a serial devolveu a mesma sequência que o interpretador produz para o mesmo programa. A conferência dos LEDs um a um continua sendo feita a olho.

**Erros.** O repositório traz dez programas de exemplo, cinco deles escritos para falhar, e mais dezenove exemplos mínimos, um para cada erro que o compilador sabe emitir, do caractere inesperado à entrada que acabou. Cada um é verificado por um teste que compara a mensagem com a documentada.

## 6. Conclusão

O trabalho cobriu o pipeline de compilação completo, da análise léxica à geração de código, e foi além do exercício em dois pontos que mudaram o rigor exigido. O primeiro foi manter quatro executores obrigados a concordar: isso transformou cada decisão de semântica (o arredondamento da divisão, o comportamento do curto-circuito, a ordem dos erros) em algo verificável automaticamente, e não em uma escolha de implementação isolada. O segundo foi gerar código para uma plataforma real: o microcontrolador não perdoa um `int` de 16 bits nem uma leitura bloqueante, e essas restrições apareceram como código, não como texto.

Ficaram de fora, por escolha: ponto flutuante, que quebraria a concordância exata entre o Python e o AVR; funções definidas pelo usuário; e operações de string além de concatenação e comparação.

Os caminhos naturais de continuação são o suporte a funções, que exigiria registros de ativação na representação intermediária e uma convenção de chamada nos dois geradores, e uma análise de fluxo de dados que permitisse otimizações além das locais, como eliminação de subexpressões comuns entre blocos.

## Referências

1. AHO, A. V.; LAM, M. S.; SETHI, R.; ULLMAN, J. D. **Compiladores: princípios, técnicas e ferramentas.** 2. ed. São Paulo: Pearson, 2008.
2. DAMERAU, F. J. A technique for computer detection and correction of spelling errors. **Communications of the ACM**, v. 7, n. 3, p. 171-176, 1964.
3. PYODIDE DEVELOPMENT TEAM. **Pyodide: Python distribution for the browser and Node.js based on WebAssembly.** Disponível em: <https://pyodide.org>.
4. ARDUINO. **arduino-cli: Arduino command line interface.** Disponível em: <https://arduino.github.io/arduino-cli>.
5. Repositório do projeto, com o código, os exemplos e a documentação por etapa. Disponível em: <https://github.com/fernandomcrsilva/grove-language>.
