// Arduino de mentira para os testes: relógio virtual e um log do que o programa fez.
//
//   g++ -x c++ -include tests/arduino_falso.h programa.ino -o programa && ./programa
//
// Cada linha da saída é "P <ms> <pino> <0|1>" para digitalWrite e "O <ms> <texto>"
// para Serial.println, que é o que o programa Grove imprime. A última é
// "F <ms>", o relógio no fim do setup.
#ifndef ARDUINO_FALSO_H
#define ARDUINO_FALSO_H

#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <string>

typedef std::string String;
typedef uint8_t byte;

enum { LOW = 0, HIGH = 1, OUTPUT = 1, INPUT = 0 };

static unsigned long _agora = 0;  // relógio virtual: só o delay faz o tempo andar

inline void _fim() {  // acabou a entrada (ou o setup): registra a hora e sai
    printf("F %lu\n", _agora);
    exit(0);
}

inline unsigned long millis() { return _agora; }
inline void delay(unsigned long ms) { _agora += ms; }
inline void pinMode(int, int) {}
inline void digitalWrite(int pino, int valor) { printf("P %lu %d %d\n", _agora, pino, valor ? 1 : 0); }

struct SerialFalso {
    bool aberta = false;  // print não fecha a linha; println fecha

    void abrir() {
        if (!aberta) printf("O %lu ", _agora);
        aberta = true;
    }
    void begin(long) {}
    void flush() {}
    int available() {  // a entrada do CJPHONEHOME é o stdin; sem mais linhas, o programa acaba
        int c = getchar();
        if (c == EOF) _fim();
        ungetc(c, stdin);
        return 1;
    }
    char read() { return (char)getchar(); }
    void print(const char *s) { abrir(); printf("%s", s); }
    void println(const char *s) { abrir(); printf("%s\n", s); aberta = false; }
    void println(const String &s) { println(s.c_str()); }
    void println(long v) { abrir(); printf("%ld\n", v); aberta = false; }
} Serial;

// no AVR max é macro; definida depois dos headers da std para não atrapalhá-los
#define max(a, b) ((a) > (b) ? (a) : (b))

void setup();
void loop();

int main() {
    setup();  // o corpo do programa vive todo no setup
    // ARDUINO_FALSO_DEPOIS=<ms> roda o loop() por mais esse tanto, para ver o que ele faz sozinho
    const char *extra = getenv("ARDUINO_FALSO_DEPOIS");
    unsigned long fim = _agora + (extra ? strtoul(extra, nullptr, 10) : 0);
    while (_agora < fim) {
        unsigned long antes = _agora;
        loop();
        if (_agora == antes) break;  // loop vazio: não adianta insistir
    }
    printf("F %lu\n", _agora);
    return 0;
}

#endif
