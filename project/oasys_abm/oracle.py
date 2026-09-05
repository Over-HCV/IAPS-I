"""El replanificador LLM, abstraído como oráculo ruidoso.

El agente no llama a ningún modelo de lenguaje. El replanificador se modela con dos
parámetros —competencia ``p`` y costo ``c``— por una razón metodológica, no de
presupuesto: abstraerlo así **convierte una propiedad del modelo en un parámetro del
experimento**. Con un LLM real solo se puede responder "¿funcionó con este modelo, hoy?";
con el oráculo se responde "¿a partir de qué competencia mínima conviene dejar que un
agente se auto-edite, y cuánto puede costarle cada edición?" — un enunciado que sobrevive
al cambio de modelo. El argumento completo está en ``docs/00-rationale.md`` §3.4–3.5.

Los dos modos de fallo están elegidos para parecerse a los de un modelo de lenguaje real:
son planes **coherentes y equivocados**, no ruido. Un LLM que se equivoca no devuelve
basura; devuelve algo razonable y falso.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from random import Random
from typing import Any

from oasys_abm.book import Book, Line, LineOp, goto_lines
from oasys_abm.planner import astar, manhattan


class ProposalKind(StrEnum):
    """Cómo salió la propuesta del oráculo. Se registra para las métricas."""

    OPTIMAL = "OPTIMAL"
    """Ruta óptima hacia el objetivo real."""

    STALE_TARGET = "STALE_TARGET"
    """Ruta óptima hacia donde el agente *creía* que estaba el objetivo."""

    DETOUR = "DETOUR"
    """Objetivo correcto, camino subóptimo."""

    INFEASIBLE = "INFEASIBLE"
    """No se encontró ninguna ruta; no hay propuesta que hacer."""


@dataclass(frozen=True, slots=True)
class RepairRequest:
    """Todo lo que el oráculo necesita para proponer una reparación.

    Attributes:
        book: el plan actual.
        from_idx: índice desde el cual se reemplazará.
        origin: celda donde está el agente.
        true_goal: celda donde el objetivo está realmente. ``None`` si el agente no
            puede observarlo.
        believed_goal: celda donde el agente cree que está el objetivo.
        resource_id: identificador del recurso objetivo.
        tail: **toda** la continuación del plan tras recoger el objetivo: los objetivos
            que queden pendientes, el regreso a la base y el ``DELIVER`` bloqueado que
            la gobernanza obliga a conservar. Que la reparación arrastre la continuación
            en vez de truncar la tarea es esencial: un parche que reduce el plan a un
            solo objetivo produce sistemáticamente planes peores, y el experimento
            estaría midiendo ese defecto en vez de la replanificación.
    """

    book: Book
    from_idx: int
    origin: Any
    true_goal: Any | None
    believed_goal: Any
    resource_id: str
    tail: tuple[Line, ...] = ()


@dataclass(frozen=True, slots=True)
class Proposal:
    """Resultado de una consulta al oráculo.

    Attributes:
        from_idx: índice desde el cual aplicar ``lines``.
        lines: el sufijo propuesto.
        kind: si la propuesta fue óptima o cuál fue el modo de fallo.
        expanded: nodos expandidos por la búsqueda, como medida del esfuerzo.
    """

    from_idx: int
    lines: list[Line]
    kind: ProposalKind
    expanded: int = 0

    @property
    def feasible(self) -> bool:
        """True si hay algo que aplicar."""
        return self.kind is not ProposalKind.INFEASIBLE


@dataclass(slots=True)
class Oracle:
    """Replanificador con competencia y costo explícitos.

    Attributes:
        p: probabilidad de que la propuesta sea la óptima.
        cost: ticks de deliberación que consume cada consulta.
        random: generador del modelo, para que las corridas sean reproducibles.
        passable: predicado de transitabilidad de una celda.
        dimensions: tamaño de la retícula (necesario si es toroidal).
        torus: si la retícula da la vuelta.
        cells: celdas de las que muestrear puntos intermedios para el fallo por
            desvío. Sin ellas, ese modo de fallo no puede garantizarse y el oráculo
            degrada a devolver la ruta óptima.
    """

    p: float
    cost: int
    random: Random
    passable: Callable[[Any], bool] | None = None
    dimensions: Sequence[int] | None = None
    torus: bool = False
    cells: Sequence[Any] | None = None

    def _route(self, origin: Any, goal: Any) -> tuple[list[Any], int]:
        """Ruta óptima entre dos celdas, con el número de nodos expandidos."""
        res = astar(
            origin,
            goal,
            passable=self.passable,
            dimensions=self.dimensions,
            torus=self.torus,
        )
        return res.path, res.expanded

    def _after_pick(self, req: RepairRequest, goal: Any) -> tuple[list[Line], int]:
        """Lo que va después de llegar al objetivo: recogerlo y seguir con el plan."""
        return [Line(LineOp.PICK, req.resource_id), *req.tail], 0

    def _build(self, req: RepairRequest, goal: Any) -> tuple[list[Line], int]:
        """Plan completo hacia ``goal``: ruta, recogida, regreso y cola comprometida."""
        path, expanded = self._route(req.origin, goal)
        if not path:
            return [], expanded
        cola, e_cola = self._after_pick(req, goal)
        if not cola:
            return [], expanded + e_cola
        return goto_lines(path) + cola, expanded + e_cola

    def _pick_waypoint(self, origin: Any, goal: Any, *, tries: int = 12) -> Any | None:
        """Elegir un punto intermedio que aleje realmente de la ruta directa.

        Un vecino inmediato no sirve: desde una esquina todos los vecinos acercan al
        objetivo, y el "desvío" saldría de longitud óptima. Se muestrea entre todas las
        celdas y se exige que la suma de las dos distancias supere la directa.
        """
        if not self.cells:
            return None
        directa = manhattan(
            origin.coordinate,
            goal.coordinate,
            dimensions=self.dimensions,
            torus=self.torus,
        )
        for _ in range(tries):
            cand = self.random.choice(self.cells)
            if cand is origin or cand is goal or not self._ok(cand):
                continue
            rodeo = manhattan(
                origin.coordinate,
                cand.coordinate,
                dimensions=self.dimensions,
                torus=self.torus,
            ) + manhattan(
                cand.coordinate,
                goal.coordinate,
                dimensions=self.dimensions,
                torus=self.torus,
            )
            if rodeo > directa:
                return cand
        return None

    def _detour(self, req: RepairRequest, goal: Any) -> tuple[list[Line], int, bool]:
        """Objetivo correcto por un camino subóptimo, vía un punto intermedio.

        Modela el fallo del replanificador que llega a donde debe pero gastando de más:
        el plan es válido y el agente lo ejecuta entero antes de notar nada.

        Returns:
            Las líneas, los nodos expandidos, y si el desvío resultó realmente más
            largo que la ruta directa. Cuando la geometría no permite desviar, se
            devuelve la ruta óptima y el tercer valor es False, para que quien llama
            no etiquete como fallo algo que no lo fue.
        """
        directo, e0 = self._route(req.origin, goal)
        waypoint = self._pick_waypoint(req.origin, goal)
        if waypoint is None:
            lines, expanded = self._build(req, goal)
            return lines, expanded, False

        first, e1 = self._route(req.origin, waypoint)
        second, e2 = self._route(waypoint, goal)
        if not first or not second:
            lines, expanded = self._build(req, goal)
            return lines, expanded, False

        cola, e_cola = self._after_pick(req, goal)
        if not cola:
            lines, expanded = self._build(req, goal)
            return lines, expanded, False

        lines = goto_lines(first) + goto_lines(second) + cola
        pasos = (len(first) - 1) + (len(second) - 1)
        return lines, e0 + e1 + e2 + e_cola, pasos > max(0, len(directo) - 1)

    def _ok(self, cell: Any) -> bool:
        """Aplicar el predicado de transitabilidad, tolerando que no haya."""
        return self.passable is None or self.passable(cell)

    def propose(self, req: RepairRequest) -> Proposal:
        """Proponer una reparación del plan desde ``req.from_idx``.

        Con probabilidad ``p`` devuelve la ruta óptima hacia el objetivo real. Con
        probabilidad ``1 - p`` falla de uno de dos modos, elegido al azar:

        - **objetivo obsoleto**: ruta óptima hacia la última posición conocida, que ya
          cambió. El plan es internamente coherente y va al lugar equivocado.
        - **desvío**: objetivo correcto, camino más largo del necesario.

        Si el agente no puede observar el objetivo real (``true_goal is None``), no hay
        acierto posible: lo mejor que puede hacer es dirigirse a su creencia, y eso se
        clasifica como ``STALE_TARGET`` aunque el oráculo haya "acertado". La ceguera no
        es un fallo del replanificador, es una limitación del sensor.
        """
        acierta = self.random.random() < self.p
        goal_real = req.true_goal

        if goal_real is None:
            lines, expanded = self._build(req, req.believed_goal)
            kind = ProposalKind.STALE_TARGET
        elif acierta:
            lines, expanded = self._build(req, goal_real)
            kind = ProposalKind.OPTIMAL
        elif self.random.random() < 0.5:
            lines, expanded = self._build(req, req.believed_goal)
            kind = (
                ProposalKind.OPTIMAL
                if req.believed_goal is goal_real
                else ProposalKind.STALE_TARGET
            )
        else:
            lines, expanded, desvio_real = self._detour(req, goal_real)
            kind = ProposalKind.DETOUR if desvio_real else ProposalKind.OPTIMAL

        if not lines:
            return Proposal(req.from_idx, [], ProposalKind.INFEASIBLE, expanded)
        return Proposal(req.from_idx, lines, kind, expanded)
