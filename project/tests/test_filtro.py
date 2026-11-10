"""El filtro de ``BAYESIAN`` (``docs/roadmap-c5.md``, C5-B).

El filtro tiene que ser tres cosas a la vez: una distribución (masa 1), **sólida** (su
soporte es exactamente la región posible de KB-2, contra la que se prueba tick a tick) y
**calibrada** (cuando dice «probabilidad x», acierta con frecuencia x). Y la política tiene
que reducirse a ``CLOSED_LOOP`` cuando no hay incertidumbre que gestionar (HB2).
"""

import math
from typing import Any

import numpy as np
from project import agents
from project.conocimiento import BaseConocimiento, Vecindario, expandir
from project.filtro import BetaBernoulli, CreenciaBayesiana, FiltroRecurso, MallaFiltro
from project.model import OASysWorld
import pytest

SEMILLAS = range(8)

PARAMETROS: dict[str, Any] = {
    "size": 13,
    "n_resources": 7,
    "max_steps": 250,
    "densidad_obstaculos": 0.12,
}

POR_POLITICA = ["politica", "n_consultas", "lambda_estimado"]


def correr(policy: str, **kw: Any) -> OASysWorld:
    """Una corrida corta con parámetros de test."""
    modelo = OASysWorld(policy=policy, **{**PARAMETROS, **kw})
    modelo.run_model()
    return modelo


def serie(modelo: OASysWorld) -> Any:
    """Todas las métricas tick a tick, sin las que nombran o solo tiene una política."""
    return modelo.datacollector.get_model_vars_dataframe().drop(columns=POR_POLITICA)


def mundo(rng: int = 0) -> OASysWorld:
    """Un mundo con una componente de la base grande, para probar el filtro suelto."""
    m = OASysWorld(size=13, densidad_obstaculos=0.2, rng=rng)
    assert len(m.libres) > 50
    return m


# ------------------------------------------------------------------ Beta–Bernoulli


def test_beta_bernoulli_es_la_posterior_conjugada() -> None:
    """Prior Beta(1,1): media 1/2; tras s éxitos en n, media (1+s)/(2+n)."""
    b = BetaBernoulli()
    assert b.media == 0.5 and b.n == 0
    for exito in [True, False, False, True, False]:
        b.observar(exito)
    assert b.n == 5
    assert b.media == pytest.approx(3 / 7)
    a, c = 3, 4
    assert b.desviacion == pytest.approx(
        math.sqrt(a * c / ((a + c) ** 2 * (a + c + 1)))
    )


# ------------------------------------------------------------------ el filtro


def test_la_masa_se_conserva_y_propagar_no_muta() -> None:
    """Predecir conserva la masa; corregir renormaliza; ``propagado`` no toca el filtro."""
    m = mundo()
    malla = MallaFiltro(m.libres)
    f = FiltroRecurso(malla, m.libres[len(m.libres) // 2])
    rnd = np.random.default_rng(0)
    for _ in range(15):
        f.predecir(0.3)
        assert f.p.sum() == pytest.approx(1.0)
        vistas = [m.libres[i] for i in rnd.choice(len(m.libres), 8, replace=False)]
        f.corregir(vistas)
        assert f.p.sum() == pytest.approx(1.0)
        assert all(f.prob(c) == 0 for c in vistas)
    antes = f.p.copy()
    q = f.propagado(0.3, 6)
    assert np.array_equal(f.p, antes)
    assert q.sum() == pytest.approx(1.0) and not np.array_equal(q, antes)


@pytest.mark.parametrize("lam", [0.05, 0.3, 0.9])
def test_un_avistamiento_sin_poda_da_la_bola_geodesica(lam: float) -> None:
    """Tras ``k`` predicciones sin corregir, el soporte es la bola geodésica de radio k."""
    m = mundo(1)
    malla = MallaFiltro(m.libres)
    origen = m.libres[len(m.libres) // 3]
    f = FiltroRecurso(malla, origen)
    for k in range(1, 12):
        f.predecir(lam)
        assert f.soporte() == expandir([origen], k, Vecindario())


def vigilar(modelo: OASysWorld, registro: dict[str, int]) -> None:
    """Junto a cada observación de ``BAYESIAN``, alimentar una KB-2 con lo mismo y comparar.

    Comprueba tick a tick: soporte del filtro == región posible (con λ>0 la KB sabe que
    el mundo es dinámico), masa 1, y celda real con probabilidad positiva (solidez).
    """
    c = modelo.collector
    kb = BaseConocimiento(dinamico=True)
    original_percibir = c.conocimiento.percibir
    original_observar = c.observar

    def percibir(vistos: Any, visibles: Any, *, derivas: int, t: int) -> None:
        original_percibir(vistos, visibles, derivas=derivas, t=t)
        kb.percibir(vistos, visibles, derivas=derivas, t=t)

    def observar() -> None:
        original_observar()
        cre = c.conocimiento
        assert isinstance(cre, CreenciaBayesiana)
        reales = {r.rid: r.cell for r in modelo.recursos()}
        assert set(cre.filtros) == set(kb.regiones)
        for rid, filtro in cre.filtros.items():
            assert filtro.soporte() == kb.regiones[rid].celdas, (
                f"tick {modelo.steps}, {rid}"
            )
            assert filtro.p.sum() == pytest.approx(1.0)
            assert filtro.prob(reales[rid]) > 0
            registro["max"] = max(registro.get("max", 0), len(kb.regiones[rid]))

    def recoger(rid: str, t: int, original: Any = c.conocimiento.recoger) -> None:
        original(rid, t)
        kb.recoger(rid, t)

    c.conocimiento.percibir = percibir  # type: ignore[method-assign]
    c.conocimiento.recoger = recoger  # type: ignore[method-assign]
    c.observar = observar  # type: ignore[method-assign]


@pytest.mark.parametrize("orden_aleatorio", [False, True])
@pytest.mark.parametrize("radio", [1, 3])
@pytest.mark.parametrize("lam", [0.2, 0.5])
def test_el_soporte_es_la_region_de_kb2_y_es_solido(
    lam: float, radio: int, orden_aleatorio: bool
) -> None:
    """Soporte del filtro == región posible de KB-2, tick a tick, y la celda real dentro.

    Es lo que ata C5-B a KB-2: la probabilidad refina la lógica, nunca la contradice.
    """
    registro: dict[str, int] = {}
    for s in range(5):
        m = OASysWorld(
            policy=agents.Policy.BAYESIAN,
            lambda_dinamismo=lam,
            radio=radio,
            orden_aleatorio=orden_aleatorio,
            rng=s,
            **PARAMETROS,
        )
        vigilar(m, registro)
        m.run_model()
    assert registro["max"] > 10


# --------------------------------------------------------------- λ aprendido


@pytest.mark.parametrize("lam", [0.1, 0.3, 0.6])
def test_lambda_estimado_cae_cerca_del_verdadero(lam: float) -> None:
    """HB3: con visión total y una corrida larga, |λ̂ − λ| < 3 desviaciones posteriores."""
    m = correr(
        agents.Policy.BAYESIAN, rng=2, lambda_dinamismo=lam, radio=None, max_steps=800
    )
    aprendiz = m.collector.conocimiento.aprendiz
    assert aprendiz.n > 1000
    assert abs(aprendiz.media - lam) < 3 * aprendiz.desviacion
    fila = m.datacollector.get_model_vars_dataframe().iloc[-1]
    assert fila.lambda_estimado == pytest.approx(aprendiz.media)


@pytest.mark.parametrize("radio", [1, 3])
def test_lambda_estimado_no_se_sesga_con_vision_parcial(radio: int) -> None:
    """Con radio pequeño λ̂ no se sesga hacia abajo, promediando corridas.

    Los ensayos se seleccionan porque la celda previa sigue a la vista, no porque el
    recurso se vuelva a ver: exigir lo segundo descarta justo a los que se movieron
    fuera de la vista y subestima λ (a λ=0.5 y r=1, ~0.38).
    """
    lam = 0.5
    exitos = n = 0
    for s in range(12):
        a = correr(
            agents.Policy.BAYESIAN,
            rng=s,
            lambda_dinamismo=lam,
            radio=radio,
            max_steps=400,
        ).collector.conocimiento.aprendiz
        exitos, n = exitos + a.exitos, n + a.n
    p = exitos / n
    assert abs(p - lam) < 3 * math.sqrt(lam * (1 - lam) / n) + 0.02


# ------------------------------------------------------------ controles exactos


@pytest.mark.parametrize("lam", [0.1, 0.25, 0.5])
def test_hb2_con_vision_total_y_ahora_es_el_lazo_cerrado(lam: float) -> None:
    """HB2: ``r=∞`` y ``"ahora"`` ⇒ ``BAYESIAN`` ≡ ``CLOSED_LOOP`` tick a tick.

    Con visión total cada filtro es una masa puntual, el costo esperado es la distancia y
    la regla de reparación es el monitor. El λ aprendido no llega a intervenir.
    """
    for s in SEMILLAS:
        kw = {"rng": s, "lambda_dinamismo": lam, "radio": None}
        cerrado = correr(agents.Policy.CLOSED_LOOP, **kw)
        bayes = correr(agents.Policy.BAYESIAN, horizonte_validez="ahora", **kw)
        assert serie(cerrado).equals(serie(bayes))


def test_la_regla_de_reparacion_es_la_de_utilidad_esperada() -> None:
    """Se repara si y solo si c < (1 − q)(c + k), con q del filtro propagado k pasos."""
    m = mundo(3)
    cre = CreenciaBayesiana(MallaFiltro(m.libres), lam_fijo=0.4)
    origen = m.libres[10]
    cre.percibir({"r": origen}, [origen], derivas=0, t=0)
    for k in (0, 1, 3, 8):
        q = cre.prob_al_llegar("r", origen, k)
        for costo in (0, 2, 5, 20):
            valido = cre.plan_valido(
                "r",
                refutada=None,
                celda_pick=origen,
                k=k,
                horizonte="llegada",
                costo=costo,
            )
            assert valido == (not costo < (1 - q) * (costo + k))
    assert cre.prob_al_llegar("r", origen, 0) == 1.0


# -------------------------------------------------------------- calibración


@pytest.mark.slow
def test_hb5_el_filtro_con_lambda_conocido_esta_calibrado() -> None:
    """HB5: en cada bin poblado, la frecuencia observada ≈ la probabilidad media.

    La tolerancia es ancha a propósito (las celdas de un mismo tick están correlacionadas
    y el error binomial lo subestima), pero un filtro mal calibrado —λ equivocado,
    corrección sin renormalizar, soporte mal podado— se sale de ella con holgura.
    """
    from project.analysis import datos_calibracion

    for lam in (0.1, 0.4):
        d = datos_calibracion(semillas=range(16), lambda_dinamismo=lam, pasos=400)
        poblados = d[d.n >= 100]
        assert len(poblados) >= 3
        for _, fila in poblados.iterrows():
            assert abs(fila.frecuencia - fila.p_media) < 3 * fila.err + 0.05, (
                fila.to_dict()
            )
