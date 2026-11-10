"""Tests de la calibración ABC (paquete C5-A)."""

from __future__ import annotations

from project import calibracion as cal
from project.agents import Policy
from project.model import OASysWorld
import numpy as np
import pandas as pd
import pytest


def _tabla_sintetica(n: int = 4000, rng: int = 0) -> pd.DataFrame:
    """Tabla cuyos estadísticos son función determinista de (λ, p).

    Las cinco columnas responden a (λ, p) de forma distinta y con escalas dispares, para
    que la estandarización importe: sin ella mandaría la última, que vale 100 veces más.
    """
    gen = np.random.default_rng(rng)
    lam = gen.uniform(*cal.PRIOR["lam"], size=n)
    p = gen.uniform(*cal.PRIOR["p"], size=n)
    stats = np.column_stack(
        [1 - lam, lam * p, lam**2, p - 0.5 * lam, 100 * (lam + p)]
    )
    tabla = pd.DataFrame(stats, columns=cal.ESTADISTICOS)
    tabla.insert(0, "p", p)
    tabla.insert(0, "lam", lam)
    return tabla


def _stats_sinteticos(lam: float, p: float) -> np.ndarray:
    return np.array([1 - lam, lam * p, lam**2, p - 0.5 * lam, 100 * (lam + p)])


class TestABCSintetico:
    def test_posterior_concentrada_en_la_verdad(self):
        tabla = _tabla_sintetica()
        res = cal.abc_rechazo(_stats_sinteticos(0.25, 0.7), tabla, frac=0.02)
        assert len(res.posterior) == 80
        assert res.posterior["lam"].mean() == pytest.approx(0.25, abs=0.02)
        assert res.posterior["p"].mean() == pytest.approx(0.7, abs=0.03)
        ic = res.intervalos
        assert ic.loc["lam", "q05"] <= 0.25 <= ic.loc["lam", "q95"]
        assert ic.loc["p", "q05"] <= 0.7 <= ic.loc["p", "q95"]
        # La posterior debe ser mucho más angosta que el prior.
        assert ic.loc["lam", "q95"] - ic.loc["lam", "q05"] < 0.1
        assert ic.loc["p", "q95"] - ic.loc["p", "q05"] < 0.1

    def test_acepta_los_mas_cercanos_ordenados(self):
        tabla = _tabla_sintetica(500)
        res = cal.abc_rechazo(_stats_sinteticos(0.1, 0.9), tabla, frac=0.1)
        assert len(res.posterior) == 50
        assert res.posterior["distancia"].is_monotonic_increasing
        assert set(res.intervalos.columns) == {"q05", "q50", "q95"}
        assert list(res.intervalos.index) == ["lam", "p"]

    def test_estadistico_constante_no_rompe(self):
        tabla = _tabla_sintetica(500)
        tabla["entregas"] = 3.0  # SD y MAD nulas: escala 1, no NaN
        res = cal.abc_rechazo(_stats_sinteticos(0.25, 0.7), tabla, frac=0.05)
        assert np.isfinite(res.posterior["distancia"]).all()


class TestEstadisticos:
    def test_modelo_y_fila_coinciden(self):
        modelo = OASysWorld(**cal.DESPLIEGUE, lambda_dinamismo=0.25, rng=3)
        while modelo.running:
            modelo.step()
        fila = modelo.datacollector.get_model_vars_dataframe().iloc[-1].to_dict()
        fila["max_steps"] = modelo.max_steps
        np.testing.assert_allclose(cal.estadisticos(modelo), cal.estadisticos(fila))
        assert len(cal.estadisticos(modelo)) == len(cal.ESTADISTICOS)

    def test_simular_reproducible(self):
        a = cal.simular(0.2, 0.8, [0, 1])
        b = cal.simular(0.2, 0.8, [0, 1])
        np.testing.assert_array_equal(a, b)

    def test_sin_dinamismo_no_hay_fallos(self):
        s = dict(zip(cal.ESTADISTICOS, cal.simular(0.0, 0.7, [0]), strict=True))
        assert s["divergencias_reales"] == 0
        assert s["tareas_fallidas"] == 0


def test_recomendar_distribucion():
    posterior = pd.DataFrame({"lam": [0.02, 0.24, 0.26, 0.49], "p": [0.6, 0.7, 0.95, 0.9]})
    rec = cal.recomendar(posterior)
    assert set(rec["fuente"]) == {"principal (λ)", "competencia (λ, p)", "combinada"}
    sumas = rec.groupby("fuente")["fraccion"].sum()
    np.testing.assert_allclose(sumas.to_numpy(), 1.0)
    # `competencia` solo compara políticas con plan.
    con_plan = rec[rec["fuente"] == "competencia (λ, p)"]["politica"]
    assert all(Policy(pol).planifica for pol in con_plan)


def test_combinada_es_dos_etapas():
    """Si `principal` elige no planificar, manda; si planifica, decide `competencia`."""
    principal = pd.DataFrame(
        {
            "costo_edicion": 5,
            "radio": "3",
            "lambda_dinamismo": [0.0, 0.0, 0.5, 0.5],
            "politica": ["OPEN_LOOP", "MODEL_BASED", "OPEN_LOOP", "MODEL_BASED"],
            "utilidad_neta": [10.0, 5.0, 1.0, 8.0],
        }
    )
    competencia = pd.DataFrame(
        {
            "costo_edicion": 5,
            "radio": "3",
            "lambda_dinamismo": [0.0, 0.0, 0.5, 0.5],
            "competencia": 0.9,
            "politica": ["OPEN_LOOP", "CLOSED_LOOP", "OPEN_LOOP", "CLOSED_LOOP"],
            "utilidad_neta": [5.0, 9.0, 5.0, 9.0],
        }
    )
    posterior = pd.DataFrame({"lam": [0.1, 0.7], "p": [0.9, 0.9]})
    rec = cal.recomendar(posterior, principal, competencia)
    comb = rec[rec["fuente"] == "combinada"].set_index("politica")["fraccion"]
    assert comb.to_dict() == {"CLOSED_LOOP": 0.5, "MODEL_BASED": 0.5}


def test_cargar_referencia_sin_archivo(tmp_path, monkeypatch):
    monkeypatch.setattr(cal, "RUTA_REFERENCIA", tmp_path / "abc.parquet")
    with pytest.raises(FileNotFoundError, match="--referencia"):
        cal.cargar_referencia()


@pytest.mark.slow
def test_lambda_recuperado_tabla_real_pequena(tmp_path):
    """Con una tabla real de 300 muestras, λ* = 0.25 cae en el IC del 90 %."""
    tabla = cal.tabla_referencia(300, rng=1, ruta=tmp_path / "abc.parquet")
    assert (tmp_path / "abc.parquet").exists()
    assert len(tabla) == 300
    res = cal.abc_rechazo(cal.observar(0.25, 0.7), tabla, frac=0.1)
    ic = res.intervalos
    assert ic.loc["lam", "q05"] <= 0.25 <= ic.loc["lam", "q95"]
