"""La KB de ``KNOWLEDGE_BASED`` (``docs/roadmap-c4b.md``, KB-2).

Tres bloques. Las propiedades de la región posible, que son lo que hace sólida la
inferencia; la equivalencia entre el nivel de implementación (conjuntos) y el de
conocimiento (DPLL sobre las mismas observaciones, ``project.logica``); y los controles
exactos de la política, que son los que dicen que los ganchos en el recolector no cambian
nada que no deban cambiar.
"""

from collections import deque
import random
from typing import Any

from mesa import Model
from mesa.discrete_space import OrthogonalVonNeumannGrid
from project import agents
from project.conocimiento import BaseConocimiento, RegionPosible, Vecindario, expandir
from project.logica import And, Implies, KnowledgeBase, Not, Or, exactly
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
"""Columnas que dependen de la política por definición, fuera de toda comparación."""


def correr(policy: str, **kw: Any) -> OASysWorld:
    """Una corrida corta con parámetros de test."""
    modelo = OASysWorld(policy=policy, **{**PARAMETROS, **kw})
    modelo.run_model()
    return modelo


def serie(modelo: OASysWorld) -> Any:
    """Todas las métricas tick a tick, sin las que nombran o solo tiene una política."""
    return modelo.datacollector.get_model_vars_dataframe().drop(columns=POR_POLITICA)


def reticula(
    lado: int, obstaculos: list[tuple[int, int]] = ()
) -> OrthogonalVonNeumannGrid:
    """Una retícula suelta, sin modelo de recolección, con su capa de obstáculos."""
    grid = OrthogonalVonNeumannGrid(
        (lado, lado), torus=False, capacity=None, random=Model(rng=0).random
    )
    grid.create_property_layer("obstaculo", default_value=False, dtype=bool)
    for xy in obstaculos:
        grid.obstaculo.data[xy] = True
    return grid


def bola_geodesica(origen: Any, k: int) -> set[Any]:
    """BFS de profundidad ``k`` sobre celdas transitables, escrita aparte a propósito."""
    dist = {origen: 0}
    cola = deque([origen])
    while cola:
        c = cola.popleft()
        if dist[c] == k:
            continue
        for v in c.connections.values():
            if not v.obstaculo and v not in dist:
                dist[v] = dist[c] + 1
                cola.append(v)
    return set(dist)


# ------------------------------------------------------------ la región posible


def test_sin_observaciones_la_region_es_la_bola_geodesica() -> None:
    """Tras ``k`` ticks sin ver nada, la región es la bola geodésica de radio ``k``.

    Junto a una pared es estrictamente menor que la bola de Manhattan: la celda al otro
    lado está a distancia 2 en Manhattan pero a mucho más rodeando el muro.
    """
    muro = [(3, y) for y in range(6)]
    grid = reticula(7, muro)
    origen = grid[(2, 1)]
    region = RegionPosible(origen, Vecindario())
    for k in range(1, 9):
        region.avanzar(1, set())
        assert region.celdas == bola_geodesica(origen, k)
        assert region.celdas == expandir([origen], k, Vecindario())
    manhattan_3 = {
        c
        for c in grid.all_cells.cells
        if not c.obstaculo and abs(c.coordinate[0] - 2) + abs(c.coordinate[1] - 1) <= 3
    }
    geodesica_3 = bola_geodesica(origen, 3)
    assert geodesica_3 < manhattan_3
    assert grid[(4, 1)] in manhattan_3 and grid[(4, 1)] not in geodesica_3


def test_una_celda_vista_vacia_se_excluye_y_luego_vuelve() -> None:
    """Lo visto vacío en t' se excluye en t', pero vuelve a ser posible si es alcanzable.

    La poda ingenua —la bola menos *todas* las celdas vistas vacías desde el
    avistamiento— no es sólida: el recurso pudo entrar después en una de ellas.
    """
    grid = reticula(5)
    c0, c1 = grid[(2, 2)], grid[(3, 2)]
    region = RegionPosible(c0, Vecindario())
    region.avanzar(1, {c1})
    assert c1 not in region and c0 in region
    region.avanzar(1, set())
    assert c1 in region
    ingenua = expandir([c0], 2, Vecindario()) - {c1}
    assert c1 not in ingenua


@pytest.mark.parametrize("semilla", range(20))
def test_la_bola_del_segundo_avistamiento_esta_en_la_del_primero(semilla: int) -> None:
    """Con dos avistamientos de una caminata real, la intersección de bolas es la última.

    Por desigualdad triangular: el axioma obliga a d(c1, c2) ≤ t2 − t1, así que la bola
    de radio t − t2 alrededor de c2 cabe en la de radio t − t1 alrededor de c1.
    """
    m = OASysWorld(size=11, densidad_obstaculos=0.2, rng=semilla)
    rnd = random.Random(semilla)
    vecinas = Vecindario()
    camino = [rnd.choice(m.libres)]
    for _ in range(30):
        opciones = vecinas(camino[-1])
        camino.append(
            rnd.choice(opciones) if opciones and rnd.random() < 0.6 else camino[-1]
        )
    t1 = rnd.randrange(0, 10)
    t2 = rnd.randrange(t1, 20)
    for t in range(t2, 31):
        segunda = expandir([camino[t2]], t - t2, vecinas)
        primera = expandir([camino[t1]], t - t1, vecinas)
        assert segunda <= primera
        assert camino[t] in segunda


@pytest.mark.parametrize("semilla", range(10))
def test_el_peor_caso_coincide_con_la_fuerza_bruta(semilla: int) -> None:
    """El atajo de los extremos de x+y y x−y da el mismo máximo que recorrer la región."""
    m = OASysWorld(size=13, rng=semilla)
    if len(m.libres) < 20:
        pytest.skip("la base quedó aislada por los obstáculos")
    rnd = random.Random(semilla)
    region = RegionPosible(rnd.choice(m.libres), Vecindario())
    for _ in range(rnd.randrange(1, 12)):
        region.avanzar(1, set(rnd.sample(m.libres, 6)))
    if not region.celdas:
        pytest.skip("la poda vació la región")
    c = m.collector
    for origen in rnd.sample(m.libres, 10):
        assert region.peor_caso(origen.coordinate) == region.peor_caso_con(
            origen, c._dist
        )


# ----------------------------------------------------------------- solidez


def vigilar_solidez(modelo: OASysWorld, tamanos: list[int]) -> None:
    """Comprobar, justo después de cada observación, que la celda real está en la región.

    Es la versión honesta del «0 muertes en celda declarada segura» del Wumpus. Llena
    ``tamanos`` con el tamaño de las regiones comprobadas, para que la prueba pueda
    asegurarse de no ser vacía.
    """
    c = modelo.collector
    original = c.observar

    def observar() -> None:
        original()
        kb = c.conocimiento
        assert isinstance(kb, BaseConocimiento)
        reales = {r.rid: r.cell for r in modelo.recursos()}
        for rid, region in kb.regiones.items():
            assert rid in reales, f"{rid} se rastrea pero ya no está en el mundo"
            assert reales[rid] in region, (
                f"tick {modelo.steps}: {rid} fuera de su región"
            )
            tamanos.append(len(region))

    c.observar = observar  # type: ignore[method-assign]


@pytest.mark.parametrize("orden_aleatorio", [False, True])
@pytest.mark.parametrize("radio", [1, 3])
@pytest.mark.parametrize("lam", [0.25, 0.5])
def test_solidez_la_celda_real_siempre_esta_en_la_region(
    lam: float, radio: int, orden_aleatorio: bool
) -> None:
    """En toda corrida con λ>0 y visión parcial, ningún recurso escapa de su región.

    Con el orden sorteado puede haber 0, 1 o 2 derivas entre dos observaciones: la región
    se expande por el número real (``OASysWorld.derivas``), o dejaría de ser sólida.
    """
    tamanos: list[int] = []
    for s in range(6):
        m = OASysWorld(
            policy=agents.Policy.KNOWLEDGE_BASED,
            lambda_dinamismo=lam,
            radio=radio,
            orden_aleatorio=orden_aleatorio,
            rng=s,
            **PARAMETROS,
        )
        vigilar_solidez(m, tamanos)
        m.run_model()
    assert max(tamanos) > 10  # hubo regiones anchas que comprobar


# ------------------------------------------------- nivel de conocimiento: DPLL


def test_dpll_responde_falso_fuera_de_la_region_y_desconocido_dentro() -> None:
    """La región por conjuntos es exactamente lo que DPLL no puede descartar.

    Retícula de 4×4 con un obstáculo y 3 ticks. Se codifica ``En_x_y_t`` por celda y
    tick, ``exactly(1, ...)`` por tick, el axioma de deriva y las observaciones (el
    avistamiento en t=0 y las celdas vistas vacías en t=1 y t=2). Para cada celda y tick,
    ``ask_status`` debe dar ``falso`` fuera de :math:`R(r,t)` y ``desconocido`` dentro.
    """
    grid = reticula(4, [(1, 2)])
    libres = [c for c in grid.all_cells.cells if not c.obstaculo]
    vecinas = Vecindario()

    def sym(c: Any, t: int) -> str:
        return f"En_{c.coordinate[0]}_{c.coordinate[1]}_t{t}"

    avistado = grid[(1, 1)]
    vistas = {
        1: {grid[(0, 1)], grid[(1, 0)]},
        2: {grid[(2, 1)], grid[(0, 0)], grid[(3, 3)]},
    }

    kb = KnowledgeBase()
    for t in range(3):
        kb.tell(exactly(1, [sym(c, t) for c in libres]))
    for t in range(2):
        for c in libres:
            kb.tell(
                Implies(
                    sym(c, t), Or(sym(c, t + 1), *[sym(v, t + 1) for v in vecinas(c)])
                )
            )
    kb.tell(sym(avistado, 0))
    for t, celdas in vistas.items():
        kb.tell(And(*[Not(sym(c, t)) for c in celdas]))

    region = RegionPosible(avistado, vecinas)
    for t in (1, 2):
        region.avanzar(1, vistas[t])
        assert len(region) > 1
        for c in libres:
            esperado = "desconocido" if c in region else "falso"
            assert kb.ask_status(sym(c, t)) == esperado, (c.coordinate, t)


# --------------------------------------------------------- la pregunta 3 «ahora»


def test_el_horizonte_ahora_dispara_en_los_mismos_ticks_que_el_monitor() -> None:
    """Con ``"ahora"`` la pregunta 3 dice *inválido* en todo evento de divergencia.

    Es decir, reproduce exactamente las dos reglas de detección de ``CLOSED_LOOP``
    (objetivo visto en otro sitio, celda creída vista vacía): el monitor de hoy es la
    lectura a nivel de implementación de esta consulta.
    """
    respuestas: list[bool] = []
    for s in SEMILLAS:
        m = OASysWorld(
            policy=agents.Policy.KNOWLEDGE_BASED,
            horizonte_validez="ahora",
            lambda_dinamismo=0.3,
            radio=3,
            rng=s,
            **PARAMETROS,
        )
        c = m.collector
        original = c._plan_sigue_valido

        def registrar(original: Any = original) -> bool:
            r = original()
            respuestas.append(r)
            return r

        c._plan_sigue_valido = registrar  # type: ignore[method-assign]
        m.run_model()
    assert respuestas and not any(respuestas)


def test_el_horizonte_llegada_mantiene_planes() -> None:
    """Con ``"llegada"`` hay eventos en que el plan se mantiene: es la palanca de KB-2.

    Y cada consulta se cuenta: una por evento si se mantiene, dos (la 3 y la 2) si se
    repara.
    """
    respuestas: list[bool] = []
    consultas = 0
    for s in SEMILLAS:
        m = OASysWorld(
            policy=agents.Policy.KNOWLEDGE_BASED,
            lambda_dinamismo=0.3,
            radio=3,
            rng=s,
            **PARAMETROS,
        )
        c = m.collector
        original = c._plan_sigue_valido

        def registrar(original: Any = original) -> bool:
            r = original()
            respuestas.append(r)
            return r

        c._plan_sigue_valido = registrar  # type: ignore[method-assign]
        m.run_model()
        consultas += c.n_consultas
    assert any(respuestas) and not all(respuestas)
    assert consultas == sum(1 if r else 2 for r in respuestas)


# ------------------------------------------------------------ controles exactos


@pytest.mark.parametrize("lam", [0.1, 0.25, 0.5])
def test_h2_con_vision_total_y_ahora_es_el_lazo_cerrado(lam: float) -> None:
    """H2: ``r=∞`` y ``"ahora"`` ⇒ ``KNOWLEDGE_BASED`` ≡ ``CLOSED_LOOP`` tick a tick.

    Con visión total la región de cada recurso es un punto en cada decisión, el peor caso
    es la distancia a la creencia y la pregunta 3 es el monitor. Cualquier diferencia
    delata que un gancho cambia algo más de lo que debe (aquí, por ejemplo, el orden de la
    tabla de creencias, que rompe los empates).
    """
    for s in SEMILLAS:
        kw = {"rng": s, "lambda_dinamismo": lam, "radio": None}
        cerrado = correr(agents.Policy.CLOSED_LOOP, **kw)
        kb = correr(agents.Policy.KNOWLEDGE_BASED, horizonte_validez="ahora", **kw)
        assert serie(cerrado).equals(serie(kb))


@pytest.mark.parametrize("horizonte", ["ahora", "llegada"])
@pytest.mark.parametrize("radio", [1, 3, None])
def test_h2_sin_dinamismo_es_el_lazo_cerrado_en_todo_radio(
    radio: int | None, horizonte: str
) -> None:
    """H2 con λ=0: el agente sabe que nada se mueve, y ≡ ``CLOSED_LOOP`` en todo radio."""
    for s in SEMILLAS:
        kw = {"rng": s, "lambda_dinamismo": 0.0, "radio": radio}
        cerrado = correr(agents.Policy.CLOSED_LOOP, **kw)
        kb = correr(agents.Policy.KNOWLEDGE_BASED, horizonte_validez=horizonte, **kw)
        assert serie(cerrado).equals(serie(kb))


def test_las_demas_politicas_no_consultan_ni_estiman() -> None:
    """Los reporters nuevos son 0 y ``nan`` fuera de las políticas que infieren."""
    for p in agents.Policy:
        if p.infiere:
            continue
        fila = correr(
            p, rng=1, lambda_dinamismo=0.3
        ).datacollector.get_model_vars_dataframe()
        assert (fila.n_consultas == 0).all()
        assert fila.lambda_estimado.isna().all()


def test_el_horizonte_invalido_se_rechaza() -> None:
    """Un horizonte mal escrito no debe pasar en silencio a un valor por defecto."""
    with pytest.raises(ValueError):
        OASysWorld(horizonte_validez="luego")


# --------------------------------------------------------------- costo de preguntar


@pytest.mark.parametrize("ticks", [1, 3])
def test_cada_consulta_cuesta_ticks_quieto(ticks: int) -> None:
    """Con ``c=0`` todo tick deliberando es de consulta: ``ticks_por_ask`` por cada una.

    La corrida puede acabar a mitad de la pausa de la última (a lo sumo dos consultas,
    la 3 y la 2, en un mismo evento).
    """
    for s in SEMILLAS:
        m = correr(
            agents.Policy.KNOWLEDGE_BASED,
            rng=s,
            lambda_dinamismo=0.3,
            costo_edicion=0,
            ticks_por_ask=ticks,
        )
        c = m.collector
        assert c.n_consultas > 0
        assert (
            ticks * (c.n_consultas - 2) <= c.pasos_deliberando <= ticks * c.n_consultas
        )


def test_preguntar_quieto_no_mueve_al_agente() -> None:
    """Durante la pausa de una consulta el agente no se mueve ni avanza el plan."""
    m = OASysWorld(
        policy=agents.Policy.KNOWLEDGE_BASED,
        lambda_dinamismo=0.4,
        costo_edicion=0,
        ticks_por_ask=4,
        rng=3,
        **PARAMETROS,
    )
    c = m.collector
    pausados = 0
    for _ in range(PARAMETROS["max_steps"]):
        en_pausa = c._pausa > 0
        celda, pc = c.cell, c.book.pc
        m.step()
        if en_pausa:
            pausados += 1
            assert c.cell is celda and c.book.pc == pc
    assert pausados > 0


# ------------------------------------------------------------ regresión con CSV


def test_el_barrido_conocimiento_reproduce_los_barridos_guardados() -> None:
    """Las políticas viejas del barrido nuevo dan exactamente las corridas ya guardadas.

    ``OPEN_LOOP`` y ``CLOSED_LOOP`` contra ``observabilidad`` (mismas semillas, λ y
    radio) y ``MODEL_BASED`` con ``r=3`` contra ``principal`` con ``c=5``. Si falla, los
    parámetros nuevos están cambiando a políticas que no deberían leerlos.
    """
    an = pytest.importorskip("project.analysis")
    try:
        nuevo = an.cargar("conocimiento")
        obs = an.cargar("observabilidad")
        principal = an.cargar("principal")
    except FileNotFoundError as e:
        pytest.skip(str(e))
    claves = ["politica", "rng", "lambda_dinamismo", "radio"]
    metricas = [
        "entregas",
        "utilidad_neta",
        "pasos_deliberando",
        "n_ediciones",
        "n_ediciones_por_fallo",
        "tareas_fallidas",
    ]

    def tabla(df: Any) -> Any:
        return df.set_index(claves)[metricas].sort_index()

    viejas = ["OPEN_LOOP", "CLOSED_LOOP"]
    a = tabla(nuevo[nuevo.politica.isin(viejas)])
    b = tabla(obs[obs.politica.isin(viejas)])
    assert a.index.equals(b.index) and (a.values == b.values).all()

    mb = nuevo[(nuevo.politica == "MODEL_BASED") & (nuevo.radio == "3")]
    ref = principal[
        (principal.politica == "MODEL_BASED")
        & (principal.costo_edicion == 5)
        & principal.lambda_dinamismo.isin(mb.lambda_dinamismo.unique())
    ]
    a, b = tabla(mb), tabla(ref)
    assert len(a) == 120 and a.index.equals(b.index) and (a.values == b.values).all()
