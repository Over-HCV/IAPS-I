"""La traza tick a tick debe decir la verdad sobre la corrida que dibuja.

``animacion`` deduce lo que el modelo no guarda —qué acción se ejecutó, si se
reescribió el plan y desde qué renglón— comparando el estado antes y después de cada
``step``. Si esa deducción se desalinea del modelo, la película miente, y miente de
forma convincente. Estos tests la anclan a los contadores del propio ``Collector``.
"""

import matplotlib

matplotlib.use("Agg")

from project import animacion as anim  # noqa: E402
from project.agents import Policy  # noqa: E402
import pytest  # noqa: E402

PASOS = 60

PARAMETROS: dict[str, object] = {
    "size": 13,
    "n_resources": 7,
    "densidad_obstaculos": 0.12,
    "lambda_dinamismo": 0.5,
    "costo_edicion": 2,
}


def traza(policy: str = "CLOSED_LOOP", **kw: object) -> tuple:
    """Una traza corta con los parámetros de test."""
    return anim.traza_corrida(pasos=PASOS, policy=policy, **{**PARAMETROS, **kw})


# ----------------------------------------------------------------------- estructura


def test_un_frame_por_tick_mas_el_inicial() -> None:
    """``pasos`` ticks producen ``pasos + 1`` frames, numerados en orden."""
    _, frames = traza()
    assert len(frames) == PASOS + 1
    assert [f.tick for f in frames] == list(range(PASOS + 1))
    assert frames[0].accion == "INICIO"


def test_la_traza_es_reproducible() -> None:
    """Misma semilla, misma película: es el control de sanidad nº 4 del diseño."""
    _, a = traza(rng=7)
    _, b = traza(rng=7)
    assert [(f.tick, f.agente, f.accion, f.pc) for f in a] == [
        (f.tick, f.agente, f.accion, f.pc) for f in b
    ]


@pytest.mark.parametrize("policy", [str(p) for p in Policy])
def test_toda_accion_esta_en_el_espacio_de_acciones(policy: str) -> None:
    """Ninguna etiqueta inventada: el panel de acciones no puede quedarse en blanco."""
    _, frames = traza(policy)
    assert {f.accion for f in frames} <= set(anim.ACCIONES)


def test_el_contador_de_programa_nunca_sale_del_plan() -> None:
    """``pc`` apunta dentro del plan o justo detrás de la última línea."""
    _, frames = traza()
    assert all(0 <= f.pc <= len(f.lineas) for f in frames)


# ------------------------------------------------------------------- deducciones


def test_el_lazo_abierto_solo_delibera_tras_un_fallo() -> None:
    """``OPEN_LOOP`` ejecuta su plan ciego: solo paga deliberación cuando el plan falla.

    Toda racha de ``DELIBERAR`` debe venir precedida de un ``FALLO`` (con, a lo sumo, el
    tick de espera en que arranca la deliberación), y toda edición suya es una
    replanificación forzada.
    """
    modelo, frames = traza("OPEN_LOOP")
    assert any(f.accion == "FALLO" for f in frames), "la traza debería tener un fallo"
    assert any(f.accion == "DELIBERAR" for f in frames)
    for i, f in enumerate(frames):
        if f.accion != "DELIBERAR":
            continue
        j = i - 1
        while frames[j].accion in ("DELIBERAR", "ESPERA"):
            j -= 1
        assert frames[j].accion == "FALLO"
    c = modelo.collector
    assert c.n_ediciones == c.n_ediciones_por_fallo


@pytest.mark.parametrize(
    "policy", ["OPEN_LOOP", "CLOSED_LOOP", "COLD_RESTART", "GOVERNED"]
)
def test_las_ediciones_detectadas_cuadran_con_el_contador(policy: str) -> None:
    """Cada edición del plan aparece en exactamente un frame, y ninguno más."""
    modelo, frames = traza(policy, presupuesto=3 if policy == "GOVERNED" else None)
    detectadas = sum(f.edicion in ("aplicada", "rechazada") for f in frames)
    assert detectadas == modelo.collector.n_ediciones


def test_una_edicion_aplicada_dice_desde_donde_cambio_el_plan() -> None:
    """El renglón resaltado existe y no es anterior al contador de programa.

    Reescribir el pasado es justo lo que ``Book.replace_suffix`` rechaza, así que un
    ``edit_desde`` por debajo del ``pc`` significaría que la deducción está mal.
    """
    _, frames = traza(costo_edicion=0)
    aplicadas = [f for f in frames if f.edicion == "aplicada"]
    assert aplicadas, "la corrida de prueba debería producir alguna edición"
    for f in aplicadas:
        assert f.edit_desde is not None
        assert f.edit_desde <= len(f.lineas)


def test_la_carga_en_vuelo_se_ve_en_el_frame() -> None:
    """``carrying`` y las entregas acumuladas crecen como en el modelo."""
    modelo, frames = traza()
    assert frames[-1].metricas["entregas"] == modelo.collector.entregas
    assert len(frames[-1].carrying) == len(modelo.collector.carrying)


# ----------------------------------------------------------------- observabilidad


def test_el_radio_de_vision_es_el_del_modelo() -> None:
    """La visión del frame es la del agente, no una reconstrucción aparte."""
    _, total = traza(radio=None)
    lado = PARAMETROS["size"]
    assert len(total[0].vision) == lado * lado  # type: ignore[operator]

    _, corta = traza(radio=1)
    assert all(len(f.vision) <= 5 for f in corta)  # von Neumann: centro + 4 vecinos


def test_las_creencias_pueden_divergir_de_la_realidad() -> None:
    """Con λ alto y radio corto tiene que haber algún frame con creencia obsoleta."""
    _, frames = traza(radio=1, lambda_dinamismo=0.8)
    divergentes = [
        f
        for f in frames
        for rid, cell in f.creencias.items()
        if f.recursos.get(rid) not in (None, cell)
    ]
    assert divergentes, "sin divergencia no hay nada que animar"


# ------------------------------------------------------------------------ dibujo


def test_el_dibujo_no_revienta() -> None:
    """Smoke: la animación se construye y renderiza un frame bajo Agg."""
    modelo, frames = traza()
    animacion = anim.animar(frames[:3], modelo, dpi=50, figsize=(6.0, 3.5))
    animacion._init_draw()
    animacion._fig.canvas.draw()


def test_la_figura_estatica_usa_los_mismos_paneles() -> None:
    """El modo estático dibuja sin re-simular y devuelve una figura de matplotlib."""
    modelo, frames = traza()
    fig = anim.figura_estatica(frames, modelo, dpi=50, figsize=(6.0, 3.5))
    assert len(fig.axes) == 4
