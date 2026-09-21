# Interpretador (back-end)

`grove/interpreter.py` percorre a AST e executa cada nó diretamente (*tree-walking*). Não gera código intermediário. Um método por tipo de nó: `exec_<Nó>` para instruções, `eval_<Nó>` para expressões.

## Tipos de valor

| Tipo | Literais | Operações |
|---|---|---|
| inteiro | `42`, `-3` | `+ - * / %`, comparações; `/` é divisão inteira |
| string | `"texto"` | `+` (concatena), `==` `!=` |
| booleano | `FULLCLIP`, `GHOSTTOWN` | `!` `&&` `\|\|`, `==` `!=` |

Não há conversão implícita. `1 + "a"` é erro. `HELLOLADIES` imprime booleanos como `FULLCLIP` / `GHOSTTOWN`.

## Escopo

Cada `{ … }` cria um escopo novo, encadeado ao pai. `HESOYAM` declara no escopo atual; atribuição sem `HESOYAM` procura a variável do escopo atual para fora e altera a primeira que encontrar. Ao sair do bloco o escopo é descartado.

```
HESOYAM x = 1;
{ HESOYAM x = 2; HELLOLADIES x; }   # 2 (sombra)
HELLOLADIES x;                      # 1
{ x = 9; }
HELLOLADIES x;                      # 9
```

## Controle de fluxo

- `TURNUPTHEHEAT` / `KANGAROO` exigem condição booleana; inteiro na condição é erro.
- `&&` e `||` fazem curto-circuito: o lado direito só é avaliado se necessário.
- `GOODBYECRUELWORLD` sai do `KANGAROO` mais interno. Implementado com uma exceção interna (`BreakSignal`) capturada pelo laço.

## Erros de execução

Todos lançam `RuntimeError_` e a CLI sai com código 1:

| Situação | Mensagem |
|---|---|
| ler ou atribuir variável inexistente | `variável 'y' não declarada` |
| `HESOYAM` duas vezes no mesmo escopo | `variável 'a' já declarada neste escopo` |
| `GOODBYECRUELWORLD` fora de laço | `GOODBYECRUELWORLD fora de laço` |
| `/ 0` ou `% 0` | `divisão por zero` |
| condição não booleana | `condição do TURNUPTHEHEAT exige booleano, recebeu '1'` |
| operação entre tipos diferentes | `tipos incompatíveis para '+': '1' e 'a'` |

## Pipeline completo

```
texto ──lexer──▶ tokens ──parser──▶ AST ──interpreter──▶ saída
```

```bash
python -m grove examples/fizzbuzz.cj            # executa
python -m grove examples/fizzbuzz.cj --tokens   # para no léxico
python -m grove examples/fizzbuzz.cj --ast      # para no sintático
```
