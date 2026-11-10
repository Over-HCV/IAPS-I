"""Poner la raíz del repositorio en sys.path para que el paquete ``project`` sea importable.

Así los tests corren con ``uv run pytest project/tests`` sin instalar el paquete, igual
que el cuaderno, que importa ``from project import ...``.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
