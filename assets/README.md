# Falas do jogo

Coloque aqui os clipes em `.wav`. Eles **não** são versionados (são áudio da Rockstar); cada pessoa do grupo copia os seus.

| Arquivo | Quando toca | Fala sugerida |
|---|---|---|
| `passed.wav` | programa rodou sem erro | "MISSION PASSED! Respect +" |
| `lex_error.wav` | erro léxico | "WASTED" |
| `parse_error.wav` | erro sintático | Big Smoke: "All you had to do was follow the damn train, CJ!" |
| `semantic_error.wav` | erro semântico | "BUSTED" |
| `runtime_error.wav` | erro de execução | CJ: "Ah shit, here we go again." |

Converter mp3 para wav: `ffmpeg -i fala.mp3 passed.wav`. Sem arquivo, o Grove fica em silêncio.
