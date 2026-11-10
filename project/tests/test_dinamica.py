"""Series temporales agregadas (``docs/roadmap-c4.md``, paquete 3)."""

from project import analysis as an
from project.experiments import COLUMNAS_DINAMICA, correr_dinamica
import pandas as pd
import pytest

CHICA = {
    "size": 11,
    "n_resources": 5,
    "capacidad": 2,
    "max_steps": 23,
    "policy": ["OPEN_LOOP", "CLOSED_LOOP"],
    "lambda_dinamismo": [0.0, 0.3],
    "costo_edicion": 2,
}


def test_correr_dinamica_decima_y_conserva_el_ultimo_tick() -> None:
    """Con ``cada=5`` se guardan los múltiplos de 5 y el último tick (23)."""
    df = correr_dinamica(CHICA, cada=5, semillas=[0, 1])
    assert list(df.columns) == COLUMNAS_DINAMICA
    ticks = sorted(df.tick.unique())
    assert ticks == [0, 5, 10, 15, 20, 23]
    # Una fila por (corrida, tick): 2 políticas × 2 λ × 2 semillas × 6 ticks.
    assert len(df) == 2 * 2 * 2 * 6
    # Las entregas son acumuladas: nunca bajan a lo largo de una corrida.
    for _, g in df.groupby(["politica", "lambda_dinamismo", "rng"]):
        assert g.sort_values("tick").entregas.is_monotonic_increasing


def test_agregar_tiempo_media_y_error_estandar() -> None:
    """Media y SEM por tick sobre un DataFrame sintético con valores conocidos."""
    df = pd.DataFrame(
        {
            "tick": [0, 0, 10, 10],
            "politica": ["OPEN_LOOP"] * 4,
            "lambda_dinamismo": [0.1] * 4,
            "entregas": [0.0, 2.0, 4.0, 8.0],
        }
    )
    t = an.agregar_tiempo(df, "entregas").set_index("x")
    assert t.loc[0, "y"] == pytest.approx(1.0)
    assert t.loc[10, "y"] == pytest.approx(6.0)
    # std muestral de (4, 8) = 2.828..., SEM = std / sqrt(2) = 2.
    assert t.loc[10, "err"] == pytest.approx(2.0)
    assert set(t.columns) == {"y", "err", "serie", "faceta"}
