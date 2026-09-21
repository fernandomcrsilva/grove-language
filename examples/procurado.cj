# nível de procurado: sobe até 6 estrelas ou até a polícia desistir
HESOYAM estrelas = 0;
HESOYAM policia_ligada = FULLCLIP;
KANGAROO (FULLCLIP) {
    TURNUPTHEHEAT (!policia_ligada || estrelas >= 6) {
        GOODBYECRUELWORLD;
    }
    estrelas = estrelas + 1;
    HELLOLADIES estrelas;
}
HELLOLADIES "fim: ";
