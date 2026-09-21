# Gramática

Notação EBNF. `{ x }` = zero ou mais, `[ x ]` = opcional, `|` = alternativa. Terminais entre aspas; `IDENT`, `NUMBER`, `STRING` vêm do léxico (ver [tokens.md](tokens.md)).

```ebnf
programa     = { declaracao } EOF ;

declaracao   = varDecl | instrucao ;
varDecl      = "HESOYAM" IDENT "=" expressao ";" ;

instrucao    = seStmt
             | enquantoStmt
             | printStmt
             | breakStmt
             | bloco
             | atribuicao ;

seStmt       = "TURNUPTHEHEAT" "(" expressao ")" bloco
             [ "BRINGITON" "(" expressao ")" bloco { "BRINGITON" "(" expressao ")" bloco } ]
             [ "TURNDOWNTHEHEAT" bloco ] ;
enquantoStmt = "KANGAROO" "(" expressao ")" bloco ;
printStmt    = "HELLOLADIES" expressao ";" ;
breakStmt    = "GOODBYECRUELWORLD" ";" ;
bloco        = "{" { declaracao } "}" ;
atribuicao   = IDENT "=" expressao ";" ;

(* expressões, da menor para a maior precedência; todas associativas à esquerda *)
expressao    = ou ;
ou           = e { "||" e } ;
e            = igualdade { "&&" igualdade } ;
igualdade    = comparacao { ( "==" | "!=" ) comparacao } ;
comparacao   = termo { ( "<" | ">" | "<=" | ">=" ) termo } ;
termo        = fator { ( "+" | "-" ) fator } ;
fator        = unario { ( "*" | "/" | "%" ) unario } ;
unario       = ( "!" | "-" ) unario | primario ;
primario     = NUMBER | STRING | "FULLCLIP" | "GHOSTTOWN" | IDENT
             | "(" expressao ")" ;
```

## Precedência (da mais alta para a mais baixa)

1. `(…)` (agrupamento), literais, identificadores
2. `!` `-` (unários, prefixo)
3. `*` `/` `%`
4. `+` `-`
5. `<` `>` `<=` `>=`
6. `==` `!=`
7. `&&` (e)
8. `||` (ou)

## Propriedades

- **LL(1)**: cada regra decide a alternativa olhando só o próximo token. O parser (`grove/parser.py`) é uma descida recursiva direta: um método por regra.
- **Sem ambiguidade de else**: o bloco do `TURNUPTHEHEAT` é sempre delimitado por `{ … }`, então o `TURNDOWNTHEHEAT` sempre pertence ao `TURNUPTHEHEAT` imediatamente anterior.
- **`BRINGITON` é açúcar**: `A BRINGITON B` gera a mesma AST que `A TURNDOWNTHEHEAT TURNUPTHEHEAT B` (um `If` aninhado em `orelse`). As duas formas são aceitas.
- **Declaração vs. atribuição**: `HESOYAM x = …` cria a variável; `x = …` sem `HESOYAM` só atribui. A verificação de "variável já declarada" é semântica e fica para a próxima etapa.

## Nós da AST

Definidos em `grove/ast.py` como `dataclass`es:

| Nó | Campos | Produzido por |
|---|---|---|
| `Program` | `body: list` | `programa` |
| `VarDecl` | `name, value` | `varDecl` |
| `Assign` | `name, value` | `atribuicao` |
| `If` | `cond, then: Block, orelse: Block \| If \| None` | `seStmt` |
| `While` | `cond, body: Block` | `enquantoStmt` |
| `Print` | `value` | `printStmt` |
| `Break` | | `breakStmt` |
| `Block` | `stmts: list` | `bloco` |
| `Binary` | `left, op: str, right` | `ou` … `fator` |
| `Unary` | `op: str, operand` | `unario` |
| `Literal` | `value: int \| str \| bool` | `primario` |
| `Var` | `name` | `primario` |

## Erros sintáticos

`ParseError` com linha, coluna, o que era esperado e o que foi encontrado:

```
erro: linha 2, coluna 1: esperado ; (fim de instrução), encontrado 'HELLOLADIES'
```

## Exemplo de AST

Entrada:

```
HESOYAM n = 5;
KANGAROO (n > 1) {
    n = n - 1;
}
```

Saída de `python -m grove arquivo.cj --ast`:

```
Program
  body:
    VarDecl
      name: 'n'
      value:
        Literal
          value: 5
    While
      cond:
        Binary
          left:
            Var
              name: 'n'
          op: '>'
          right:
            Literal
              value: 1
      body:
        Block
          stmts:
            Assign
              name: 'n'
              value:
                Binary
                  left:
                    Var
                      name: 'n'
                  op: '-'
                  right:
                    Literal
                      value: 1
```
