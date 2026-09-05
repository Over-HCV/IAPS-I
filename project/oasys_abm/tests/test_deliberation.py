"""La deliberación como acción con duración, progreso e interrupción."""

from oasys_abm.book import Line, LineOp
from oasys_abm.deliberation import Deliberation, DeliberationState
import pytest


def nueva(duration: int = 3) -> Deliberation:
    return Deliberation(
        duration=duration, from_idx=0, lines=[Line(LineOp.SCAN)], label="test"
    )


def test_duracion_cero_nace_terminada() -> None:
    """Deliberar gratis (c=0) no cuesta ningún tick."""
    d = Deliberation(duration=0, from_idx=0)
    assert d.is_complete
    assert d.progress == 1.0
    assert d.remaining == 0


def test_duracion_negativa_es_error() -> None:
    with pytest.raises(ValueError, match="negativa"):
        Deliberation(duration=-1, from_idx=0)


def test_consume_ticks_hasta_terminar() -> None:
    d = nueva(3)
    assert d.tick() is DeliberationState.ACTIVE
    assert d.tick() is DeliberationState.ACTIVE
    assert d.tick() is DeliberationState.COMPLETED
    assert d.is_complete


def test_progreso_es_monotono_y_acotado() -> None:
    d = nueva(4)
    anterior = d.progress
    for _ in range(6):
        d.tick()
        assert d.progress >= anterior
        assert 0.0 <= d.progress <= 1.0
        anterior = d.progress
    assert d.progress == 1.0


def test_remaining_llega_a_cero() -> None:
    d = nueva(2)
    assert d.remaining == 2
    d.tick()
    assert d.remaining == 1
    d.tick()
    assert d.remaining == 0


def test_tick_es_idempotente_tras_terminar() -> None:
    """El bucle del agente no debería tener que comprobar el estado antes de avanzar."""
    d = nueva(1)
    d.tick()
    elapsed = d.elapsed
    for _ in range(5):
        assert d.tick() is DeliberationState.COMPLETED
    assert d.elapsed == elapsed


def test_interrupcion_descarta_el_resultado() -> None:
    """Los ticks gastados se pierden: es la forma operacional del thrashing."""
    d = nueva(5)
    d.tick()
    d.tick()
    assert d.interrupt() is True
    assert d.state is DeliberationState.INTERRUPTED
    assert d.lines == []
    assert not d.is_complete
    assert d.elapsed == 2


def test_no_se_puede_interrumpir_lo_ya_terminado() -> None:
    d = nueva(1)
    d.tick()
    assert d.interrupt() is False
    assert d.is_complete
    assert d.lines != []


def test_interrumpir_dos_veces_no_hace_nada() -> None:
    d = nueva(5)
    assert d.interrupt() is True
    assert d.interrupt() is False


def test_una_interrumpida_no_avanza() -> None:
    d = nueva(5)
    d.interrupt()
    assert d.tick() is DeliberationState.INTERRUPTED
    assert d.elapsed == 0
