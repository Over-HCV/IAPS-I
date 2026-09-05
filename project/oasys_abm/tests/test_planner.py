"""Corrección de la búsqueda: A\\* contra el oráculo BFS.

BFS es óptima en una retícula de coste unitario, así que sirve de referencia para
verificar que la heurística de Manhattan no rompe la optimalidad de A\\*
(Russell & Norvig, §3.4–3.5). Es el control de sanidad nº 5 de ``docs/02-design.md``.
"""

import random

from mesa.discrete_space import OrthogonalVonNeumannGrid
from oasys_abm.planner import astar, bfs, manhattan
import pytest


def rejilla(size: int = 15, *, torus: bool = False) -> OrthogonalVonNeumannGrid:
    return OrthogonalVonNeumannGrid(
        (size, size), torus=torus, random=random.Random(0xC0FFEE)
    )


def bloqueo(coords: set[tuple[int, int]]):
    return lambda cell: cell.coordinate not in coords


def ruta_valida(res, start, goal, passable) -> None:
    """Toda ruta devuelta debe ser transitable y realmente conectada."""
    assert res.path[0] is start
    assert res.path[-1] is goal
    for cell in res.path:
        assert passable(cell)
    for a, b in zip(res.path, res.path[1:], strict=False):
        assert b in a.connections.values()


@pytest.mark.parametrize("seed", [1, 7, 13, 42, 99])
def test_astar_es_optimo_contra_bfs(seed: int) -> None:
    """Con obstáculos aleatorios, A\\* y BFS deben coincidir en longitud de ruta."""
    rng = random.Random(seed)
    grid = rejilla(15)
    start, goal = grid[(0, 0)], grid[(14, 14)]
    obstaculos = {(rng.randrange(15), rng.randrange(15)) for _ in range(40)} - {
        (0, 0),
        (14, 14),
    }
    passable = bloqueo(obstaculos)

    a, b = astar(start, goal, passable=passable), bfs(start, goal, passable=passable)
    assert a.found == b.found
    if a.found:
        assert a.cost == b.cost
        ruta_valida(a, start, goal, passable)


def test_astar_expande_menos_que_bfs_con_destino_cercano() -> None:
    r"""El sentido de la heurística: menos nodos expandidos para el mismo resultado.

    El destino no puede ser la esquina opuesta: en una rejilla abierta de 20x20, ir de
    (0,0) a (19,19) hace que las 400 celdas estén sobre *alguna* ruta óptima, todas con
    el mismo f = g + h, y A\* no tiene nada que podar. La ventaja de la heurística
    aparece cuando el destino está dentro de la rejilla y BFS gasta su presupuesto
    explorando en todas las direcciones.
    """
    grid = rejilla(20)
    start, goal = grid[(0, 0)], grid[(5, 5)]
    a, b = astar(start, goal), bfs(start, goal)
    assert a.cost == b.cost == 10
    assert a.expanded < b.expanded


def test_astar_no_poda_cuando_todo_es_optimo() -> None:
    r"""Caso límite documentado: de esquina a esquina en rejilla abierta.

    Toda celda del rectángulo entre origen y destino pertenece a una ruta óptima, así
    que A\* debe expandirlas todas. No es un defecto de la heurística: es la geometría
    del problema, y conviene tenerlo escrito para no "arreglarlo" más adelante.
    """
    grid = rejilla(20)
    start, goal = grid[(0, 0)], grid[(19, 19)]
    a = astar(start, goal)
    assert a.cost == 38
    assert a.expanded == 400


def test_origen_igual_a_destino() -> None:
    grid = rejilla(5)
    cell = grid[(2, 2)]
    for res in (astar(cell, cell), bfs(cell, cell)):
        assert res.found
        assert res.path == [cell]
        assert res.cost == 0


def test_destino_inalcanzable() -> None:
    """Un muro completo alrededor del destino: no hay ruta y hay que decirlo."""
    grid = rejilla(9)
    start, goal = grid[(0, 0)], grid[(4, 4)]
    muro = {(3, 4), (5, 4), (4, 3), (4, 5)}
    passable = bloqueo(muro)
    for res in (
        astar(start, goal, passable=passable),
        bfs(start, goal, passable=passable),
    ):
        assert not res.found
        assert res.path == []


def test_manhattan_plano() -> None:
    assert manhattan((0, 0), (3, 4)) == 7
    assert manhattan((2, 2), (2, 2)) == 0


def test_manhattan_toroidal_toma_el_atajo() -> None:
    """En un toro de lado 10, de 0 a 9 hay un paso, no nueve."""
    assert manhattan((0, 0), (9, 0), dimensions=(10, 10), torus=True) == 1
    assert manhattan((0, 0), (9, 0)) == 9


def test_manhattan_toroidal_exige_dimensiones() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        manhattan((0, 0), (1, 1), torus=True)


def test_astar_en_toro_usa_el_atajo() -> None:
    """Con torus=True la heurística sigue siendo admisible y la ruta más corta."""
    grid = rejilla(10, torus=True)
    start, goal = grid[(0, 0)], grid[(9, 9)]
    a = astar(start, goal, dimensions=(10, 10), torus=True)
    b = bfs(start, goal)
    assert a.found
    assert a.cost == b.cost == 2
