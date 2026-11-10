"""La regla de costo: toda reparación se paga igual, los planes de rutina son gratis.

Todas las políticas que planifican usan el mismo replanificador al mismo precio, y solo
difieren en *cuándo* lo invocan: ``OPEN_LOOP`` al fallar el plan, ``CLOSED_LOOP`` y
``GOVERNED`` al detectar la divergencia. Estos tests anclan esa regla, que es la que hace
justa la comparación (``info/02-design.md`` §3.2).
"""

from typing import Any

from project.agents import Collector, Policy
from project.book import LineOp
from project.model import OASysWorld
import pytest

SEMILLAS = range(8)

PARAMETROS: dict[str, Any] = {
    "size": 13,
    "n_resources": 7,
    "max_steps": 250,
    "densidad_obstaculos": 0.12,
}


def correr(policy: str, **kw: Any) -> OASysWorld:
    """Una corrida corta con parámetros de test."""
    modelo = OASysWorld(policy=policy, **{**PARAMETROS, **kw})
    modelo.run_model()
    return modelo


def serie(modelo: OASysWorld) -> Any:
    """Todas las métricas tick a tick, sin la columna que nombra la política."""
    return modelo.datacollector.get_model_vars_dataframe().drop(columns="politica")


def provocar_fallo(costo: int, rng: int) -> tuple[OASysWorld, Collector]:
    """Un ``OPEN_LOOP`` a punto de replanificar por un fallo del plan.

    Con λ=0 nada se mueve solo. Tras el primer tick se traslada a mano el recurso
    objetivo a la celda libre más lejana de donde el agente cree que está: el lazo
    abierto no repara al verlo moverse, camina hasta la celda vieja y el ``PICK`` falla.
    Devuelve el modelo justo después del tick del fallo.
    """
    m = OASysWorld(
        policy=Policy.OPEN_LOOP,
        lambda_dinamismo=0.0,
        competencia=1.0,
        radio=None,
        costo_edicion=costo,
        rng=rng,
        **PARAMETROS,
    )
    m.step()
    c = m.collector
    assert c.target is not None and c.deliberation is None
    creido = c.belief[c.target]
    ocupadas = {r.cell for r in m.recursos()}
    lejos = max(
        (x for x in m.libres if x is not m.base and x not in ocupadas),
        key=lambda x: c._dist(x, creido),
    )
    recurso = next(r for r in m.recursos() if r.rid == c.target)
    recurso.cell = lejos

    for _ in range(200):
        m.step()
        if c.tareas_fallidas:
            break
    assert c.tareas_fallidas == 1
    assert c.pasos_deliberando == 0 and c.n_ediciones == 0
    return m, c


# --------------------------------------------------------------- el fallo se paga


@pytest.mark.parametrize("costo", [1, 3, 5])
@pytest.mark.parametrize("rng", [0, 1, 2])
def test_un_fallo_del_lazo_abierto_cuesta_c_ticks(costo: int, rng: int) -> None:
    """Tras un fallo, ``OPEN_LOOP`` delibera ``c`` ticks quieto, como el lazo cerrado.

    La reparación pasa por el oráculo, se marca como forzada y no mueve al agente
    mientras dura. Antes el plan se reconstruía gratis en el tick siguiente.
    """
    m, c = provocar_fallo(costo, rng)
    celda = c.cell

    m.step()  # arranca la deliberación
    assert c.deliberation is not None and c.deliberation.por_fallo
    for _ in range(costo):
        assert c.cell is celda
        m.step()
    assert c.deliberation is None
    assert c.cell is celda
    assert c.pasos_deliberando == costo
    assert c.n_ediciones == c.n_ediciones_por_fallo == 1


@pytest.mark.parametrize("rng", [0, 1, 2])
def test_con_c_cero_el_fallo_no_cobra_ticks(rng: int) -> None:
    """Con ``c = 0`` la reparación es instantánea: se repara y se actúa en el mismo tick."""
    m, c = provocar_fallo(0, rng)
    celda = c.cell
    m.step()
    assert c.deliberation is None
    assert c.pasos_deliberando == 0
    assert c.n_ediciones_por_fallo == 1
    assert c.cell is not celda


@pytest.mark.parametrize("lam", [0.1, 0.3, 0.5])
def test_el_lazo_abierto_paga_exactamente_sus_fallos(lam: float) -> None:
    """Todo tick deliberando del lazo abierto corresponde a una replanificación forzada.

    ``OPEN_LOOP`` nunca es interrumpido (ignora las divergencias), así que cada
    reparación suya consume exactamente ``c`` ticks; la corrida puede acabar a mitad de
    la última.
    """
    costo = 4
    for s in SEMILLAS:
        c = correr(
            Policy.OPEN_LOOP, rng=s, lambda_dinamismo=lam, costo_edicion=costo
        ).collector
        assert c.n_ediciones == c.n_ediciones_por_fallo
        assert c.n_ediciones_por_fallo <= c.tareas_fallidas
        assert costo * c.n_ediciones <= c.pasos_deliberando
        assert c.pasos_deliberando <= costo * (c.n_ediciones + 1)


# ------------------------------------------------------- los planes de rutina, gratis


@pytest.mark.parametrize("policy", [str(p) for p in Policy if p.planifica])
def test_los_planes_de_rutina_son_gratuitos(policy: str) -> None:
    """El plan inicial y el que sigue a cada entrega no pasan por el oráculo.

    Con λ=0 nada falla ni diverge, así que una corrida con varias entregas —cada una
    seguida de un plan nuevo— debe terminar sin un solo tick de deliberación.
    """
    for s in SEMILLAS:
        m = correr(policy, rng=s, lambda_dinamismo=0.0, costo_edicion=5, radio=None)
        c = m.collector
        assert c.entregas >= 2 * m.capacidad  # al menos un plan tras una entrega
        assert c.pasos_deliberando == 0
        assert c.n_ediciones == 0
        assert c.tareas_fallidas == 0


def test_el_primer_plan_es_gratuito() -> None:
    """Al primer tick el agente ya tiene plan y ya se movió, sin deliberar."""
    m = OASysWorld(
        policy=Policy.OPEN_LOOP, costo_edicion=10, radio=None, rng=0, **PARAMETROS
    )
    m.step()
    c = m.collector
    assert len(c.book) > 0
    assert c.book.pc == 1
    assert c.pasos_deliberando == 0
    assert c.deliberation is None


def test_sin_objetivo_conocido_el_fallo_no_se_paga() -> None:
    """Si tras el fallo no queda recurso conocido, no hay sobre qué deliberar.

    El agente vuelve con lo que lleve o deambula, sin consultar al oráculo ni pagar.
    """
    for rng in range(3):
        m, c = provocar_fallo(5, rng)
        for r in m.recursos():
            m.retirar_recurso(r)
        c.belief.clear()
        m.step()
        assert c.deliberation is None
        assert c.pasos_deliberando == 0
        assert c.n_ediciones == 0
        assert c.target is None
        if c.carrying:
            assert c.book.lines[-1].op is LineOp.DELIVER
        else:
            assert len(c.book) == 0  # sin plan: deambula


# ------------------------------------------------------------- controles exactos


@pytest.mark.parametrize("lam", [0.1, 0.25, 0.5])
@pytest.mark.parametrize("costo", [0, 5])
def test_gobernada_con_presupuesto_cero_es_el_lazo_abierto(lam: float, costo: int) -> None:
    """``GOVERNED`` con ``B = 0`` ≡ ``OPEN_LOOP``, semilla a semilla y tick a tick.

    El presupuesto acota solo las reparaciones proactivas; las forzadas por un fallo se
    pagan siempre. Sin presupuesto, lo único que queda es replanificar al fallar —que es
    exactamente el lazo abierto—. Cualquier diferencia delata que la gobernanza o la
    regla de costo se aplican de forma distinta a las dos políticas.
    """
    for s in SEMILLAS:
        kw = {"rng": s, "lambda_dinamismo": lam, "costo_edicion": costo}
        abierto = correr(Policy.OPEN_LOOP, **kw)
        gobernada = correr(Policy.GOVERNED, presupuesto=0, **kw)
        assert serie(abierto).equals(serie(gobernada))


@pytest.mark.parametrize("costo", [0, 5])
def test_sin_dinamismo_lazo_abierto_y_cerrado_coinciden(costo: int) -> None:
    """λ=0 ⇒ ``OPEN_LOOP`` ≡ ``CLOSED_LOOP`` con oráculo ruidoso y visión parcial.

    Sin dinamismo no hay fallos ni divergencias, y por tanto ninguna reparación que
    pagar: la regla de costo no puede introducir diferencias donde no hay nada que
    reparar.
    """
    for s in SEMILLAS:
        kw = {
            "rng": s,
            "lambda_dinamismo": 0.0,
            "costo_edicion": costo,
            "competencia": 0.9,
            "radio": 3,
        }
        abierto = correr(Policy.OPEN_LOOP, **kw)
        cerrado = correr(Policy.CLOSED_LOOP, **kw)
        assert serie(abierto).equals(serie(cerrado))
        assert cerrado.collector.pasos_deliberando == 0
