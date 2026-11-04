# código que o otimizador encolhe: python -m grove examples/otimizacao.cj --ir --otimizar
HESOYAM segundos = 60 * 60;          # vira 3600 na compilação
HESOYAM dobro = segundos * 2;        # a constante se propaga: 7200
HELLOLADIES dobro + 0;               # o + 0 some
TURNUPTHEHEAT (GHOSTTOWN) {          # nunca roda: o desvio e o bloco somem
    HELLOLADIES "nunca";
}
KANGAROO (FULLCLIP) {                # o teste do laço some: é sempre verdadeiro
    HELLOLADIES "uma vez";
    GOODBYECRUELWORLD;
}
