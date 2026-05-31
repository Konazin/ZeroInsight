"""Ponto de entrada na raiz do repositório — ZeroInsight."""

from __future__ import annotations

import sys
from pathlib import Path

# Garante imports ao rodar `python main.py` na raiz do projeto
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from zero_insight.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
