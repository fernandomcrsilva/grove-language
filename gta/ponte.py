"""Ponte entre o GTA San Andreas e a placa: lê o nível de procurado e manda pela USB.

    python gta/ponte.py /dev/ttyUSB0 --arquivo ~/.wine/.../cleo/procurado.txt
    sudo python gta/ponte.py /dev/ttyUSB0 --memoria  # sem CLEO: lê o nível da memória do jogo
    python gta/ponte.py /dev/ttyUSB0 --demo        # sem o jogo: sobe 0 a 6 e volta

Usa o pyserial se ele estiver instalado; se não, abre a porta na mão com o stty,
que basta no Linux e no macOS. No Windows, instale o pyserial.

O script CLEO (gta/procurado.cs) grava o nível num arquivo a cada 200 ms; aqui
só vigiamos esse arquivo e escrevemos uma linha na serial quando o número muda.
Uma linha por mudança é o que o CJPHONEHOME do programa da placa espera.

Sem CLEO (--memoria), a ponte acha sozinha onde o jogo guarda o nível: lê toda a
memória gravável do processo procurando o número de estrelas que você digitou, e a
cada mudança de nível descarta os endereços que não acompanharam. Não depende da
versão do executável, mas precisa de sudo para ler a memória de outro processo.
"""
import argparse
import os
import struct
import subprocess
import sys
import time

ESPERA_BOOT = 2.0   # abrir a porta reinicia a placa; espera ela subir
INTERVALO = 0.1     # com os 200 ms do CLEO, o LED reage em até 0,3 s
DEMO = [0, 1, 2, 3, 4, 5, 6, 0]
BLOCO = 16 << 20    # a varredura lê a memória em pedaços de 16 MB
LIMITE_32 = 1 << 32  # ponytail: o jogo é 32 bits; acima disso só tem o próprio Wine
MIRA = 5            # cópias do mesmo nível que sobrevivem a toda mudança; qualquer uma serve


class PortaSimples:
    """A porta serial sem pyserial: o stty ajusta o baud, o resto é escrever no arquivo."""

    def __init__(self, porta, baud):
        for opcao in ("-F", "-f"):  # -F no Linux, -f no macOS
            if subprocess.run(["stty", opcao, porta, str(baud), "raw", "-echo"],
                              capture_output=True).returncode == 0:
                break
        else:
            sys.exit(f"não consegui configurar {porta}: a placa está ligada? você está no grupo uucp?")
        self.fd = os.open(porta, os.O_RDWR | os.O_NOCTTY)  # abrir reinicia a placa

    def write(self, dados):
        os.write(self.fd, dados)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        os.close(self.fd)


def abrir(porta, baud):
    try:
        import serial  # pyserial, se houver
    except ImportError:
        return PortaSimples(porta, baud)
    return serial.Serial(porta, baud)


def nivel_do_arquivo(caminho):
    """Nível gravado pelo CLEO; 0 se o arquivo ainda não existe ou está sendo escrito."""
    try:
        with open(caminho, encoding="utf-8", errors="ignore") as f:
            return max(0, min(6, int(f.read().strip() or 0)))
    except (OSError, ValueError):
        return 0


def achar_jogo():
    """PID do gta-sa.exe (ou gta_sa.exe) rodando no Wine ou no Proton."""
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                programa = f.read().split(b"\0")[0].lower()
        except OSError:
            continue
        if programa.endswith((b"gta-sa.exe", b"gta_sa.exe")):  # o argv[0] do Wine é o caminho do .exe
            return int(pid)
    sys.exit("não achei o gta-sa.exe rodando: abra o jogo primeiro, ou passe --pid")


def abrir_memoria(pid):
    try:
        return os.open(f"/proc/{pid}/mem", os.O_RDONLY)
    except PermissionError:
        sys.exit("sem permissão para ler a memória do jogo: rode a ponte com sudo")


def regioes(pid, limite):
    """Faixas de memória graváveis do processo, cortadas no limite."""
    with open(f"/proc/{pid}/maps") as f:
        for linha in f:
            faixa, permissao = linha.split()[:2]
            ini, fim = (int(x, 16) for x in faixa.split("-"))
            if permissao.startswith("rw") and (limite is None or ini < limite):
                yield ini, fim if limite is None else min(fim, limite)


def varrer(mem, pid, nivel, limite=LIMITE_32):
    """Todo endereço alinhado da memória gravável que guarda `nivel` como inteiro de 32 bits."""
    alvo = struct.pack("<i", nivel)
    achados = []
    for ini, fim in regioes(pid, limite):
        for pedaco in range(ini, fim, BLOCO):
            try:
                dados = os.pread(mem, min(BLOCO, fim - pedaco), pedaco)
            except OSError:
                break  # região que o kernel não deixa ler: pula
            i = dados.find(alvo)
            while i != -1:
                if i % 4 == 0:
                    achados.append(pedaco + i)
                i = dados.find(alvo, i + 1)
    return achados


def ler(mem, endereco):
    dados = os.pread(mem, 4, endereco)
    if len(dados) < 4:
        raise OSError("endereço fora da memória do jogo")
    return struct.unpack("<i", dados)[0]


def filtrar(mem, candidatos, nivel):
    """Só os endereços que agora valem `nivel`."""
    sobram = []
    for e in candidatos:
        try:
            if ler(mem, e) == nivel:
                sobram.append(e)
        except OSError:
            pass
    return sobram


def _estrelas(perguntar, minimo):
    while True:
        try:
            n = int(perguntar(f"estrelas agora ({minimo} a 6): "))
        except ValueError:
            continue
        if minimo <= n <= 6:
            return n


def calibrar(mem, pid, perguntar=input, limite=LIMITE_32):
    """Acha o endereço do nível de procurado perguntando quantas estrelas há na tela.

    Para quando uma mudança de nível não elimina mais ninguém: o que sobra são cópias
    do nível, e não coincidências que por acaso bateram até ali.
    """
    print("No jogo, pegue estrelas (o cheat TURNUPTHEHEAT dá duas) e diga quantas há.")
    candidatos = []
    while not candidatos:
        n = _estrelas(perguntar, 1)  # 0 está em toda parte; começa com pelo menos uma estrela
        candidatos = varrer(mem, pid, n, limite)
    antes = None
    while len(candidatos) != antes or len(candidatos) > MIRA:
        quantos = "1 endereço vale" if len(candidatos) == 1 else f"{len(candidatos)} endereços valem"
        print(f"{quantos} {n}. Mude o nível no jogo (TURNDOWNTHEHEAT zera).")
        novo = _estrelas(perguntar, 0)
        if novo == n:
            print("o nível precisa mudar antes de responder")
            continue
        n, antes = novo, len(candidatos)
        candidatos = filtrar(mem, candidatos, n)
        if not candidatos:
            sys.exit("perdi o rastro do nível: calibre de novo, conferindo as estrelas antes de responder")
    print(f"achei o nível em {candidatos[0]:#x}")
    return candidatos[0]


def nivel_da_memoria(mem, endereco):
    try:
        n = ler(mem, endereco)
    except OSError:
        sys.exit("o jogo fechou")
    return n if 0 <= n <= 6 else 0


def niveis(args, nivel_atual):
    """Gera o nível atual, para sempre."""
    if args.demo:
        while True:
            for n in DEMO:
                yield n
                time.sleep(args.passo)
    else:
        while True:
            yield nivel_atual()
            time.sleep(INTERVALO)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("porta", help="/dev/ttyUSB0 (clone CH340), /dev/ttyACM0 (original), COM3 no Windows")
    fonte = ap.add_mutually_exclusive_group(required=True)
    fonte.add_argument("--arquivo", help="procurado.txt que o script CLEO grava")
    fonte.add_argument("--memoria", action="store_true", help="sem CLEO: lê o nível direto da memória do jogo")
    fonte.add_argument("--demo", action="store_true", help="sem o jogo: sobe de 0 a 6 e volta, em laço")
    ap.add_argument("--pid", type=int, help="processo do jogo, se a ponte não achar sozinha")
    ap.add_argument("--passo", type=float, default=2.0, metavar="S", help="segundos por nível no --demo")
    ap.add_argument("--baud", type=int, default=115200)
    args = ap.parse_args(argv)

    if args.memoria:  # calibra antes de abrir a porta: abrir reinicia a placa
        pid = args.pid or achar_jogo()
        mem = abrir_memoria(pid)
        endereco = calibrar(mem, pid)
        nivel_atual = lambda: nivel_da_memoria(mem, endereco)
    else:
        nivel_atual = lambda: nivel_do_arquivo(args.arquivo)

    with abrir(args.porta, args.baud) as placa:
        time.sleep(ESPERA_BOOT)
        anterior = None
        for nivel in niveis(args, nivel_atual):
            if nivel != anterior:
                placa.write(f"{nivel}\n".encode())
                print(f"{nivel} estrela(s)", flush=True)
                anterior = nivel
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
