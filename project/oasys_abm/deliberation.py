"""La deliberación como acción con duración, progreso e interrupción.

Es la pieza conceptual del trabajo. En la mayoría de modelos basados en agentes, decidir
es gratis: ocurre entre ticks y no consume nada. Aquí no. Deliberar es **una acción del
mismo tipo que moverse**, ocupa ``duration`` ticks del reloj, y durante esos ticks el
mundo sigue cambiando. Sin eso no hay costo que medir y la pregunta del trabajo se vuelve
trivial (ver ``docs/02-design.md`` §1).

De ahí se sigue la decisión de modelado más importante del módulo: **el plan que produce
una deliberación se calcula con el mundo tal como estaba cuando la deliberación empezó.**
Si el mundo se movió mientras el agente pensaba, el plan llega desactualizado. Ese es el
costo real de pensar en un entorno dinámico, y es lo que hace que deliberar más no sea
siempre mejor.

Nota de implementación: MESA 4.0 trae una clase ``Action`` equivalente, y MESA 3.5.1 trae
un simulador de eventos discretos (``mesa.experimental.devs``) sobre el cual podría
construirse. No se usa ninguno de los dos. El simulador queda descartado porque
``batch_run`` —el eje experimental del proyecto— es un bucle ``while model.running:
model.step()`` que no sabe nada de colas de eventos (``mesa/batchrunner.py:206``), y una
cola de eventos solo paga cuando los eventos son escasos, mientras que aquí cada agente
actúa en cada tick. La clase ``Action`` de 4.0 queda descartada porque es justamente el
objeto de estudio: importarla prehecha escondería el mecanismo que se quiere medir
(ver ``docs/00-rationale.md`` §4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from oasys_abm.book import Line


class DeliberationState(StrEnum):
    """Ciclo de vida de una deliberación."""

    ACTIVE = "ACTIVE"
    """En curso: quedan ticks por consumir."""

    COMPLETED = "COMPLETED"
    """Terminó y su resultado puede aplicarse."""

    INTERRUPTED = "INTERRUPTED"
    """Abortada antes de terminar; el resultado se descarta."""


@dataclass(slots=True)
class Deliberation:
    """Una deliberación en curso.

    El resultado (``lines``) se calcula al **iniciar** y se retiene hasta que termina.
    Esa demora es intencional: modela que la respuesta de un replanificador refleja el
    mundo del momento en que se le preguntó, no el del momento en que responde.

    Attributes:
        duration: ticks que consume. ``0`` = instantánea.
        from_idx: índice del plan desde el cual se aplicará el resultado.
        lines: el sufijo propuesto, ya calculado.
        elapsed: ticks consumidos hasta ahora.
        state: estado del ciclo de vida.
        label: etiqueta del tipo de propuesta, para las métricas.
    """

    duration: int
    from_idx: int
    lines: list[Line] = field(default_factory=list)
    elapsed: int = 0
    state: DeliberationState = DeliberationState.ACTIVE
    label: str = ""

    def __post_init__(self) -> None:
        """Una deliberación de duración cero nace ya terminada."""
        if self.duration < 0:
            raise ValueError("la duración no puede ser negativa")
        if self.duration == 0:
            self.state = DeliberationState.COMPLETED

    @property
    def progress(self) -> float:
        """Fracción completada, en ``[0, 1]``."""
        if self.duration == 0:
            return 1.0
        return min(1.0, self.elapsed / self.duration)

    @property
    def remaining(self) -> int:
        """Ticks que faltan para terminar."""
        return max(0, self.duration - self.elapsed)

    @property
    def is_active(self) -> bool:
        """True mientras siga consumiendo ticks."""
        return self.state is DeliberationState.ACTIVE

    @property
    def is_complete(self) -> bool:
        """True si terminó y su resultado es aplicable."""
        return self.state is DeliberationState.COMPLETED

    def tick(self) -> DeliberationState:
        """Consumir un tick. Devuelve el estado resultante.

        Llamarlo sobre una deliberación que ya no está activa no hace nada: es
        idempotente a propósito, para que el bucle del agente no tenga que comprobar
        el estado antes de avanzar.
        """
        if not self.is_active:
            return self.state
        self.elapsed += 1
        if self.elapsed >= self.duration:
            self.state = DeliberationState.COMPLETED
        return self.state

    def interrupt(self) -> bool:
        """Abortar la deliberación y descartar su resultado.

        Es lo que ocurre cuando llega una divergencia nueva antes de que el agente
        termine de pensar sobre la anterior: los ticks ya gastados se pierden. Esa
        pérdida es la forma operacional del *thrashing* de replanificación.

        Returns:
            True si se interrumpió algo que estaba activo; False si ya había terminado
            o ya estaba interrumpida.
        """
        if not self.is_active:
            return False
        self.state = DeliberationState.INTERRUPTED
        self.lines = []
        return True
