# Código intermediário

`grove/ir.py` traduz a AST anotada pela análise semântica ([semantica.md](semantica.md)) em **código de três endereços** (TAC): uma sequência linear de instruções simples, com no máximo um operador cada, temporários (`t1`, `t2`, …) e desvios para rótulos (`L1`, `L2`, …). É a representação clássica entre a AST e o código de máquina: não tem aninhamento, escopo nem curto-circuito implícito.

```
AST anotada ──ir──▶ TAC        python -m grove arquivo.cj --ir
```

## Instruções

Cada instrução é uma quádrupla `Quad(op, arg1, arg2, result)`. Os argumentos são nomes (variável ou temporário) ou constantes; as variáveis usam o **nome único** da tabela de símbolos, porque a TAC não tem escopo de bloco.

| Forma | `op` | Significado |
|---|---|---|
| `x = a` | `=` | cópia |
| `t = a op b` | `+ - * / % == != < > <= >=` | operação binária |
| `t = !a` · `t = -a` | `!` · `neg` | operação unária |
| `print a` | `print` | `HELLOLADIES` |
| `goto L` | `goto` | desvio incondicional |
| `if a goto L` · `ifFalse a goto L` | `if` · `iffalse` | desvio se verdadeiro · se falso |
| `L:` | `label` | rótulo |

Constantes aparecem como na Grove: `5`, `"texto"`, `FULLCLIP`, `GHOSTTOWN`.

## Esquema de tradução

Um método `gen_<Nó>` por instrução e `expr` para expressões. `expr` devolve onde ficou o valor: uma constante ou uma variável não geram instrução nenhuma, e um operador gera uma instrução com destino num temporário novo.

| Grove | TAC |
|---|---|
| `HESOYAM x = e;` · `x = e;` | código de `e`, com a última instrução já escrevendo em `x` |
| `HELLOLADIES e;` | código de `e`; `print v` |
| `TURNUPTHEHEAT (c) { A } TURNDOWNTHEHEAT { B }` | `c`; `ifFalse c goto Lsenão`; `A`; `goto Lfim`; `Lsenão:`; `B`; `Lfim:` |
| sem `TURNDOWNTHEHEAT` | `c`; `ifFalse c goto Lfim`; `A`; `Lfim:` |
| `BRINGITON` | um `If` no `orelse`, que reaproveita o `Lfim` do primeiro |
| `KANGAROO (c) { A }` | `Linício:`; `c`; `ifFalse c goto Lfim`; `A`; `goto Linício`; `Lfim:` |
| `GOODBYECRUELWORLD;` | `goto Lfim` do laço mais interno (uma pilha de rótulos de laço) |
| `{ … }` solto | só as instruções de dentro: o escopo já foi resolvido pelos nomes únicos |

**Destino direto.** Numa atribuição, a última instrução da expressão já escreve na variável: `r = r * n` sai como uma instrução, não como `t1 = r * n; r = t1`.

### Curto-circuito

`&&` e `||` não são instruções da TAC: viram desvio, e o lado direito só é avaliado quando precisa.

```
a && b          t = a                 a || b          t = a
                ifFalse t goto L                      if t goto L
                t = b                                 t = b
                L:                                    L:
```

O resultado fica num temporário mesmo quando há destino, porque a variável seria escrita duas vezes: em `x = y && x`, escrever `y` em `x` antes de avaliar o lado direito leria o `x` errado.

No fim, os rótulos são renumerados na ordem em que cada um é definido na listagem.

## Exemplo: fatorial

Saída de `python -m grove examples/fatorial.cj --ir`:

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

## Exemplo: curto-circuito e break

Saída de `python -m grove examples/procurado.cj --ir`. `!policia_ligada || estrelas >= 6` vira as linhas 5–8: se a polícia está desligada, pula direto para `L2` sem comparar as estrelas. O `GOODBYECRUELWORLD` é o `goto L4` da linha 10, o fim do laço.

```
  1      estrelas = 0
  2      policia_ligada = FULLCLIP
  3  L1:
  4      ifFalse FULLCLIP goto L4
  5      t1 = !policia_ligada
  6      if t1 goto L2
  7      t1 = estrelas >= 6
  8  L2:
  9      ifFalse t1 goto L3
 10      goto L4
 11  L3:
 12      estrelas = estrelas + 1
 13      print estrelas
 14      goto L1
 15  L4:
 16      print "fim: "
```

Não há otimização: `ifFalse FULLCLIP goto L4` fica como está, mesmo sendo sempre falso.

## Executor de TAC

`execute(code)` roda a listagem: um contador de programa, um dicionário de memória e um índice rótulo → posição. Serve de **oráculo**: nos testes (`tests/test_ir.py`, `tests/test_codegen.py`), todo exemplo e todo trecho delicado (sombra, curto-circuito, `break` aninhado, negativos em `/` e `%`) dá a mesma saída no interpretador, na TAC e no Python gerado.
