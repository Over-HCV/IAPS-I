"""Poner ``project/`` en sys.path para que ``oasys_abm`` sea importable.

No se importa ``project`` como paquete a propósito: su ``__init__.py`` está roto en la
copia vendorizada de los ejemplos de Mesa.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
