# Falas do jogo

Coloque aqui os clipes de áudio. Eles **não** são versionados (são áudio da Rockstar); cada pessoa do grupo copia os seus. Os mesmos arquivos servem para a linha de comando e para o Grove Online (o app).

| Arquivo | Quando toca | Fala sugerida |
|---|---|---|
| `passed.wav` | programa rodou sem erro | "MISSION PASSED! Respect +" |
| `lex_error.wav` | erro léxico | "WASTED" |
| `parse_error.wav` | erro sintático | Big Smoke: "All you had to do was follow the damn train, CJ!" |
| `semantic_error.wav` | erro semântico | "BUSTED" |
| `runtime_error.wav` | erro de execução, ou programa que passou de 5 s no app | CJ: "Ah shit, here we go again." |

Converter mp3 para wav: `ffmpeg -i fala.mp3 passed.wav`. Sem arquivo, o Grove fica em silêncio.

## No Grove Online

- O som toca quando alguém **executa** o programa (botão Executar, Ctrl+Enter, um exemplo ou um arquivo aberto). Não toca na execução automática ao abrir a página, nem na compilação ao vivo enquanto se digita.
- O app também aceita `.mp3` com os mesmos nomes (`passed.mp3`…); a linha de comando só toca `.wav`.
- O botão de alto-falante no canto, ao lado das estrelas, liga e desliga as falas. A escolha fica salva no navegador.
- O app procura os arquivos em `assets/`, ao lado de `playground/`. Funciona quando a página é aberta de onde os arquivos estão, por exemplo com `python -m http.server` na raiz do repositório, como na apresentação.
- No GitHub Pages os arquivos só existem se forem commitados, e hoje eles não são: `.gitignore` ignora `assets/*.wav`. Publicar os áudios da Rockstar no repositório é uma decisão do grupo. Sem eles, o app no ar fica em silêncio e avisa uma vez.
