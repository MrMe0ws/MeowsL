"""Точка входа: py -3 main.py

Запускает фоновый переводчик с глобальными хоткеями.
UI: frameless popup со скруглёнными углами, ресайзом со всех сторон,
языковыми метками внутри полей и копированием по hover.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from translate_meows.app import run  # noqa: E402

if __name__ == "__main__":
    sys.exit(run())
