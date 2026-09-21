"""Gera colab/grove.ipynb a partir dos dois .py desta pasta.

O notebook é derivado, como docs/tokens.pdf é de docs/tokens.md: edite os .py
e rode `python3 colab/gerar_notebook.py` para refazê-lo. Só stdlib.
"""
import json
import pathlib

AQUI = pathlib.Path(__file__).parent

INTRO = """# Grove no Colab

Linguagem de programação em que as palavras-chave são os cheats de **GTA San Andreas**. \
Projeto da disciplina de Compiladores.

1. A primeira célula é o compilador: analisador léxico, nós da AST e analisador sintático.
2. A segunda roda um programa `.cj` de exemplo e mostra a tabela de tokens e a AST em árvore.

Rode as duas na ordem (`Ctrl+F9` roda tudo). Repositório: <https://github.com/fernandomcrsilva/grove-language>
"""


def celula(tipo: str, texto: str) -> dict:
    c = {"cell_type": tipo, "metadata": {}, "source": texto.splitlines(keepends=True)}
    if tipo == "code":
        c |= {"execution_count": None, "outputs": []}
    return c


notebook = {
    "cells": [
        celula("markdown", INTRO),
        celula("code", (AQUI / "grove.py").read_text()),
        celula("code", (AQUI / "exemplo_grove.py").read_text()),
    ],
    "metadata": {
        "colab": {"provenance": [], "toc_visible": True},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

destino = AQUI / "grove.ipynb"
destino.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n")
print(f"{destino.name} gerado: {len(notebook['cells'])} células")
