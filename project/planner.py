"""Búsqueda en el espacio de estados: BFS y A\\* sobre la retícula.

Los dos algoritmos están escritos a mano, no importados, por dos razones. La primera es
que son el contenido de las sesiones 3 y 4 del curso y el notebook debe mostrarlos. La
segunda es que en este trabajo la búsqueda no es un capítulo aparte: **A\\* es el
planificador que el agente invoca cada vez que se auto-edita**, así que su costo en nodos
expandidos forma parte del costo de deliberar.

Ambas funciones devuelven un ``SearchResult`` con el número de nodos expandidos, que es
lo que permite la comparación clásica entre búsqueda ciega e informada
(Russell & Norvig, §3.4 y §3.5).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import Any, Protocol


class CellLike(Protocol):
    """Lo mínimo que el planificador necesita de una celda de ``discrete_space``."""

    coordinate: tuple[int, ...]
    connections: dict[Any, Any]


Passable = Callable[[Any], bool]


@dataclass(slots=True)
class SearchResult:
    """Resultado de una búsqueda.

    Attributes:
        path: celdas desde el origen hasta el destino, ambos incluidos. Vacío si no hay
            ruta.
        expanded: nodos sacados de la frontera. La métrica de comparación entre
            búsqueda ciega e informada.
        found: si se alcanzó el destino.
    """

    path: list[Any]
    expanded: int
    found: bool

    def __len__(self) -> int:
        """Longitud de la ruta en número de celdas."""
        return len(self.path)

    @property
    def cost(self) -> int:
        """Número de movimientos de la ruta (celdas menos uno)."""
        return max(0, len(self.path) - 1)


def manhattan(
    a: Sequence[int],
    b: Sequence[int],
    *,
    dimensions: Sequence[int] | None = None,
    torus: bool = False,
) -> int:
    """Distancia de Manhattan, con corrección toroidal opcional.

    Es admisible y consistente para una retícula de von Neumann con coste unitario:
    nunca sobreestima, porque cada movimiento reduce como mucho en uno la suma de las
    diferencias por eje.

    Args:
        a: coordenada de origen.
        b: coordenada de destino.
        dimensions: tamaño de la retícula por eje. Obligatorio si ``torus`` es True.
        torus: si la retícula da la vuelta.
    """
    if not torus:
        return sum(abs(x - y) for x, y in zip(a, b, strict=True))
    if dimensions is None:
        raise ValueError("torus=True requiere 'dimensions'")
    total = 0
    for x, y, dim in zip(a, b, dimensions, strict=True):
        d = abs(x - y)
        total += min(d, dim - d)
    return total


def _reconstruct(came_from: dict[Any, Any], goal: Any) -> list[Any]:
    """Rehacer la ruta siguiendo los punteros de predecesor hacia atrás."""
    path = [goal]
    while path[-1] in came_from:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


def _neighbors(cell: Any, passable: Passable | None) -> Iterable[Any]:
    """Vecinos transitables de una celda, según ``cell.connections``."""
    for nb in cell.connections.values():
        if passable is None or passable(nb):
            yield nb


def bfs(start: Any, goal: Any, *, passable: Passable | None = None) -> SearchResult:
    """Búsqueda en anchura — búsqueda ciega (R&N §3.4.1).

    En una retícula de coste unitario BFS es óptima, así que sirve de oráculo contra el
    cual verificar que A\\* devuelve rutas de la misma longitud.

    Args:
        start: celda de origen.
        goal: celda de destino.
        passable: predicado de transitabilidad; None = todo transitable.
    """
    if start is goal:
        return SearchResult([start], 0, True)

    frontier: deque[Any] = deque([start])
    came_from: dict[Any, Any] = {}
    seen = {start}
    expanded = 0

    while frontier:
        cell = frontier.popleft()
        expanded += 1
        for nb in _neighbors(cell, passable):
            if nb in seen:
                continue
            seen.add(nb)
            came_from[nb] = cell
            if nb is goal:
                return SearchResult(_reconstruct(came_from, goal), expanded, True)
            frontier.append(nb)

    return SearchResult([], expanded, False)


def astar(
    start: Any,
    goal: Any,
    *,
    passable: Passable | None = None,
    dimensions: Sequence[int] | None = None,
    torus: bool = False,
) -> SearchResult:
    """Búsqueda A\\* con heurística de Manhattan (R&N §3.5.2).

    La heurística es consistente sobre una retícula de von Neumann con coste unitario,
    de modo que A\\* es óptima y no necesita reexpandir nodos ya cerrados.

    Args:
        start: celda de origen.
        goal: celda de destino.
        passable: predicado de transitabilidad; None = todo transitable.
        dimensions: tamaño de la retícula, necesario si ``torus`` es True.
        torus: si la retícula da la vuelta.
    """
    if start is goal:
        return SearchResult([start], 0, True)

    def h(cell: Any) -> int:
        return manhattan(
            cell.coordinate, goal.coordinate, dimensions=dimensions, torus=torus
        )

    tie = count()
    frontier: list[tuple[int, int, Any]] = [(h(start), next(tie), start)]
    came_from: dict[Any, Any] = {}
    g_score: dict[Any, int] = {start: 0}
    closed: set[Any] = set()
    expanded = 0

    while frontier:
        _, _, cell = heappop(frontier)
        if cell in closed:
            continue
        closed.add(cell)
        expanded += 1

        if cell is goal:
            return SearchResult(_reconstruct(came_from, goal), expanded, True)

        for nb in _neighbors(cell, passable):
            if nb in closed:
                continue
            tentative = g_score[cell] + 1
            if tentative < g_score.get(nb, 1 << 30):
                g_score[nb] = tentative
                came_from[nb] = cell
                heappush(frontier, (tentative + h(nb), next(tie), nb))

    return SearchResult([], expanded, False)
