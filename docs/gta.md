# O GTA acendendo os LEDs

O nível de procurado do jogo sai pela USB e vira estrelas na protoboard. Três peças, cada fronteira simples: um arquivo texto e uma linha na serial.

```
NO JOGO                     NO PC                      NA PLACA
GTA San Andreas   grava   gta/ponte.py     USB       Mega 2560
script CLEO       ────▶   Python        ──"3\n"──▶   procurado_led.cj
opcode 01C0               pyserial                   compilado para C++
a cada 200 ms             procurado.txt              CJPHONEHOME lê a linha
```

| Peça | Onde roda | Arquivo | O que faz |
|---|---|---|---|
| 1. Script CLEO | dentro do GTA SA | [gta/procurado_cleo.txt](../gta/procurado_cleo.txt) | lê o nível com o opcode `01C0` e grava em `procurado.txt` a cada 200 ms |
| 2. Ponte | no PC | [gta/ponte.py](../gta/ponte.py) | vigia o arquivo e manda uma linha pela USB quando o número muda |
| 3. Programa da placa | no Mega 2560 | [examples/procurado_led.cj](../examples/procurado_led.cj) | `CJPHONEHOME` espera a linha; `estrelas` acende o HUD |

Com os 200 ms do CLEO e os 100 ms da ponte, o LED reage em até 0,3 s depois da estrela aparecer na tela.

## O cheat que faltava: `CJPHONEHOME`

Até aqui a Grove só escrevia. `CJPHONEHOME` é a primeira expressão que **lê**:

```
HESOYAM estrelas = 0;
KANGAROO (FULLCLIP) {
    estrelas = CJPHONEHOME;   # espera a próxima linha
    HELLOLADIES estrelas;
}
```

É o programa inteiro da placa. Nos dois alvos ele vira a leitura natural de cada um — `int(input())` no Python, uma linha da serial no Arduino — e por isso o **mesmo `.cj` roda no terminal e na placa**. Detalhes da tradução em [geracao-de-codigo.md](geracao-de-codigo.md).

Na placa, a pausa de 1,5 s por nível desaparece quando o programa lê: quem dá o ritmo passa a ser o jogo. E o pisca-pisca não para enquanto a linha não chega — `_linha()` fica chamando `_tique()` durante a espera.

## Sem nada ainda: só o terminal

Antes de GTA, de placa e de fio, o programa roda no computador:

```bash
python -m grove examples/procurado_led.cj
```

Digite `3`, `6`, `0` e veja a saída. `Ctrl+D` encerra (a Grove avisa que a entrada acabou). É assim que se ensaia a demonstração.

## Com a placa, sem o jogo

A ponte tem um modo `--demo` que sobe de 0 a 6 e volta, em laço. Serve para testar a fiação e para a apresentação, caso o jogo não abra no dia:

```bash
mkdir -p hud
python -m grove examples/procurado_led.cj --mega --hud > hud/hud.ino
arduino-cli compile --fqbn arduino:avr:mega:cpu=atmega2560 hud
arduino-cli upload  --fqbn arduino:avr:mega:cpu=atmega2560 -p /dev/ttyUSB0 hud
python gta/ponte.py /dev/ttyUSB0 --demo
```

A parte que vale nota — o compilador e o hardware — não depende do GTA rodar.

## Com o jogo

### Qual GTA serve

| Versão | CLEO | O que fazer |
|---|---|---|
| **Clássico 1.0** US ou EU (disco, GOG, Wine/Proton) | sim | instalar o CLEO 4.4 e pronto |
| **Steam 3.0** | sim | instalar o CLEO 4.4 e pronto — o CLEO 5 é que só aceita a 1.0 US |
| **1.01 US** | não | é a única das clássicas sem assinatura no CLEO 4; use a ponte com `--memoria` |
| **Definitive Edition** | não | não aceita CLEO nem tem endereços conhecidos; plano B é ler a tela |

O CLEO identifica a versão lendo quatro posições do executável, uma por build
conhecida (1.0 US, 1.0 EU, 1.01 EU e Steam 3.0). Executável modificado — repack,
crack, "compact exe" — não bate com nenhuma delas e o CLEO desiste de carregar,
mesmo sendo a versão certa do jogo.

### Instalar o script

1. Instale o [CLEO 4.4](https://github.com/cleolibrary/CLEO4/releases) na pasta do jogo.
2. Abra [gta/procurado_cleo.txt](../gta/procurado_cleo.txt) no [Sanny Builder](https://sannybuilder.com/) (modo SA) e compile com F6 para `procurado.cs`. Se ele reclamar da linha do `0AD9`, confira a grafia no `sascm.ini` da sua versão: há builds com `in_file`, outros com `to_file` ou `format`.
3. Copie o `.cs` para a pasta `cleo/` do jogo.
4. Entre no jogo: o arquivo `cleo/procurado.txt` passa a existir e a mudar sozinho.

### Ligar tudo, nesta ordem

```bash
python gta/ponte.py /dev/ttyUSB0 --arquivo ~/.wine/drive_c/GTA/cleo/procurado.txt
```

A ponte não precisa de biblioteca nenhuma no Linux e no macOS: sem o pyserial instalado, ela ajusta a porta com o `stty` e escreve direto. No Windows, instale o pyserial (`pip install pyserial`); no Arch, se preferir usá-lo, `sudo pacman -S python-pyserial`.

A ponte imprime cada mudança no terminal, então dá para ver se o problema é o jogo (número não muda), a ponte (não imprime) ou a placa (imprime e o LED não acende).

Com o Wine ou o Proton, o caminho do arquivo é dentro do prefixo. A ponte recebe o caminho na linha de comando justamente por isso.

### Sem CLEO: lendo a memória do jogo

Quando o CLEO não carrega (executável que ele não reconhece, 1.01 US, qualquer
outra versão), a ponte lê o nível direto da memória do processo. Não instala nada
no jogo e não depende da versão do executável.

1. Abra o jogo **de dentro da pasta dele** e carregue um save. O jogo procura
   `movies\`, `models\` e o resto na pasta de onde foi aberto:

   ```bash
   cd "/caminho/do/Grand Theft Auto San Andreas"
   wine gta-sa.exe
   ```
2. Rode a ponte com sudo (ler a memória de outro processo exige isso):

   ```bash
   sudo python gta/ponte.py /dev/ttyUSB0 --memoria
   ```

3. A ponte pede o número de estrelas. Pegue estrelas no jogo — o cheat
   `TURNUPTHEHEAT` dá duas — e digite quantas há.
4. Ela pede de novo a cada mudança. Mude o nível (mais estrelas, ou
   `TURNDOWNTHEHEAT` para zerar) e digite o número novo. Em três ou quatro
   rodadas aparece `achei o nível em 0x…`, e daí em diante o LED segue o jogo.

Como funciona: a primeira resposta faz a ponte varrer toda a memória gravável do
jogo atrás de inteiros com aquele valor (milhares de endereços). Cada mudança
descarta os que não acompanharam. Ela para quando uma mudança não elimina mais
ninguém: o que sobra são cópias do próprio nível. Calibre de novo cada vez que
abrir o jogo.

Se a ponte não achar o processo sozinha, passe `--pid` com o número que o
`pgrep -f gta-sa.exe` mostrar.

## Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| A ponte não imprime nada | o CLEO não está rodando, ou o caminho do arquivo está errado | confira se `cleo/procurado.txt` existe e muda quando você pega uma estrela |
| O jogo abre, mas nenhum script CLEO roda | o executável não é uma das builds que o CLEO reconhece | use o modo `--memoria`, que não depende do CLEO |
| `perdi o rastro do nível` | você digitou antes do nível mudar na tela, ou digitou errado | calibre de novo; responda só depois que as estrelas pararem de piscar |
| `sem permissão para ler a memória do jogo` | faltou o sudo | `sudo python gta/ponte.py … --memoria` |
| O jogo não abre no Wine: tela preta ou azul, processo parado em 0% de CPU | faltam os plugins do GStreamer que tocam os vídeos de abertura, ou o jogo foi aberto fora da pasta dele | `sudo pacman -S gst-plugins-base gst-plugins-good` e abra com `wine gta-sa.exe` de dentro da pasta do jogo |
| `não consegui configurar /dev/ttyUSB0` | placa desligada, ou você fora do grupo `uucp` | veja [mega2560.md](mega2560.md#3-instalar-o-compilador) |
| `Permission denied` na porta | você não está no grupo `uucp` | veja [mega2560.md](mega2560.md#3-instalar-o-compilador) |
| A ponte imprime, o LED não acende | fiação | veja [mega2560.md](mega2560.md#6-problemas-comuns) — comece pela polaridade do LED |
| O LED fica um nível atrasado | normal nos primeiros 2 s | abrir a porta reinicia a placa; a ponte espera o boot antes do primeiro número |
