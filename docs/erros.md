# Catálogo de erros

Um exemplo mínimo para **cada erro** que a Grove sabe dar, em [`examples/erros/`](../examples/erros). São os 19 erros alcançáveis pela linha de comando, levantados do código em 09/11/2026 — é uma fotografia, não um contrato: um erro novo no compilador não aparece aqui sozinho. Cada arquivo tem duas ou três linhas e provoca um erro só, para dar para ver a mensagem isolada. Os exemplos de `examples/erro_*.cj` continuam servindo ao outro propósito: mostrar vários erros de uma vez.

Rodar todos, um atrás do outro:

```bash
for f in examples/erros/*.cj; do echo "== $f"; python -m grove "$f" < /dev/null; done
```

Todo erro sai com código 1 e nada é executado — menos os de execução, que já imprimiram o que vinha antes. As mensagens abaixo são a saída real do compilador, sem o prefixo `erro: `, e o teste [`tests/test_erros.py`](../tests/test_erros.py) lê esta tabela e confere cada uma: se uma mensagem mudar e esta página não, a suíte quebra.

## Léxico

O lexer para no primeiro caractere que não souber ler.

| Erro | Exemplo | Mensagem |
|---|---|---|
| string sem fechar | [`lexico_string_sem_fechar.cj`](../examples/erros/lexico_string_sem_fechar.cj) | `linha 2, coluna 13: string sem fechar` |
| caractere fora do alfabeto | [`lexico_caractere_inesperado.cj`](../examples/erros/lexico_caractere_inesperado.cj) | `linha 2, coluna 17: caractere inesperado '$'` |

## Sintático

O parser **não** para no primeiro: anota, pula até um ponto seguro e continua ([gramatica.md](gramatica.md#todos-de-uma-vez)). Nos exemplos abaixo só há um erro em cada arquivo, de propósito.

| Erro | Exemplo | Mensagem |
|---|---|---|
| falta um token (aqui, o `;`) | [`sintatico_falta_ponto_virgula.cj`](../examples/erros/sintatico_falta_ponto_virgula.cj) | `linha 3, coluna 1: esperado ; (fim de instrução), encontrado 'HELLOLADIES'` |
| falta o nome da variável | [`sintatico_falta_nome.cj`](../examples/erros/sintatico_falta_nome.cj) | `linha 2, coluna 9: esperado identificador, encontrado '='` |
| expressão faltando | [`sintatico_esperado_expressao.cj`](../examples/erros/sintatico_esperado_expressao.cj) | `linha 2, coluna 13: esperado expressão, encontrado ';'` |
| else sem if antes | [`sintatico_else_sem_if.cj`](../examples/erros/sintatico_else_sem_if.cj) | `linha 2, coluna 1: TURNDOWNTHEHEAT sem um TURNUPTHEHEAT antes` |
| cheat digitado errado | [`sintatico_cheat_digitado_errado.cj`](../examples/erros/sintatico_cheat_digitado_errado.cj) | `linha 2, coluna 1: 'HESOYM' não é um cheat da Grove; você quis dizer HESOYAM?` |

As duas primeiras linhas são o mesmo ponto do código (`expect`), que troca o nome do token esperado: `;`, identificador, `)`, `}`, e assim por diante.

## Semântico

Aqui o compilador junta **todos** os erros antes de reclamar ([semantica.md](semantica.md)). Cada arquivo abaixo tem um só.

| Erro | Exemplo | Mensagem |
|---|---|---|
| variável não declarada | [`semantico_nao_declarada.cj`](../examples/erros/semantico_nao_declarada.cj) | `linha 2, coluna 13: variável 'respeito' não declarada` |
| nome parecido com um que existe | [`semantico_nome_parecido.cj`](../examples/erros/semantico_nome_parecido.cj) | `linha 3, coluna 13: variável 'grena' não declarada; você quis dizer 'grana'?` |
| redeclaração no mesmo escopo | [`semantico_ja_declarada.cj`](../examples/erros/semantico_ja_declarada.cj) | `linha 3, coluna 9: variável 'grana' já declarada neste escopo (linha 2)` |
| tipo errado na atribuição | [`semantico_tipo_na_atribuicao.cj`](../examples/erros/semantico_tipo_na_atribuicao.cj) | `linha 3, coluna 1: 'grana' é inteiro, não pode receber string` |
| condição não booleana | [`semantico_condicao_nao_booleana.cj`](../examples/erros/semantico_condicao_nao_booleana.cj) | `linha 3, coluna 1: condição do TURNUPTHEHEAT exige booleano, recebeu inteiro` |
| break fora de laço | [`semantico_break_fora_de_laco.cj`](../examples/erros/semantico_break_fora_de_laco.cj) | `linha 2, coluna 1: GOODBYECRUELWORLD fora de laço` |
| operador unário no tipo errado | [`semantico_unario_tipo_errado.cj`](../examples/erros/semantico_unario_tipo_errado.cj) | `linha 2, coluna 13: '!' exige booleano, recebeu inteiro` |
| os dois lados de tipos diferentes | [`semantico_tipos_incompativeis.cj`](../examples/erros/semantico_tipos_incompativeis.cj) | `linha 2, coluna 15: tipos incompatíveis para '+': inteiro e string` |
| operador que não serve para o tipo | [`semantico_operador_nao_se_aplica.cj`](../examples/erros/semantico_operador_nao_se_aplica.cj) | `linha 2, coluna 18: '<' não se aplica a string` |

## Execução

O que só dá para saber rodando. Sem linha e coluna: a TAC e o Python gerado não carregam a posição do fonte.

| Erro | Exemplo | Mensagem |
|---|---|---|
| divisão (ou resto) por zero | [`execucao_divisao_por_zero.cj`](../examples/erros/execucao_divisao_por_zero.cj) | `divisão por zero` |
| entrada acabou | [`execucao_entrada_acabou.cj`](../examples/erros/execucao_entrada_acabou.cj) | `CJPHONEHOME: a entrada acabou` |
| entrada não é um inteiro | [`execucao_entrada_nao_inteira.cj`](../examples/erros/execucao_entrada_nao_inteira.cj) | `CJPHONEHOME esperava um número inteiro, recebeu 'abc'` |

Os dois últimos precisam de entrada: rode sem `< /dev/null` e aperte Ctrl+D, ou digite `abc`.

## Avisos

Não são erros: o programa roda e sai com código 0.

| Aviso | Quando | Mensagem |
|---|---|---|
| variável nunca lida | declarada e nenhuma expressão a lê | `aviso: linha 2, coluna 9: variável 'grana' declarada e nunca lida` |
| divisão por zero escrita no fonte | `1 / 0`, com o zero literal | `aviso: linha 2, coluna 15: divisão por zero` |

O segundo vira erro de execução logo depois, quando a divisão acontece de verdade.

## Erros que a CLI nunca mostra

`grove/interpreter.py` tem as próprias checagens de variável não declarada, redeclaração, condição não booleana e tipos incompatíveis. Pela linha de comando elas são inalcançáveis: a análise semântica pega tudo isso antes. Ficam como rede de segurança para quem chama `run()` direto, sem passar pelo `check()`.
