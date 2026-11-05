# Nível de procurado do GTA nos LEDs.
# O PC manda o nível (0 a 6) numa linha; CJPHONEHOME espera essa linha.
# Na placa, cada valor novo de `estrelas` acende as luzes e o giroflex.
# No terminal (sem placa): python -m grove examples/procurado_led.cj  e digite os números.
HESOYAM estrelas = 0;
KANGAROO (FULLCLIP) {
    estrelas = CJPHONEHOME;
    HELLOLADIES estrelas;
}
