"""El orden de activación como parámetro (``docs/roadmap-c4.md``, paquete 1)."""

from project.agents import Policy
from project.model import OASysWorld
import pytest

BASE: dict[str, object] = {
    "size": 13,
    "n_resources": 7,
    "max_steps": 200,
    "densidad_obstaculos": 0.12,
    "lambda_dinamismo": 0.25,
}
METRICAS = ("entregas", "pasos_deliberando", "n_ediciones", "tareas_fallidas")


def _metricas(**kw: object) -> tuple[int, ...]:
    m = OASysWorld(**{**BASE, **kw})  # type: ignore[arg-type]
    m.run_model()
    return tuple(getattr(m.collector, k) for k in METRICAS) + (m.divergencias_reales,)


@pytest.mark.parametrize("rng", [0, 1, 2])
def test_orden_aleatorio_es_reproducible(rng: int) -> None:
    """Con la misma semilla, dos corridas con orden aleatorio son idénticas."""
    kw = {"policy": Policy.CLOSED_LOOP, "orden_aleatorio": True, "rng": rng}
    assert _metricas(**kw) == _metricas(**kw)


def test_por_defecto_el_recolector_actua_primero() -> None:
    """Sin el parámetro el orden es fijo: el valor explícito False da lo mismo."""
    for rng in range(3):
        por_defecto = _metricas(policy=Policy.CLOSED_LOOP, rng=rng)
        explicito = _metricas(policy=Policy.CLOSED_LOOP, orden_aleatorio=False, rng=rng)
        assert por_defecto == explicito


def test_el_orden_aleatorio_cambia_la_corrida() -> None:
    """El sorteo de verdad altera la dinámica en alguna semilla (no es un no-op)."""
    distintas = sum(
        _metricas(policy=Policy.CLOSED_LOOP, rng=s)
        != _metricas(policy=Policy.CLOSED_LOOP, orden_aleatorio=True, rng=s)
        for s in range(5)
    )
    assert distintas > 0
