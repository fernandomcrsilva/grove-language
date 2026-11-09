# Falas do jogo

Coloque aqui os clipes de áudio. Desde 09/11/2026 eles **são** versionados e sobem junto com o site, por decisão do grupo — antes cada pessoa copiava os seus. Os mesmos arquivos servem para a linha de comando e para o Grove Online (o app). As falas continuam sendo material da Rockstar: num repositório público, quem publica responde por elas.

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
- No site os arquivos sobem no `wrangler deploy` como qualquer outro asset — nem o `.gitignore` nem o `.assetsignore` os excluem mais. Enquanto um deles não existir, o app fica em silêncio e avisa uma vez.
