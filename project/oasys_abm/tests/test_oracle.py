"""El replanificador abstraído: competencia, modos de fallo y reproducibilidad."""

import random

from mesa.discrete_space import OrthogonalVonNeumannGrid
from oasys_abm.book import Book, Line, LineOp
from oasys_abm.oracle import Oracle, ProposalKind, RepairRequest
import pytest


def escenario(
    *, p: float, seed: int = 7, true_goal: tuple[int, int] | None = (8, 8)
) -> tuple[Oracle, RepairRequest]:
    """Agente en (0,0), cree que el recurso está en (2,2), realmente está en (8,8)."""
    grid = OrthogonalVonNeumannGrid((12, 12), random=random.Random(seed))
    oracle = Oracle(
        p=p,
        cost=3,
        random=random.Random(seed),
        dimensions=(12, 12),
        cells=grid.all_cells.cells,
    )
    req = RepairRequest(
        book=Book([Line(LineOp.SCAN)]),
        from_idx=0,
        origin=grid[(0, 0)],
        true_goal=None if true_goal is None else grid[true_goal],
        believed_goal=grid[(2, 2)],
        resource_id="r0",
        tail=(Line(LineOp.DELIVER, None, locked=True),),
    )
    return oracle, req


def test_competencia_maxima_siempre_acierta() -> None:
    oracle, req = escenario(p=1.0)
    for _ in range(50):
        assert oracle.propose(req).kind is ProposalKind.OPTIMAL


def test_competencia_nula_nunca_acierta() -> None:
    """Con p=0 y una creencia equivocada, toda propuesta es un fallo."""
    oracle, req = escenario(p=0.0)
    kinds = {oracle.propose(req).kind for _ in range(50)}
    assert ProposalKind.OPTIMAL not in kinds
    assert kinds <= {ProposalKind.STALE_TARGET, ProposalKind.DETOUR}


def test_aparecen_los_dos_modos_de_fallo() -> None:
    oracle, req = escenario(p=0.0, seed=3)
    kinds = {oracle.propose(req).kind for _ in range(80)}
    assert kinds == {ProposalKind.STALE_TARGET, ProposalKind.DETOUR}


def test_sin_observacion_no_hay_acierto_posible() -> None:
    """Si el agente no ve el objetivo, lo mejor que puede hacer es ir a su creencia.

    La ceguera no es un fallo del replanificador: es una limitación del sensor, y se
    clasifica como STALE_TARGET incluso con competencia máxima.
    """
    oracle, req = escenario(p=1.0, true_goal=None)
    for _ in range(20):
        assert oracle.propose(req).kind is ProposalKind.STALE_TARGET


def test_creencia_correcta_hace_inofensivo_el_fallo() -> None:
    """Si la creencia coincide con la realidad, equivocarse de objetivo no daña."""
    grid = OrthogonalVonNeumannGrid((12, 12), random=random.Random(1))
    oracle = Oracle(
        p=0.0,
        cost=1,
        random=random.Random(1),
        dimensions=(12, 12),
        cells=grid.all_cells.cells,
    )
    req = RepairRequest(
        book=Book([]),
        from_idx=0,
        origin=grid[(0, 0)],
        true_goal=grid[(4, 4)],
        believed_goal=grid[(4, 4)],
        resource_id="r0",
    )
    kinds = {oracle.propose(req).kind for _ in range(50)}
    assert ProposalKind.STALE_TARGET not in kinds


@pytest.mark.parametrize("p", [0.0, 0.5, 1.0])
def test_la_propuesta_conserva_la_cola_comprometida(p: float) -> None:
    """El DELIVER bloqueado debe sobrevivir a cualquier propuesta, buena o mala."""
    oracle, req = escenario(p=p)
    for _ in range(20):
        prop = oracle.propose(req)
        assert prop.feasible
        assert prop.lines[-1] == Line(LineOp.DELIVER, None, locked=True)
        assert prop.lines[-2].op is LineOp.PICK


def test_la_propuesta_es_aplicable_al_plan() -> None:
    """Una propuesta debe pasar la validación de replace_suffix sin ser rechazada."""
    oracle, req = escenario(p=0.5)
    book = Book([Line(LineOp.SCAN), Line(LineOp.DELIVER, None, locked=True)])
    prop = oracle.propose(
        RepairRequest(
            book=book,
            from_idx=0,
            origin=req.origin,
            true_goal=req.true_goal,
            believed_goal=req.believed_goal,
            resource_id="r0",
            tail=(Line(LineOp.DELIVER, None, locked=True),),
        )
    )
    book.replace_suffix(prop.from_idx, prop.lines)
    assert book.locked_render() == [Line(LineOp.DELIVER, None, locked=True)]


def test_desvio_es_mas_largo_que_lo_optimo() -> None:
    """El fallo por desvío llega al objetivo correcto, pero gastando de más.

    Que sea *estrictamente* más largo es una invariante: si la geometría no permite
    desviar, el oráculo devuelve la ruta óptima y la etiqueta como OPTIMAL en vez de
    fingir un fallo que no ocurrió.
    """
    oracle_ok, req = escenario(p=1.0, seed=11)
    optimo = oracle_ok.propose(req)
    oracle_mal, req = escenario(p=0.0, seed=11)
    desvios = [
        p
        for p in (oracle_mal.propose(req) for _ in range(60))
        if p.kind is ProposalKind.DETOUR
    ]
    assert desvios
    assert all(len(d.lines) > len(optimo.lines) for d in desvios)


def test_objetivo_inalcanzable_da_propuesta_infeasible() -> None:
    grid = OrthogonalVonNeumannGrid((9, 9), random=random.Random(0))
    muro = {(3, 4), (5, 4), (4, 3), (4, 5)}
    oracle = Oracle(
        p=1.0,
        cost=1,
        random=random.Random(0),
        passable=lambda c: c.coordinate not in muro,
        dimensions=(9, 9),
    )
    req = RepairRequest(
        book=Book([]),
        from_idx=0,
        origin=grid[(0, 0)],
        true_goal=grid[(4, 4)],
        believed_goal=grid[(4, 4)],
        resource_id="r0",
    )
    prop = oracle.propose(req)
    assert prop.kind is ProposalKind.INFEASIBLE
    assert not prop.feasible
    assert prop.lines == []


def test_misma_semilla_mismas_propuestas() -> None:
    """Control de sanidad nº 4: reproducibilidad."""
    a, req_a = escenario(p=0.5, seed=99)
    b, req_b = escenario(p=0.5, seed=99)
    ka = [a.propose(req_a).kind for _ in range(30)]
    kb = [b.propose(req_b).kind for _ in range(30)]
    assert ka == kb


def test_sin_pool_de_celdas_no_se_finge_un_desvio() -> None:
    """Sin celdas de las que muestrear, el desvío es imposible y se dice la verdad."""
    grid = OrthogonalVonNeumannGrid((10, 10), random=random.Random(5))
    oracle = Oracle(p=0.0, cost=1, random=random.Random(5), dimensions=(10, 10))
    req = RepairRequest(
        book=Book([]),
        from_idx=0,
        origin=grid[(0, 0)],
        true_goal=grid[(6, 6)],
        believed_goal=grid[(6, 6)],
        resource_id="r0",
    )
    kinds = {oracle.propose(req).kind for _ in range(40)}
    assert ProposalKind.DETOUR not in kinds
