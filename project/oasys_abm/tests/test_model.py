"""Controles de sanidad del experimento (``docs/02-design.md`` §9).

No comprueban que el código no reviente, sino que el modelo se comporta como la teoría
exige. Si alguno falla, los resultados del barrido no significan nada.
"""

import statistics as st

from oasys_abm.agents import Policy
from oasys_abm.book import LineOp
from oasys_abm.model import OASysWorld
import pytest

SEMILLAS = range(8)


def correr(policy: str, **kw: object) -> OASysWorld:
    """Una corrida corta con parámetros de test."""
    base: dict[str, object] = {
        "size": 13,
        "n_resources": 7,
        "max_steps": 250,
        "densidad_obstaculos": 0.12,
    }
    base.update(kw)
    modelo = OASysWorld(policy=policy, **base)  # type: ignore[arg-type]
    modelo.run_model()
    return modelo


def entregas_medias(policy: str, **kw: object) -> float:
    """Entregas promedio sobre el conjunto de semillas."""
    return st.mean(correr(policy, rng=s, **kw).collector.entregas for s in SEMILLAS)


# --------------------------------------------------------------- controles 1 a 3


def test_sanidad_1_sin_dinamismo_replanificar_no_cambia_nada() -> None:
    """λ=0, p=1, r=∞: el lazo cerrado debe coincidir exactamente con el abierto.

    Si el mundo no se mueve, no hay nada que reparar. Cualquier diferencia delata que
    la replanificación se está disparando sin causa.
    """
    comun = {"lambda_dinamismo": 0.0, "competencia": 1.0, "radio": None}
    for s in SEMILLAS:
        abierto = correr(Policy.OPEN_LOOP, rng=s, **comun).collector
        cerrado = correr(Policy.CLOSED_LOOP, rng=s, **comun).collector
        assert cerrado.entregas == abierto.entregas
        assert cerrado.n_ediciones == 0


@pytest.mark.parametrize("lam", [0.1, 0.3, 0.5])
def test_sanidad_2_deliberacion_perfecta_y_gratuita_no_perjudica(lam: float) -> None:
    """c=0, p=1, r=∞: replanificar solo puede ayudar.

    Las tres condiciones hacen falta. Con radio finito el oráculo casi nunca ve dónde
    está de verdad el objetivo, repara sobre una creencia obsoleta y el control deja de
    valer — eso es un hallazgo del trabajo, no un control.
    """
    comun = {
        "lambda_dinamismo": lam,
        "costo_edicion": 0,
        "competencia": 1.0,
        "radio": None,
    }
    assert entregas_medias(Policy.CLOSED_LOOP, **comun) >= entregas_medias(
        Policy.OPEN_LOOP, **comun
    )


def test_sanidad_3_replanificador_malo_y_caro_destruye_el_plan() -> None:
    """p=0.5, c=10, λ bajo: auto-editarse debe salir peor que no hacerlo.

    Si este control no falla en la dirección esperada, el modelo de costo no muerde y
    la frontera de fase que busca el trabajo no puede existir.
    """
    comun = {"lambda_dinamismo": 0.05, "costo_edicion": 10, "competencia": 0.5}
    assert entregas_medias(Policy.CLOSED_LOOP, **comun) < entregas_medias(
        Policy.OPEN_LOOP, **comun
    )


def test_sanidad_4_reproducibilidad() -> None:
    """La misma semilla debe dar exactamente la misma corrida."""
    a = correr(Policy.CLOSED_LOOP, rng=7, lambda_dinamismo=0.3)
    b = correr(Policy.CLOSED_LOOP, rng=7, lambda_dinamismo=0.3)
    da = a.datacollector.get_model_vars_dataframe()
    db = b.datacollector.get_model_vars_dataframe()
    assert da.equals(db)


# --------------------------------------------------------------------- métricas


@pytest.mark.parametrize("lam", [0.0, 0.2, 0.5])
def test_la_ceguera_esta_acotada(lam: float) -> None:
    """Las detectadas nunca pueden superar a las reales."""
    for s in SEMILLAS:
        m = correr(Policy.CLOSED_LOOP, rng=s, lambda_dinamismo=lam)
        assert m.divergencias_detectadas <= m.divergencias_reales
        fila = m.datacollector.get_model_vars_dataframe().iloc[-1]
        assert 0.0 <= fila.ceguera <= 1.0


def test_observabilidad_total_no_deja_ciego_al_agente() -> None:
    """Con radio infinito el agente debería detectar casi toda divergencia."""
    m = correr(Policy.CLOSED_LOOP, rng=3, lambda_dinamismo=0.3, radio=None)
    fila = m.datacollector.get_model_vars_dataframe().iloc[-1]
    assert fila.ceguera < 0.5


def test_el_radio_de_vision_retrasa_la_deteccion() -> None:
    """Ver menos no hace perder divergencias, las hace descubrir más tarde.

    Es el resultado que obligó a cambiar la métrica: como el plan lleva al agente justo
    a la celda donde creía que estaba el recurso, casi toda divergencia acaba
    descubriéndose y la fracción de perdidas es casi nula con cualquier radio. Lo que sí
    cambia es *cuándo* se entera — y mientras tanto camina hacia el sitio equivocado.
    """

    def latencia(radio: int | None) -> float:
        lats: list[int] = []
        for s in SEMILLAS:
            lats += correr(
                Policy.CLOSED_LOOP, rng=s, lambda_dinamismo=0.3, radio=radio
            ).latencias
        return st.mean(lats)

    assert latencia(1) > latencia(None)


# ------------------------------------------------------------------ gobernanza


@pytest.mark.parametrize("presupuesto", [0, 3, 10])
def test_el_presupuesto_de_ediciones_se_respeta(presupuesto: int) -> None:
    """La cuota de ediciones es una cota dura, como la de energía en OASys."""
    for s in SEMILLAS:
        m = correr(
            Policy.GOVERNED,
            rng=s,
            lambda_dinamismo=0.4,
            presupuesto=presupuesto,
        )
        assert m.collector.n_ediciones <= presupuesto


def test_gobernanza_ilimitada_equivale_a_lazo_cerrado() -> None:
    """Sin presupuesto que la restrinja, GOVERNED debe ser idéntica a CLOSED_LOOP."""
    for s in SEMILLAS:
        g = correr(Policy.GOVERNED, rng=s, lambda_dinamismo=0.3).collector
        c = correr(Policy.CLOSED_LOOP, rng=s, lambda_dinamismo=0.3).collector
        assert g.entregas == c.entregas
        assert g.n_ediciones == c.n_ediciones


def test_la_gobernanza_rescata_en_entorno_muy_dinamico() -> None:
    """El hallazgo central sobre gobernanza: acotar las ediciones mejora el resultado.

    Con λ alto, el lazo cerrado sin restricciones entra en thrashing y se pasa la
    corrida deliberando. Un presupuesto pequeño lo obliga a actuar.
    """
    libre = entregas_medias(Policy.CLOSED_LOOP, lambda_dinamismo=0.5)
    acotado = entregas_medias(Policy.GOVERNED, lambda_dinamismo=0.5, presupuesto=5)
    assert acotado > libre


# --------------------------------------------------------------- cold vs hot


def test_el_reinicio_en_frio_pierde_trabajo_en_vuelo() -> None:
    """La diferencia entre ``cold`` y ``hot``: el frío suelta lo que llevaba encima."""
    perdidas = [
        correr(Policy.COLD_RESTART, rng=s, lambda_dinamismo=0.4).collector.carga_perdida
        for s in range(20)
    ]
    assert sum(perdidas) > 0
    calientes = [
        correr(Policy.CLOSED_LOOP, rng=s, lambda_dinamismo=0.4).collector.carga_perdida
        for s in range(20)
    ]
    assert sum(calientes) == 0


# -------------------------------------------------------------------- invariantes


def test_el_plan_siempre_termina_en_una_entrega_bloqueada() -> None:
    """Todo plan no vacío conserva el compromiso de entrega, y es inmutable."""
    m = OASysWorld(policy=Policy.CLOSED_LOOP, size=13, max_steps=1, rng=2)
    for _ in range(120):
        m.step()
        book = m.collector.book
        if len(book) == 0:
            continue
        assert book.lines[-1].op is LineOp.DELIVER
        assert book.lines[-1].locked
        assert len(book.locked_render()) == 1


def test_planificar_gana_cuando_los_recursos_escasean() -> None:
    """Con recursos escasos y terreno obstruido, planificar bate a reaccionar.

    Es el resultado de aprendizaje nº 1 de la asignatura (R&N §2.4) comprobado
    empíricamente — pero solo se cumple en el entorno adecuado, y conviene fijar cuál.
    """
    comun = {
        "lambda_dinamismo": 0.0,
        "size": 20,
        "n_resources": 2,
        "densidad_obstaculos": 0.25,
        "max_steps": 700,
    }
    reflejo = entregas_medias(Policy.REFLEX, **comun)
    plan = entregas_medias(Policy.OPEN_LOOP, **comun)
    assert plan > reflejo


def test_con_recursos_abundantes_el_reflejo_es_competitivo() -> None:
    """Y el resultado recíproco, que es el interesante.

    La ventaja de deliberar depende del entorno de tarea. Con recursos abundantes que
    reaparecen por todas partes, el agente reflejo —que reevalúa en cada tick y recoge
    lo que se le cruza— iguala o supera al planificador, que se compromete a una cadena
    de objetivos y no aprovecha lo que encuentra por el camino. Es el costo de la
    *commitment*: planificar compra previsión y vende oportunismo.
    """
    comun = {
        "lambda_dinamismo": 0.0,
        "size": 13,
        "n_resources": 7,
        "densidad_obstaculos": 0.12,
    }
    reflejo = entregas_medias(Policy.REFLEX, **comun)
    plan = entregas_medias(Policy.OPEN_LOOP, **comun)
    assert reflejo >= plan * 0.9
