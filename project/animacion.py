"""Una corrida, tick a tick: el mecanismo antes de los agregados.

``analysis.fig_trayectoria`` dibuja el **resultado** de una corrida —la traza sobre la
retícula— y con eso se pierde justo lo que el trabajo mide: cuándo nace una divergencia
entre el plan y el mundo, cuándo el agente la nota, qué sufijo del plan se reescribe y
cuántos ticks se van en deliberar en vez de actuar. Este módulo reconstruye esa película.

Igual que ``analysis``, separa las dos capas a propósito:

- **datos** — :func:`traza_corrida` corre el modelo y devuelve una lista de :class:`Frame`
  inmutables; no sabe dibujar;
- **dibujo** — :func:`animar` y :func:`figura_estatica` reciben esos frames y los pintan.

La captura **no toca** ``model.py`` ni ``agents.py``: todo se lee desde fuera comparando
el estado antes y después de cada ``model.step()``. La acción ejecutada en un tick no está
guardada en ninguna parte del modelo —el agente la ejecuta y sigue— así que se deduce del
diferencial de contadores y del avance del contador de programa.

Uso en el cuaderno::

    from project import animacion as anim

    anim.MODO = "animacion"          # o "estatico" para la figura de siempre
    anim.mostrar(policy="CLOSED_LOOP", lambda_dinamismo=0.25, pasos=80)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Literal

from project.agents import Collector, Policy
from project.book import LineOp
from project.model import OASysWorld

RESULTS = Path(__file__).parent / "results"
ANIMACIONES = RESULTS / "animaciones"

Modo = Literal["animacion", "estatico"]

MODO: Modo = "animacion"
"""Modo por defecto. Espejo de ``analysis.BACKEND``: se cambia en un solo sitio."""

ACCIONES = ("GOTO", "PICK", "DELIVER", "SCAN", "DELIBERAR", "FALLO", "ESPERA", "INICIO")
"""Etiquetas posibles de :attr:`Frame.accion`."""

ESPACIO_DE_ACCIONES = ("GOTO", "PICK", "DELIVER", "DELIBERAR")
"""Los actuadores del PEAS (``info/02-design.md`` §1), en el orden en que se dibujan."""

FLASH = 4
"""Frames que sigue resaltado el sufijo reescrito tras una edición."""

C_AGENTE = "#1f77b4"
C_BASE = "#2ca02c"
C_RECURSO = "#ff7f0e"
C_CREENCIA = "#8c8c8c"
C_PLAN = "#7b5cd6"
C_VISION = "#2f80ed"
C_OK = "#2ca02c"
C_MAL = "#d62728"
C_LOCK = "#b8860b"

METRICAS = (
    ("entregas", C_BASE),
    ("n_ediciones", C_PLAN),
    ("n_ediciones_desperdiciadas", C_MAL),
    ("pasos_deliberando", "#555555"),
)
"""Series de la franja inferior: qué se acumula mientras corre la película."""


# --------------------------------------------------------------------------- datos


@dataclass(frozen=True, slots=True)
class Frame:
    """El estado completo del mundo en un tick, ya desacoplado del modelo.

    Todo son datos planos —coordenadas, cadenas, números—, nunca celdas ni agentes vivos.
    Es la misma decisión que toma ``book.goto_lines`` al guardar coordenadas y no celdas:
    un frame debe poder sobrevivir al modelo que lo produjo.

    Attributes:
        tick: número de paso. El frame ``0`` es el estado inicial, antes de actuar.
        agente: posición del recolector.
        vision: celdas dentro del radio de observación.
        recursos: dónde están **realmente** los recursos.
        creencias: dónde **cree** el agente que están.
        objetivo: ``rid`` del recurso que persigue el plan.
        carrying: recursos en transporte (el trabajo en vuelo que un reinicio pierde).
        ruta: coordenadas de los ``GOTO`` que quedan por ejecutar.
        lineas: el plan entero como ``(op, arg, locked)``; ``locked`` marca las líneas
            fuera del alcance de edición del agente.
        pc: contador de programa.
        accion: qué se ejecutó en este tick (una de :data:`ACCIONES`).
        deliberando: ``(elapsed, duration)`` si hay una deliberación en curso.
        kind: etiqueta de la propuesta del oráculo (``OPTIMAL``, ``STALE_TARGET``…).
        edicion: ``"aplicada"``, ``"rechazada"`` o ``"desperdiciada"``.
        edit_desde: índice del primer renglón que cambió en la edición.
        interrumpida: True si una divergencia abortó la deliberación en curso.
        metricas: contadores acumulados hasta este tick.
    """

    tick: int
    agente: tuple[int, ...]
    vision: tuple[tuple[int, ...], ...]
    recursos: dict[str, tuple[int, ...]]
    creencias: dict[str, tuple[int, ...]]
    objetivo: str | None
    carrying: tuple[str, ...]
    ruta: tuple[tuple[int, ...], ...]
    lineas: tuple[tuple[str, str, bool], ...]
    pc: int
    accion: str
    deliberando: tuple[int, int] | None
    kind: str
    edicion: str | None
    edit_desde: int | None
    interrumpida: bool
    metricas: dict[str, float]


def _estado(modelo: OASysWorld) -> dict[str, Any]:
    """Fotografía de los contadores y del plan, para diferenciar contra el tick siguiente.

    Las líneas del plan se copian a una tupla: ``Book.lines`` es una lista que
    ``replace_suffix`` reescribe en sitio, así que guardar la referencia daría siempre
    el estado de después y no habría diferencia que medir.
    """
    c: Collector = modelo.collector
    d = c.deliberation
    return {
        "pos": c.cell.coordinate,
        "pc": c.book.pc,
        "lineas": tuple(c.book.lines),
        "carrying": tuple(c.carrying),
        "entregas": c.entregas,
        "n_ediciones": c.n_ediciones,
        "desperdiciadas": c.n_ediciones_desperdiciadas,
        "deliberando": c.pasos_deliberando,
        "fallidas": c.tareas_fallidas,
        "delib": None if d is None else (d.elapsed, d.duration, d.from_idx, d.label),
    }


def _primer_cambio(antes: tuple[Any, ...], ahora: tuple[Any, ...]) -> int | None:
    """Primer índice en que dos versiones del plan difieren. ``None`` si son iguales."""
    for i, (a, b) in enumerate(zip(antes, ahora, strict=False)):
        if a != b:
            return i
    if len(antes) != len(ahora):
        return min(len(antes), len(ahora))
    return None


def _accion(antes: dict[str, Any], ahora: dict[str, Any], policy: Policy) -> str:
    """Deducir qué hizo el agente en el tick que acaba de pasar.

    El orden de las comprobaciones es el del propio ``Collector.step``: primero lo que
    consume el tick entero (deliberar), luego el fallo que aborta el plan, luego la línea
    que avanzó el contador de programa. Lo último es la inferencia por efectos, que es lo
    único disponible para las políticas reactivas: no tienen plan donde mirar.
    """
    if ahora["deliberando"] > antes["deliberando"]:
        return "DELIBERAR"
    if ahora["fallidas"] > antes["fallidas"]:
        return "FALLO"
    avanzo = ahora["pc"] == antes["pc"] + 1 and antes["pc"] < len(antes["lineas"])
    if policy.planifica and avanzo:
        return str(antes["lineas"][antes["pc"]].op)
    if ahora["entregas"] > antes["entregas"]:
        return "DELIVER"
    if len(ahora["carrying"]) > len(antes["carrying"]):
        return "PICK"
    if ahora["pos"] != antes["pos"]:
        return "GOTO"
    return "ESPERA"


def _edicion(antes: dict[str, Any], ahora: dict[str, Any]) -> tuple[str | None, int | None]:
    """Deducir si el agente reescribió el plan en este tick y desde qué renglón.

    El renglón se saca del diff del plan y no de ``Deliberation.from_idx``: con ``c = 0``
    la deliberación nace, se aplica y se destruye dentro del mismo tick, así que en el
    estado capturado antes del tick no hay nada que leer.

    Una edición que sube ``n_ediciones`` y ``n_ediciones_desperdiciadas`` a la vez sin
    tocar el plan es una que el plan rechazó por violar sus invariantes, típicamente por
    tocar líneas fuera del alcance de edición (``EditRejected`` en
    ``agents._aplicar_en_caliente``).
    """
    cambio = _primer_cambio(antes["lineas"], ahora["lineas"])
    if ahora["n_ediciones"] > antes["n_ediciones"]:
        return ("aplicada" if cambio is not None else "rechazada", cambio)
    if ahora["desperdiciadas"] > antes["desperdiciadas"]:
        return ("desperdiciada", None)
    return (None, None)


def _capturar(
    modelo: OASysWorld, tick: int, accion: str, edicion: str | None, desde: int | None,
    interrumpida: bool,
) -> Frame:
    """Congelar el estado actual del modelo en un :class:`Frame`."""
    c: Collector = modelo.collector
    recursos = {r.rid: r.cell.coordinate for r in modelo.recursos()}
    creencias = {rid: cell.coordinate for rid, cell in c.belief.items()}
    ruta = tuple(
        ln.arg for ln in c.book.remaining if ln.op is LineOp.GOTO
    )
    lineas = tuple(
        (str(ln.op), "" if ln.arg is None else str(ln.arg), ln.locked)
        for ln in c.book.lines
    )
    d = c.deliberation
    return Frame(
        tick=tick,
        agente=c.cell.coordinate,
        vision=tuple(cell.coordinate for cell in c._vision()),
        recursos=recursos,
        creencias=creencias,
        objetivo=c.target,
        carrying=tuple(c.carrying),
        ruta=ruta,
        lineas=lineas,
        pc=c.book.pc,
        accion=accion,
        deliberando=None if d is None else (d.elapsed, d.duration),
        kind="" if d is None else d.label,
        edicion=edicion,
        edit_desde=desde,
        interrumpida=interrumpida,
        metricas={
            "entregas": c.entregas,
            "n_ediciones": c.n_ediciones,
            "n_ediciones_desperdiciadas": c.n_ediciones_desperdiciadas,
            "pasos_deliberando": c.pasos_deliberando,
            "divergencias_reales": modelo.divergencias_reales,
            "divergencias_detectadas": modelo.divergencias_detectadas,
            "carga_perdida": c.carga_perdida,
        },
    )


def traza_corrida(pasos: int = 80, **kwargs: Any) -> tuple[OASysWorld, list[Frame]]:
    """Correr el modelo guardando un :class:`Frame` por tick.

    Los defaults son los de ``analysis.fig_trayectoria``, para que la película y la
    figura estática cuenten la misma corrida.

    Args:
        pasos: ticks a simular. Devuelve ``pasos + 1`` frames: el inicial y uno por tick.
        **kwargs: cualquier parámetro de :class:`~project.model.OASysWorld`
            (``policy``, ``lambda_dinamismo``, ``costo_edicion``, ``radio``, ``rng``…).

    Returns:
        El modelo ya corrido y la lista de frames.
    """
    opciones: dict[str, Any] = {
        "size": 15,
        "n_resources": 8,
        "max_steps": pasos,
        "rng": 0,
        **kwargs,
    }
    modelo = OASysWorld(**opciones)
    frames = [_capturar(modelo, 0, "INICIO", None, None, False)]

    for tick in range(1, pasos + 1):
        antes = _estado(modelo)
        modelo.step()
        ahora = _estado(modelo)

        edicion, desde = _edicion(antes, ahora)
        # Una deliberación que estaba viva y desapareció sin aplicarse es la que abortó
        # una divergencia nueva: el thrashing de `_continuar_deliberacion`.
        interrumpida = (
            antes["delib"] is not None
            and ahora["n_ediciones"] == antes["n_ediciones"]
            and ahora["desperdiciadas"] > antes["desperdiciadas"]
        )
        frames.append(
            _capturar(
                modelo,
                tick,
                _accion(antes, ahora, modelo.policy),
                edicion,
                desde,
                interrumpida,
            )
        )
    return modelo, frames


# -------------------------------------------------------------------------- dibujo


def _flashes(frames: list[Frame]) -> list[tuple[int, str] | None]:
    """Para cada frame, el sufijo que se reescribió hace poco y sigue resaltado.

    Sin esta persistencia la edición se ve un solo frame —un parpadeo de 300 ms— y es
    justo el instante que hay que poder mirar.
    """
    out: list[tuple[int, str] | None] = []
    activo: tuple[int, str] | None = None
    edad = 0
    for f in frames:
        if f.edicion in ("aplicada", "rechazada"):
            activo = (f.edit_desde or 0, f.edicion)
            edad = 0
        elif activo is not None:
            edad += 1
            if edad > FLASH:
                activo = None
        out.append(activo)
    return out


def _xy(coords: Any) -> tuple[list[float], list[float]]:
    """Separar una colección de coordenadas en dos listas, tolerando la vacía."""
    puntos = list(coords)
    if not puntos:
        return [], []
    xs, ys = zip(*puntos, strict=True)
    return list(xs), list(ys)


def _panel_grid(ax: Any, frames: list[Frame], i: int, modelo: OASysWorld) -> None:
    """El mundo: obstáculos, visión, plan, creencia contra realidad."""
    import numpy as np

    f = frames[i]
    ax.clear()
    ax.imshow(modelo.grid.obstaculo.data.T, origin="lower", cmap="Greys", alpha=0.35)

    if modelo.radio is not None:
        mask = np.zeros(modelo.dimensions)
        for x, y in f.vision:
            mask[x, y] = 1.0
        ax.imshow(
            np.ma.masked_where(mask.T == 0, mask.T),
            origin="lower",
            cmap="Blues",
            vmin=0,
            vmax=1.6,
            alpha=0.13,
        )

    traza = [g.agente for g in frames[: i + 1]]
    if len(traza) > 1:
        xs, ys = zip(*traza, strict=True)
        ax.plot(xs, ys, lw=1.0, alpha=0.35, color=C_AGENTE, zorder=2)

    # Las series se dibujan siempre, aunque vayan vacías: así la leyenda tiene las mismas
    # entradas en todos los frames y no salta de tamaño mientras corre la película.
    px, py = _xy(((f.agente,) + f.ruta) if f.ruta else ())
    ax.plot(px, py, lw=1.6, ls=":", color=C_PLAN, alpha=0.9, zorder=3, label="plan vivo")

    ax.scatter(
        *modelo.base.coordinate, s=190, marker="s", color=C_BASE, zorder=4, label="base"
    )

    rx, ry = _xy(f.recursos.values())
    ax.scatter(rx, ry, s=70, color=C_RECURSO, zorder=5, label="recurso real")

    fantasmas = [c for rid, c in f.creencias.items() if f.recursos.get(rid) != c]
    cx, cy = _xy(fantasmas)
    ax.scatter(
        cx,
        cy,
        s=95,
        marker="D",
        facecolors="none",
        edgecolors=C_CREENCIA,
        lw=1.3,
        zorder=5,
        label="creencia obsoleta",
    )

    # La flecha creencia -> realidad sobre el objetivo es la divergencia hecha imagen:
    # mientras exista, el agente camina hacia la punta equivocada.
    if f.objetivo is not None:
        creido = f.creencias.get(f.objetivo)
        real = f.recursos.get(f.objetivo)
        if creido is not None:
            ax.scatter(
                *creido, s=230, facecolors="none", edgecolors=C_PLAN, lw=1.6, zorder=6
            )
        if creido is not None and real is not None and creido != real:
            ax.annotate(
                "",
                xy=real,
                xytext=creido,
                arrowprops={"arrowstyle": "->", "color": C_MAL, "lw": 1.6},
                zorder=7,
            )

    ax.scatter(*f.agente, s=150, color=C_AGENTE, zorder=8, label="agente")
    if f.carrying:
        ax.annotate(
            f"×{len(f.carrying)}",
            f.agente,
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
            color=C_AGENTE,
            weight="bold",
            zorder=9,
        )

    objetivo = f.objetivo or "—"
    ax.set_title(
        f"tick {f.tick:>3}  ·  {modelo.policy}  ·  objetivo {objetivo}"
        f"  ·  lleva {len(f.carrying)}/{modelo.capacidad}",
        fontsize=10,
    )
    lado_x, lado_y = modelo.dimensions
    ax.set_xlim(-0.6, lado_x - 0.4)
    ax.set_ylim(-0.6, lado_y - 0.4)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(
        frameon=False,
        fontsize=7.5,
        ncol=5,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.01),
        handletextpad=0.4,
        columnspacing=1.2,
    )


def _panel_book(ax: Any, frames: list[Frame], i: int, flash: tuple[int, str] | None) -> None:
    """El plan como programa: el contador, las líneas fuera del alcance de edición y el
    sufijo recién reescrito (verde si se aplicó, rojo si se rechazó)."""
    f = frames[i]
    ax.clear()
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    titulo = "Plan vivo"
    if f.edicion:
        titulo += f"   ← edición {f.edicion}"
    ax.set_title(titulo, fontsize=10, loc="left")

    if not f.lineas:
        ax.text(
            0.02,
            0.9,
            "sin plan\n(política reactiva o plan agotado)",
            fontsize=9,
            color=C_CREENCIA,
            va="top",
        )
        return

    ancho = 16
    inicio = max(0, min(f.pc - 6, len(f.lineas) - ancho))
    fin = min(len(f.lineas), inicio + ancho)
    paso = 1.0 / (ancho + 1)

    for fila, idx in enumerate(range(inicio, fin)):
        op, arg, locked = f.lineas[idx]
        y = 0.96 - fila * paso
        actual = idx == f.pc
        marca = "▶" if actual else " "
        texto = f"{marca} {idx:>3}  {op:<7} {arg}" + ("   [fuera de alcance]" if locked else "")
        color = C_AGENTE if actual else (C_LOCK if locked else "#333333")
        if idx < f.pc:
            color = "#aaaaaa"
        caja = None
        if flash is not None and idx >= flash[0]:
            caja = {
                "facecolor": C_OK if flash[1] == "aplicada" else C_MAL,
                "alpha": 0.16,
                "edgecolor": "none",
                "pad": 1.2,
            }
        ax.text(
            0.02,
            y,
            texto,
            fontsize=8.2,
            family="monospace",
            color=color,
            weight="bold" if actual else "normal",
            va="top",
            bbox=caja,
        )

    if fin < len(f.lineas):
        ax.text(
            0.02,
            0.96 - (fin - inicio) * paso,
            f"  … {len(f.lineas) - fin} líneas más",
            fontsize=7.5,
            family="monospace",
            color="#999999",
            va="top",
        )


def _panel_accion(ax: Any, frames: list[Frame], i: int, modelo: OASysWorld) -> None:
    """El espacio de acciones, con la de este tick encendida, y la deliberación en curso."""
    from matplotlib.patches import Rectangle

    f = frames[i]
    ax.clear()
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("acción del tick", fontsize=10, loc="left")

    ancho = 1.0 / len(ESPACIO_DE_ACCIONES)
    for k, nombre in enumerate(ESPACIO_DE_ACCIONES):
        encendida = f.accion == nombre
        ax.add_patch(
            Rectangle(
                (k * ancho + 0.012, 0.58),
                ancho - 0.024,
                0.3,
                facecolor=C_AGENTE if encendida else "#eeeeee",
                edgecolor="#cccccc",
                lw=0.8,
            )
        )
        ax.text(
            k * ancho + ancho / 2,
            0.73,
            nombre,
            ha="center",
            va="center",
            fontsize=8,
            color="white" if encendida else "#777777",
            weight="bold" if encendida else "normal",
        )

    if f.accion in ("FALLO", "ESPERA", "SCAN", "INICIO"):
        ax.text(0.012, 0.44, f.accion.lower(), fontsize=8.5, color=C_MAL, va="center")

    # Deliberar es una acción con duración: la barra es el tick gastándose.
    if f.deliberando is not None:
        elapsed, duration = f.deliberando
        frac = 1.0 if duration == 0 else min(1.0, elapsed / duration)
        ax.add_patch(
            Rectangle((0.012, 0.12), 0.976, 0.16, facecolor="#eeeeee", edgecolor="none")
        )
        ax.add_patch(
            Rectangle(
                (0.012, 0.12), 0.976 * frac, 0.16, facecolor=C_PLAN, edgecolor="none"
            )
        )
        ax.text(
            0.012,
            0.04,
            f"deliberando {elapsed}/{duration} ticks   ·   {f.kind}",
            fontsize=7.5,
            color=C_PLAN,
        )
    elif f.interrumpida:
        ax.text(
            0.012,
            0.14,
            "deliberación interrumpida — thrashing",
            fontsize=8,
            color=C_MAL,
            weight="bold",
        )
    else:
        ax.text(
            0.012,
            0.14,
            f"c = {modelo.costo_edicion} ticks por edición   ·   "
            f"r = {'∞' if modelo.radio is None else modelo.radio}   ·   "
            f"λ = {modelo.lambda_dinamismo}",
            fontsize=7.5,
            color="#777777",
        )


def _panel_metricas(ax: Any, frames: list[Frame], i: int) -> None:
    """Lo que se acumula mientras corre la película: entregas, ediciones, deliberación."""
    ax.clear()
    ticks = [f.tick for f in frames]
    # La escala se fija con la corrida entera: si creciera con los datos, el cursor
    # parecería moverse hacia abajo y las series no se podrían comparar entre frames.
    techo = max(f.metricas[n] for f in frames for n, _ in METRICAS)
    for nombre, color in METRICAS:
        serie = [f.metricas[nombre] for f in frames]
        ax.step(
            ticks[: i + 1],
            serie[: i + 1],
            where="post",
            lw=1.4,
            color=color,
            label=f"{nombre.replace('_', ' ')} = {serie[i]:.0f}",
        )
    ax.set_ylim(0, max(1.0, techo) * 1.1)
    ax.axvline(frames[i].tick, color="#bbbbbb", lw=0.8, ls="--")
    ax.set_xlim(0, max(ticks))
    ax.set_xlabel("tick", fontsize=9)
    ax.legend(frameon=False, fontsize=7.5, ncol=4, loc="upper left")
    ax.tick_params(labelsize=8)


def _lienzo(figsize: tuple[float, float], dpi: int) -> tuple[Any, dict[str, Any]]:
    """Armar la figura y los cuatro ejes. Lo comparten la animación y la estática."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="white", context="notebook")
    fig = plt.figure(figsize=figsize, dpi=dpi)
    gs = fig.add_gridspec(
        2,
        2,
        width_ratios=[1.0, 1.0],
        height_ratios=[3.2, 0.85],
        hspace=0.32,
        wspace=0.06,
        left=0.035,
        right=0.985,
        top=0.93,
        bottom=0.08,
    )
    derecha = gs[0, 1].subgridspec(2, 1, height_ratios=[2.6, 1.0], hspace=0.3)
    ejes = {
        "grid": fig.add_subplot(gs[0, 0]),
        "book": fig.add_subplot(derecha[0]),
        "accion": fig.add_subplot(derecha[1]),
        "metricas": fig.add_subplot(gs[1, :]),
    }
    return fig, ejes


def animar(
    frames: list[Frame],
    modelo: OASysWorld,
    *,
    intervalo: int = 320,
    cada: int = 1,
    figsize: tuple[float, float] = (11.5, 6.6),
    dpi: int = 82,
) -> Any:
    """Construir la animación de los cuatro paneles.

    No usa *blitting*: cada frame limpia y redibuja sus ejes. Es más lento de generar
    —unos segundos para 80 frames— pero es lo único que funciona cuando el contenido de
    un panel es texto de longitud variable, como el plan.

    Args:
        frames: salida de :func:`traza_corrida`.
        modelo: el modelo que los produjo; aporta lo que no cambia (obstáculos, base).
        intervalo: milisegundos por frame en la reproducción.
        cada: quedarse con uno de cada *n* ticks, para aligerar el cuaderno.
        figsize: tamaño en pulgadas.
        dpi: resolución. Con ``to_jshtml`` cada frame viaja como PNG en base64, así que
            es el parámetro que decide cuánto pesa el ``.ipynb``.

    Returns:
        Un ``matplotlib.animation.FuncAnimation``.
    """
    from matplotlib.animation import FuncAnimation

    vista = frames[::cada]
    flashes = _flashes(vista)
    fig, ejes = _lienzo(figsize, dpi)

    def dibujar(i: int) -> list[Any]:
        _panel_grid(ejes["grid"], vista, i, modelo)
        _panel_book(ejes["book"], vista, i, flashes[i])
        _panel_accion(ejes["accion"], vista, i, modelo)
        _panel_metricas(ejes["metricas"], vista, i)
        return list(ejes.values())

    return FuncAnimation(
        fig, dibujar, frames=len(vista), interval=intervalo, blit=False, repeat=True
    )


def figura_estatica(
    frames: list[Frame],
    modelo: OASysWorld,
    *,
    figsize: tuple[float, float] = (11.5, 6.6),
    dpi: int = 110,
) -> Any:
    """Los mismos cuatro paneles en el último frame, con la traza completa encima."""
    fig, ejes = _lienzo(figsize, dpi)
    i = len(frames) - 1
    _panel_grid(ejes["grid"], frames, i, modelo)
    _panel_book(ejes["book"], frames, i, None)
    _panel_accion(ejes["accion"], frames, i, modelo)
    _panel_metricas(ejes["metricas"], frames, i)
    fig.suptitle(
        f"{modelo.policy} — {frames[i].tick} ticks, "
        f"{frames[i].metricas['entregas']:.0f} entregas, "
        f"{frames[i].metricas['n_ediciones']:.0f} ediciones",
        fontsize=11,
    )
    return fig


# ------------------------------------------------------------------------ salidas


LIMITE_MB = 40
"""Tope de ``animation.embed_limit``. El default de matplotlib (20 MB) se queda corto."""

AVISO_MB = 15.0
"""A partir de aquí conviene bajar ``pasos``, ``dpi`` o subir ``cada``."""


def a_jshtml(anim: Any) -> str:
    """Serializar la animación al reproductor JS, avisando si engorda el cuaderno."""
    import matplotlib.pyplot as plt

    plt.rcParams["animation.embed_limit"] = LIMITE_MB
    html = str(anim.to_jshtml())
    mb = len(html) / 1e6
    if mb > AVISO_MB:
        print(
            f"aviso: la animación ocupa {mb:.1f} MB dentro del .ipynb. "
            f"Bajar `pasos`/`dpi` o subir `cada` para aligerarla.",
            file=sys.stderr,
        )
    return html


def mostrar(pasos: int = 80, modo: Modo | None = None, cada: int = 1, **kwargs: Any) -> Any:
    """Lo que llama el cuaderno: una corrida, y según :data:`MODO` película o figura.

    La simulación se corre **una sola vez** para los dos modos, así que la figura
    estática y la animación muestran exactamente la misma corrida.

    Args:
        pasos: ticks a simular.
        modo: ``"animacion"`` o ``"estatico"``; por defecto :data:`MODO`.
        cada: decimación de frames en la animación.
        **kwargs: parámetros de :class:`~project.model.OASysWorld`.
    """
    import matplotlib.pyplot as plt

    modelo, frames = traza_corrida(pasos=pasos, **kwargs)
    if (modo or MODO) == "estatico":
        return figura_estatica(frames, modelo)

    from IPython.display import HTML

    anim = animar(frames, modelo, cada=cada)
    html = a_jshtml(anim)
    # Sin esto el cuaderno muestra además el último frame como figura suelta.
    plt.close(anim._fig)
    return HTML(html)


def guardar(anim: Any, ruta: str | Path) -> Path:
    """Escribir la animación a ``.mp4`` (ffmpeg) o ``.gif`` (pillow).

    Un mp4 pesa unas veinte veces menos que el mismo ``to_jshtml`` embebido, que es lo
    que conviene para la entrega si el ``.ipynb`` no debe engordar.
    """
    destino = Path(ruta)
    if not destino.is_absolute():
        destino = ANIMACIONES / destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    anim.save(str(destino), writer="pillow" if destino.suffix == ".gif" else "ffmpeg")
    return destino
