"""Tests del análisis de sensibilidad (paquete C5-S).

Los casos sintéticos tienen η² conocido analíticamente; el último corre sobre los CSV
guardados y se salta si no existen.
"""

from itertools import product

import numpy as np
import pandas as pd
import pytest

from project import sensibilidad as s
from project.analysis import RESULTS


def _factorial(niveles_a, niveles_b, reps=1):
    filas = [
        {"A": a, "B": b, "rng": r}
        for a, b, r in product(niveles_a, niveles_b, range(reps))
    ]
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- η²


def test_eta2_factor_determinante_y_factor_irrelevante():
    df = _factorial([0, 1, 2], ["x", "y"], reps=3)
    df["y_"] = 2.0 * df["A"]  # sin ruido: A lo explica todo, B nada
    assert s.eta2(df, "A", "y_") == pytest.approx(1.0)
    assert s.eta2(df, "B", "y_") == pytest.approx(0.0)


def test_eta2_metrica_constante_es_cero():
    df = _factorial([0, 1], [0, 1])
    df["y_"] = 7.0
    assert s.eta2(df, "A", "y_") == 0.0


def test_eta2_2x2_balanceado_con_ss_conocidas():
    # Celdas (A, B) -> y: (0,0)=0, (0,1)=2, (1,0)=4, (1,1)=10, dos réplicas idénticas.
    # Media global 4; SS_total = 2·(16+4+0+36) = 112.
    # Medias de A: 1 y 7 -> SS_A = 4·(9+9) = 72.   Medias de B: 2 y 6 -> SS_B = 4·(4+4) = 32.
    # Resto (interacción) = 112 − 72 − 32 = 8.
    df = _factorial([0, 1], [0, 1], reps=2)
    valores = {(0, 0): 0.0, (0, 1): 2.0, (1, 0): 4.0, (1, 1): 10.0}
    df["y_"] = [valores[(a, b)] for a, b in zip(df.A, df.B, strict=True)]
    assert s.eta2(df, "A", "y_") == pytest.approx(72 / 112)
    assert s.eta2(df, "B", "y_") == pytest.approx(32 / 112)
    # η² parcial con modelo aditivo: SS_res = SS de interacción = 8.
    parcial = s.eta2_parcial(df, ["A", "B"], "y_")
    assert parcial["A"] == pytest.approx(72 / 80)
    assert parcial["B"] == pytest.approx(32 / 40)


def test_eta2_parcial_un_factor_coincide_con_eta2():
    rng = np.random.default_rng(0)
    df = _factorial([0, 1, 2], [0], reps=10)
    df["y_"] = df["A"] + rng.normal(size=len(df))
    assert s.eta2_parcial(df, ["A"], "y_")["A"] == pytest.approx(s.eta2(df, "A", "y_"))


def test_sensibilidad_por_grupo_y_descarta_factores_constantes():
    df = pd.concat(
        [
            _factorial([0, 1, 2], [0, 1], reps=2).assign(politica="OPEN_LOOP"),
            _factorial([0, 1, 2], [0, 1], reps=2).assign(politica="CLOSED_LOOP"),
        ],
        ignore_index=True,
    )
    df["C"] = 5  # un solo nivel: no debe aparecer
    df["y_"] = np.where(df.politica == "OPEN_LOOP", df["A"], 3.0 * df["B"])
    t = s.sensibilidad(df, ["A", "B", "C"], "y_")
    assert list(t.columns) == ["politica", "factor", "eta2", "eta2_parcial"]
    assert set(t.factor) == {"A", "B"}
    assert list(dict.fromkeys(t.politica)) == ["OPEN_LOOP", "CLOSED_LOOP"]
    v = t.set_index(["politica", "factor"])["eta2"]
    assert v[("OPEN_LOOP", "A")] == pytest.approx(1.0)
    assert v[("OPEN_LOOP", "B")] == pytest.approx(0.0)
    assert v[("CLOSED_LOOP", "B")] == pytest.approx(1.0)
    assert v[("CLOSED_LOOP", "A")] == pytest.approx(0.0)


# ------------------------------------------------------------------- delta pareada


def test_delta_pareada_cancela_el_ruido_de_semilla():
    # Ambas políticas comparten un ruido enorme por semilla; la diferencia depende solo
    # de A. Sin el pareo, A explicaría casi nada; con él, todo.
    rng = np.random.default_rng(1)
    base = _factorial([0, 1, 2], ["x", "y"], reps=8)
    ruido = dict(enumerate(rng.normal(scale=100, size=8)))
    abierto = base.assign(politica="OPEN_LOOP")
    cerrado = base.assign(politica="CLOSED_LOOP")
    abierto["utilidad_neta"] = abierto.rng.map(ruido) + 5.0 * abierto.A
    cerrado["utilidad_neta"] = cerrado.rng.map(ruido)
    df = pd.concat([cerrado, abierto.sample(frac=1, random_state=0)], ignore_index=True)

    r = s.sensibilidad_delta(df, factores=["A", "B"])
    assert len(r.pares) == len(base)
    assert np.allclose(r.pares["delta"], 5.0 * r.pares["A"])
    e = r.eta2.set_index("factor")["eta2"]
    assert e["A"] == pytest.approx(1.0)
    assert e["B"] == pytest.approx(0.0)
    m = r.medias[r.medias.factor == "A"].set_index("nivel")["media"]
    assert m.to_dict() == pytest.approx({0: 0.0, 1: 5.0, 2: 10.0})
    # Sin parear, el ruido de semilla se come la señal.
    assert s.eta2(abierto, "A", "utilidad_neta") < 0.1


def test_delta_rechaza_pares_ambiguos_y_politicas_ausentes():
    df = _factorial([0, 1], [0], reps=2).assign(politica="OPEN_LOOP", utilidad_neta=1.0)
    with pytest.raises(ValueError, match="faltan"):
        s.sensibilidad_delta(df, factores=["A"])
    dup = pd.concat(
        [df, df, df.assign(politica="CLOSED_LOOP")], ignore_index=True
    )
    with pytest.raises(ValueError, match="no identifican"):
        s.sensibilidad_delta(dup, factores=["A"])


# --------------------------------------------------------------- datos guardados


def test_barridos_coinciden_con_experiments():
    from project.experiments import SWEEPS

    for nombre, factores in s.BARRIDOS.items():
        variados = {
            k for k, v in SWEEPS[nombre].items() if isinstance(v, list) and k != "policy"
        }
        assert set(factores) == variados, nombre


@pytest.mark.parametrize("nombre", list(s.BARRIDOS))
def test_csv_reales_eta2_acotado(nombre):
    if not (RESULTS / f"{nombre}.csv").exists():
        pytest.skip(f"falta results/{nombre}.csv")
    df = s.cargar(nombre)
    factores = s.BARRIDOS[nombre]
    t = s.sensibilidad(df, factores)
    assert not t.empty
    assert t["eta2"].between(0, 1).all()
    assert t["eta2_parcial"].between(0, 1).all()
    # Diseño factorial balanceado: los η² de los efectos principales suman ≤ 1.
    for politica, sub in df.groupby("politica"):
        celdas = sub.groupby(factores).size()
        if celdas.nunique() == 1:
            assert t[t.politica == politica]["eta2"].sum() <= 1 + 1e-9
    if {"OPEN_LOOP", "CLOSED_LOOP"} <= set(df.politica):
        r = s.sensibilidad_delta(df, factores=factores)
        assert r.eta2["eta2"].between(0, 1).all()
        assert r.eta2["eta2"].sum() <= 1 + 1e-9
