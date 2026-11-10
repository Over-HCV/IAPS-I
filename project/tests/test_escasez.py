"""Regresión del barrido de escasez (paquete 4 de ``docs/roadmap-c4.md``).

La celda ``n_resources=8`` de cada régimen usa los mismos parámetros y semillas que filas
ya guardadas: ``escasez`` las de ``principal`` (``c=5``) y las de ``conocimiento`` (``r=3``)
para ``KNOWLEDGE_BASED``, y ``escasez_inf`` las de ``control2``. Si no coinciden corrida a
corrida, algo cambió en el modelo entre barridos y los CSV dejaron de ser comparables.
"""

import pandas as pd
from project.analysis import RESULTS
import pytest

METRICAS = ["entregas", "utilidad_neta", "pasos_deliberando"]
CLAVES = ["politica", "lambda_dinamismo", "rng"]


def _leer(nombre: str) -> pd.DataFrame:
    ruta = RESULTS / f"{nombre}.csv"
    if not ruta.exists():
        pytest.skip(f"falta {ruta}")
    return pd.read_csv(ruta)


def _comparar(nuevo: pd.DataFrame, viejo: pd.DataFrame, politicas: list[str]) -> None:
    """Las filas de ``nuevo`` con ``n_resources=8`` son exactamente las de ``viejo``."""
    a = nuevo[(nuevo.n_resources == 8) & nuevo.politica.isin(politicas)]
    b = viejo[viejo.politica.isin(politicas) & viejo.lambda_dinamismo.isin(
        a.lambda_dinamismo.unique()
    )]
    assert not a.empty
    a = a.set_index(CLAVES)[METRICAS].sort_index()
    b = b.set_index(CLAVES)[METRICAS].sort_index()
    assert a.index.equals(b.index), "las celdas de los dos barridos no coinciden"
    pd.testing.assert_frame_equal(a, b, check_dtype=False)


def test_escasez_reproduce_principal() -> None:
    principal = _leer("principal")
    _comparar(
        _leer("escasez"),
        principal[principal.costo_edicion == 5],
        ["MODEL_BASED", "OPEN_LOOP", "COLD_RESTART", "CLOSED_LOOP"],
    )


def test_escasez_reproduce_conocimiento() -> None:
    conocimiento = _leer("conocimiento")
    _comparar(
        _leer("escasez"),
        conocimiento[conocimiento.radio == 3],
        ["KNOWLEDGE_BASED"],
    )


def test_escasez_inf_reproduce_control2() -> None:
    _comparar(_leer("escasez_inf"), _leer("control2"), ["OPEN_LOOP", "CLOSED_LOOP"])


@pytest.mark.parametrize(("nombre", "corridas"), [("escasez", 2400), ("escasez_inf", 1440)])
def test_tamano_del_barrido(nombre: str, corridas: int) -> None:
    df = _leer(nombre)
    assert len(df) == corridas
    assert sorted(df.n_resources.unique()) == [2, 4, 8, 16]
