# =====================================================================
# CÓDIGO FONTE EM GROVE PARA TESTAR
# =====================================================================
try:  # rodando como arquivo; no Colab as classes já vêm da célula anterior
    from grove import LexerGrove, ParserGrove
except ImportError:
    pass

grove_code = """
# Grove Street, home. Pelo menos era, antes de tudo dar errado.
HESOYAM respeito = 0;
HESOYAM nome = "CJ";
HESOYAM procurado = FULLCLIP;

HELLOLADIES "Ah shit, here we go again";
HELLOLADIES nome;

# Condicional: TURNUPTHEHEAT / BRINGITON / TURNDOWNTHEHEAT
TURNUPTHEHEAT (respeito >= 100) {
    HELLOLADIES "Respeito maximo no bairro";
} BRINGITON (respeito > 0 && !procurado) {
    HELLOLADIES "Subindo na vida, sem a policia atras";
} TURNDOWNTHEHEAT {
    HELLOLADIES "Comecando do zero";
}

# Laco KANGAROO com saida por GOODBYECRUELWORLD
KANGAROO (FULLCLIP) {
    respeito = respeito + 25 * 2;
    HELLOLADIES respeito;
    TURNUPTHEHEAT (respeito >= 100 || procurado == GHOSTTOWN) {
        GOODBYECRUELWORLD;
    }
}
"""

print("=====================================================================")
print("🌴 CÓDIGO FONTE GROVE ENVIADO AO COMPILADOR")
print("=====================================================================")
print(grove_code)

# 1. EXECUÇÃO DA ANÁLISE LÉXICA
lexer = LexerGrove(grove_code)
tokens = lexer.tokenize()

print("=====================================================================")
print(f"🔫 RESULTADO DA ANÁLISE LÉXICA (TABELA DE TOKENS) — {len(tokens)} tokens")
print("=====================================================================")
for t in tokens:
    print(t)

# 2. EXECUÇÃO DA ANÁLISE SINTÁTICA
parser = ParserGrove(tokens)
ast = parser.program()

print("\n=====================================================================")
print("🌳 RESULTADO DA ANÁLISE SINTÁTICA (ÁRVORE DE SINTAXE ABSTRATA - AST)")
print("=====================================================================")
print(ast)
