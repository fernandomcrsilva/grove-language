# Análise semântica

`grove/semantic.py` confere a AST **antes** de executar ou gerar código. Um método `visit_<Nó>` por instrução e `tipo_<Nó>` por expressão, como no interpretador. Não para no primeiro erro: percorre o programa inteiro, junta todos os erros e só então levanta `SemanticError`, com os erros em ordem de posição.

```
texto ──léxico──▶ tokens ──sintático──▶ AST ──semântico──▶ AST anotada + tabela de símbolos
```

Além de conferir, a análise **anota** a AST: cada expressão ganha `tipo`, e cada `VarDecl`, `Assign` e `Var` ganha `simbolo`, a entrada da tabela de símbolos que usa. O código intermediário ([codigo-intermediario.md](codigo-intermediario.md)) e o gerador de Python ([geracao-de-codigo.md](geracao-de-codigo.md)) partem dessa AST anotada.

## Tabela de símbolos

Uma pilha de escopos, um por `{ … }` mais o global. `HESOYAM` declara no escopo do topo; ler ou atribuir procura do topo para baixo. Cada declaração vira um `Simbolo`:

| Campo | O que é |
|---|---|
| `nome` | como está no fonte |
| `tipo` | `inteiro`, `string` ou `booleano`, o do inicializador |
| `escopo` | profundidade do bloco: 0 é o global |
| `linha`, `coluna` | onde foi declarada |
| `unico` | nome sem colisão entre escopos (ver abaixo) |
| `lido` | se alguma expressão lê a variável |

Saída de `python -m grove examples/fatorial.cj --simbolos`:

```
NOME	TIPO	ESCOPO	LINHA:COL	ÚNICO	LIDA
n	inteiro	0	2:9	n	sim
r	inteiro	0	3:9	r	sim
```

### Nome único

A TAC e o Python não têm escopo de bloco. Se `{ HESOYAM x = 2; }` virasse `x = 2` em Python, sobrescreveria o `x` de fora. Por isso a primeira declaração de um nome fica com ele, e as seguintes (sombra ou bloco irmão) viram `x_1`, `x_2`, …, pulando qualquer nome que já apareça no programa.

```
HESOYAM x = 1;
{
    HESOYAM x = x + 1;
    HELLOLADIES x;
}
HELLOLADIES x;
```

```
NOME	TIPO	ESCOPO	LINHA:COL	ÚNICO	LIDA
x	inteiro	0	1:9	x	sim
x	inteiro	1	3:13	x_1	sim
```

O inicializador é conferido **antes** de declarar o nome: em `HESOYAM x = x + 1;` o `x` da direita é o de fora, como no interpretador.

## Tipos

Três tipos, sem conversão implícita. O tipo de uma variável é fixado na declaração, pelo inicializador, e não muda.

| Operador | Operandos (iguais dos dois lados) | Resultado |
|---|---|---|
| `+` | inteiro · string | o dos operandos (soma ou concatenação) |
| `-` `*` `/` `%` | inteiro | inteiro |
| `<` `>` `<=` `>=` | inteiro | booleano |
| `==` `!=` | qualquer tipo, os dois iguais | booleano |
| `&&` `\|\|` | booleano | booleano |
| `!` (unário) | booleano | booleano |
| `-` (unário) | inteiro | inteiro |

Condição de `TURNUPTHEHEAT`, `BRINGITON` e `KANGAROO` tem que ser booleana.

## Erros

Todos com linha e coluna. A CLI imprime um por linha, mais o total, e sai com código 1 sem executar nada.

| Situação | Mensagem | Aponta para |
|---|---|---|
| ler ou atribuir variável inexistente | `variável 'y' não declarada` | o nome |
| `HESOYAM` duas vezes no mesmo escopo | `variável 'a' já declarada neste escopo (linha 1)` | a segunda declaração |
| operandos de tipos diferentes | `tipos incompatíveis para '+': inteiro e string` | o operador |
| operador que não vale para o tipo | `'*' não se aplica a string` · `'!' exige booleano, recebeu inteiro` | o operador |
| atribuir outro tipo | `'x' é inteiro, não pode receber string` | o nome |
| condição não booleana | `condição do TURNUPTHEHEAT exige booleano, recebeu inteiro` | o cheat |
| `GOODBYECRUELWORLD` fora de laço | `GOODBYECRUELWORLD fora de laço` | o cheat |

**Sem cascata:** uma expressão que já deu erro ganha o tipo interno `erro`, que é aceito em qualquer lugar. Assim `HELLOLADIES y + 1 * 2;` com `y` não declarada dá um erro só, não três.

Saída de `python -m grove examples/erro_semantico.cj`:

```
erro: linha 4, coluna 1: 'grana' é inteiro, não pode receber string
erro: linha 5, coluna 1: condição do TURNUPTHEHEAT exige booleano, recebeu inteiro
erro: linha 6, coluna 17: variável 'respeito' não declarada
erro: linha 8, coluna 1: GOODBYECRUELWORLD fora de laço
4 erros semânticos
```

Erro semântico toca "BUSTED" (ver [assets/README.md](../assets/README.md)).

## Avisos

Não impedem a execução; saem em stderr, no mesmo formato.

| Situação | Mensagem |
|---|---|
| variável que nenhuma expressão lê | `variável 'x' declarada e nunca lida` |
| divisão ou resto por zero literal | `divisão por zero` |

Divisão por zero é só aviso porque o ramo pode nunca rodar. Se rodar, continua sendo erro de execução: é o único erro que sobra para depois da análise.

## O que mudou desde o AP1

No AP1 essas verificações estavam dentro do interpretador: só apareciam executando, uma por vez, e só no caminho que rodou. Agora:

| Programa | AP1 | Agora |
|---|---|---|
| `TURNUPTHEHEAT (GHOSTTOWN) { HELLOLADIES z; }` | roda sem erro (o ramo nunca executa) | `variável 'z' não declarada` |
| `HESOYAM y = 1; y = "a";` | aceito: o tipo mudava | `'y' é inteiro, não pode receber string` |
| `HELLOLADIES FULLCLIP == 1;` | imprimia `FULLCLIP` (em Python, `True == 1`) | `tipos incompatíveis para '==': booleano e inteiro` |
| `examples/erro_semantico.cj` (quatro erros) | parava no primeiro que encontrava rodando, a condição da linha 5 | mostra os quatro, sem rodar |

O interpretador não mudou e continua com as checagens dele, como rede de segurança para quem chama `run()` direto. Pela CLI, porém, todo programa passa antes pela análise semântica.
