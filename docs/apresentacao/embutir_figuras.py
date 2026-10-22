"""Atualiza as figuras dos esquemas embutidas em apresentacao-projeto1.html.

O HTML guarda cada PNG de docs/modelagem/ como data URI num bloco <script id="figuras">, para abrir
sozinho, sem depender de outros arquivos. Depois de gerar as figuras de novo, rode:

    python docs/apresentacao/embutir_figuras.py
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
HTML = AQUI / "apresentacao-projeto1.html"
MODELAGEM = AQUI.parent / "modelagem"
BLOCO = re.compile(r'(<script id="figuras" type="application/json">)(.*?)(</script>)', re.S)


def figuras() -> dict[str, str]:
    return {p.stem: "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")
            for p in sorted(MODELAGEM.glob("*.png"))}


def main() -> None:
    dados = json.dumps(figuras(), separators=(",", ":"))
    texto, trocas = BLOCO.subn(lambda m: m.group(1) + dados + m.group(3), HTML.read_text(encoding="utf-8"))
    if trocas != 1:
        raise SystemExit(f"{HTML.name}: bloco de figuras não encontrado")
    HTML.write_text(texto, encoding="utf-8", newline="\n")
    print(f"{len(json.loads(dados))} figuras embutidas em {HTML.name}")


if __name__ == "__main__":
    main()
