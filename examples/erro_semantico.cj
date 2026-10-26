# erros semânticos: o AP1 achava um por vez, rodando; agora saem todos antes de executar
HESOYAM grana = 250000;
HESOYAM nome = "CJ";
grana = nome;                  # string numa variável inteira
TURNUPTHEHEAT (grana) {        # condição inteira, não booleana
    HELLOLADIES respeito;      # variável não declarada
}
GOODBYECRUELWORLD;             # break fora de laço
