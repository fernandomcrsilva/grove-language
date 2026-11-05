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
- **Declaração vs. atribuição**: `HESOYAM x = …` cria a variável; `x = …` sem `HESOYAM` só atribui. As verificações de "variável já declarada", "não declarada" e de tipos não são da gramática: ficam na análise semântica ([semantica.md](semantica.md)).

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

Cada erro tem linha, coluna, o que era esperado e o que foi encontrado:

```
erro: linha 2, coluna 1: esperado ; (fim de instrução), encontrado 'HELLOLADIES'
```

**Todos de uma vez.** O parser não para no primeiro erro (recuperação em *modo pânico*): anota a mensagem, pula até um ponto seguro e continua. O ponto seguro é logo depois do próximo `;`, ou o começo de outra instrução (`HESOYAM`, `TURNUPTHEHEAT`, `KANGAROO`, `HELLOLADIES`, `GOODBYECRUELWORLD`, `{`), ou o `}` que fecha o bloco. No fim, `ParseError` traz a lista em `erros`. Parar no começo da próxima instrução, e não só depois de um `;`, evita erros em cascata: um `;` esquecido gera um erro, não dois.

**"Você quis dizer…?"** Os cheats são compridos, e um cheat digitado errado vira um identificador comum, com um erro confuso logo depois. Quando uma instrução começa por um nome que não é seguido de `=`, o parser compara esse nome com os nove cheats pela distância de edição (`grove/sugestao.py`: inserção, remoção, troca ou inversão de duas letras vizinhas). Se a diferença é pequena para o tamanho do cheat, a mensagem sugere o certo. `TURNDOWNTHEHEAT` e `BRINGITON` soltos também têm mensagem própria.

Saída de `python -m grove examples/erro_digitacao.cj`:

```
erro: linha 2, coluna 1: 'HESOYM' não é um cheat da Grove; você quis dizer HESOYAM?
erro: linha 4, coluna 1: 'TURNUPTHEHEET' não é um cheat da Grove; você quis dizer TURNUPTHEHEAT?
erro: linha 5, coluna 5: 'HELLOLADYS' não é um cheat da Grove; você quis dizer HELLOLADIES?
erro: linha 7, coluna 19: esperado expressão, encontrado ')'
4 erros sintáticos
```

Cheat em minúsculas tem mensagem própria: `'hesoyam' não é um cheat da Grove: os cheats são em maiúsculas (HESOYAM)`.

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
