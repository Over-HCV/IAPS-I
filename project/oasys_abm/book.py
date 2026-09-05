"""El plan como programa: réplica mínima del Book de OASys.

OASys organiza un programa como ``Device -> Books -> Pages -> Lines -> Cells`` y lo
ejecuta con un contador de programa (``PageRunner { line_idx, cell_idx, call_stack }``
en ``backend/src/engine/scheduler/mod.rs``). Aquí se conserva lo mínimo que hace falta
para estudiar la auto-edición: una secuencia de líneas y un contador.

En vocabulario de Russell & Norvig un Book es un **plan**, y ``replace_suffix`` es la
operación de **replanificación** (cap. 11, §11.5.3). El atributo ``locked`` de una línea
es el análogo de ``@lock`` en OASys, cuya invariante impone
``agent::tools::governance::validate_edit``: toda construcción bloqueada debe seguir
siendo idéntica después de la edición.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any


class LineOp(StrEnum):
    """Operaciones primitivas de un plan."""

    GOTO = "GOTO"
    """Avanzar un paso hacia la celda destino (``arg`` = coordenada)."""

    PICK = "PICK"
    """Recoger el recurso ``arg`` de la celda actual."""

    DELIVER = "DELIVER"
    """Depositar lo transportado en la base."""

    SCAN = "SCAN"
    """Gastar un tick observando sin moverse."""


class EditRejected(Exception):
    """La edición propuesta viola una invariante del plan.

    Equivalente al fallo de ``validate_edit`` en OASys, donde una edición que toca una
    construcción bloqueada se rechaza entera y no deja el plan a medias.
    """


@dataclass(frozen=True, slots=True)
class Line:
    """Una instrucción del plan.

    Es inmutable a propósito: una línea bloqueada no puede alterarse ni siquiera por
    accidente, y toda edición obliga a construir líneas nuevas.
    """

    op: LineOp
    arg: Any = None
    locked: bool = False


@dataclass(slots=True)
class Book:
    """Un plan con su contador de programa.

    Attributes:
        lines: las instrucciones, en orden de ejecución.
        pc: índice de la siguiente línea a ejecutar (*program counter*).
    """

    lines: list[Line] = field(default_factory=list)
    pc: int = 0

    def __len__(self) -> int:
        """Número de líneas del plan."""
        return len(self.lines)

    @property
    def done(self) -> bool:
        """True si el contador ya pasó la última línea."""
        return self.pc >= len(self.lines)

    @property
    def current(self) -> Line | None:
        """Línea que toca ejecutar, o None si el plan terminó."""
        return None if self.done else self.lines[self.pc]

    @property
    def remaining(self) -> list[Line]:
        """Líneas todavía no ejecutadas, incluida la actual."""
        return self.lines[self.pc :]

    def advance(self) -> None:
        """Mover el contador a la línea siguiente."""
        self.pc += 1

    def replace_suffix(self, from_idx: int, new_lines: list[Line]) -> None:
        """Reemplazar el plan desde ``from_idx`` — el análogo de ``editBook``.

        La edición se acepta o se rechaza entera; nunca deja el plan a medias. Se
        rechaza en dos casos:

        1. ``from_idx`` es anterior al contador de programa. Reescribir el pasado no
           tiene sentido: esas líneas ya se ejecutaron y sus efectos ya ocurrieron.
        2. La edición altera las líneas bloqueadas. La comprobación replica la de
           OASys (``collect_locked_renders(old) != collect_locked_renders(new)`` en
           ``backend/src/agent/tools/governance.rs``): lo que debe conservarse es el
           *contenido* de lo bloqueado y su orden, no su posición. Un sufijo puede por
           tanto reescribirse aunque contenga líneas bloqueadas, siempre que las
           reproduzca intactas — que es justo lo que permite reparar la ruta hacia un
           recurso sin poder eliminar el ``DELIVER`` comprometido al final.

        Args:
            from_idx: primer índice a reemplazar.
            new_lines: líneas que sustituyen al sufijo.

        Raises:
            EditRejected: si la edición viola alguna de las dos invariantes.
        """
        if from_idx < self.pc:
            raise EditRejected(
                f"la edición toca líneas ya ejecutadas "
                f"(from_idx={from_idx} < pc={self.pc})"
            )
        if from_idx > len(self.lines):
            raise EditRejected(
                f"from_idx={from_idx} fuera de rango (len={len(self.lines)})"
            )

        candidate = self.lines[:from_idx] + list(new_lines)
        before = self.locked_render()
        after = [ln for ln in candidate if ln.locked]
        if before != after:
            raise EditRejected(
                f"la edición altera líneas bloqueadas: {before} -> {after}"
            )

        self.lines = candidate

    def copy(self) -> Book:
        """Copia independiente del plan (las líneas son inmutables, se comparten)."""
        return Book(lines=list(self.lines), pc=self.pc)

    def locked_render(self) -> list[Line]:
        """Contenido de las líneas bloqueadas, en orden.

        Análogo de ``collect_locked_renders`` en OASys
        (``backend/src/agent/tools/governance.rs``), que compara el render de las
        construcciones bloqueadas antes y después de un ``editBook``. Se compara el
        contenido y el orden, no el índice: una línea bloqueada puede desplazarse si
        el sufijo que la precede cambia de longitud.
        """
        return [ln for ln in self.lines if ln.locked]


def goto_lines(path: list[Any], *, locked: bool = False) -> list[Line]:
    """Convertir una ruta en líneas ``GOTO``.

    Acepta celdas o coordenadas, y almacena siempre **coordenadas**. La distinción
    importa: un plan es dato, igual que el fuente ``.os`` de OASys, y no debe guardar
    referencias vivas al mundo. Guardar celdas ataría el plan a la instancia concreta
    del modelo y haría imposible serializarlo o compararlo.

    Se omite el primer elemento de la ruta: es la posición actual del agente, no un
    destino al que haya que moverse.
    """
    return [Line(LineOp.GOTO, getattr(x, "coordinate", x), locked) for x in path[1:]]


def with_lock(line: Line, *, locked: bool = True) -> Line:
    """Devolver una copia de la línea con otro estado de bloqueo."""
    return replace(line, locked=locked)
