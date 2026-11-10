"""Lectura, agregación y figuras de los barridos.

Este módulo es la capa que faltaba entre ``results/*.csv`` y una conclusión legible. Se
divide en dos partes deliberadamente separadas:

- **datos** — :func:`cargar`, :func:`agregar`, :func:`cargar_dinamica`,
  :func:`agregar_tiempo`, :func:`delta_hot_vs_cold`, :func:`robustez_orden`,
  :func:`diferencia_pareada` y :func:`controles` devuelven ``DataFrame``\\ s y no saben
  nada de gráficas;
- **dibujo** — :func:`lineas` recibe uno de esos ``DataFrame``\\ s en formato largo y lo
  pinta con el backend activo.

Casi todas las figuras de barrido (frontera, caliente contra frío, competencia,
observabilidad, gobernanza, dinámica y conocimiento) son el mismo objeto gráfico (líneas por
serie, banda de error, facetas en rejilla), así que el backend se cambia en un solo sitio
(:func:`fig_calibracion` y :func:`fig_escasez` arman su rejilla a mano y son solo de
matplotlib)::

    analysis.BACKEND = "plotly"          # global
    analysis.fig_frontera(backend="mpl") # o por llamada

Uso, desde la raíz del repositorio::

    uv run python -m project.analysis --figuras
    uv run python -m project.analysis --controles
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Literal

from project.agents import Policy
import pandas as pd

RESULTS = Path(__file__).parent / "results"
FIGURAS = RESULTS / "figuras"

Backend = Literal["mpl", "plotly"]

BACKEND: Backend = "mpl"
"""Backend por defecto. ``"mpl"`` para figuras de entrega, ``"plotly"`` para explorar."""

ORDEN_POLITICAS = [str(p) for p in Policy]
"""Orden de las políticas en leyendas y paletas: el de la taxonomía de R&N §2.4."""


# --------------------------------------------------------------------------- datos


def cargar(nombre: str) -> pd.DataFrame:
    """Leer ``results/<nombre>.csv``.

    Args:
        nombre: nombre del barrido, tal como aparece en ``experiments.SWEEPS``.

    Raises:
        FileNotFoundError: con el comando exacto que genera el archivo que falta.
    """
    ruta = RESULTS / f"{nombre}.csv"
    if not ruta.exists():
        raise FileNotFoundError(
            f"no existe {ruta}. Generarlo con:\n"
            f"    uv run python -m project.experiments "
            f"--sweep {nombre}"
        )
    df = pd.read_csv(ruta)
    # `radio=None` (observabilidad total) viaja como celda vacía en el CSV. Dejarlo como
    # NaN rompe el groupby —las filas se caerían en silencio— así que se etiqueta.
    if "radio" in df.columns:
        df["radio"] = df["radio"].map(lambda v: "∞" if pd.isna(v) else str(int(v)))
    return df


def agregar(
    df: pd.DataFrame,
    *,
    x: str,
    metrica: str = "utilidad_neta",
    serie: str | None = "politica",
    faceta: str | None = None,
) -> pd.DataFrame:
    """Media y error estándar sobre las réplicas, en formato largo.

    Devuelve siempre las mismas columnas —``x``, ``y``, ``err``, ``serie``, ``faceta``—
    para que la capa de dibujo no tenga que saber de qué barrido viene el dato.

    Args:
        df: crudo, una fila por corrida.
        x: columna del eje horizontal (el parámetro barrido).
        metrica: columna a resumir.
        serie: columna que separa las líneas; ``None`` para una sola.
        faceta: columna que separa los paneles; ``None`` para un solo panel.
    """
    claves = [c for c in (x, serie, faceta) if c is not None]
    g = df.groupby(claves, dropna=False)[metrica]
    out = g.agg(["mean", "std", "count"]).reset_index()
    # Error estándar de la media: es lo que hay que dibujar cuando se comparan medias de
    # 30 réplicas. La desviación cruda mostraría la dispersión del mundo, no la
    # incertidumbre sobre la media, y haría ver como indistinguibles curvas que no lo son.
    out["err"] = out["std"] / out["count"] ** 0.5
    out = out.rename(columns={x: "x", "mean": "y"})
    out["serie"] = out[serie].astype(str) if serie else metrica
    out["faceta"] = out[faceta].astype(str) if faceta else ""
    if serie == "politica":
        out["serie"] = pd.Categorical(
            out["serie"], categories=ORDEN_POLITICAS, ordered=True
        )
    return out[["x", "y", "err", "serie", "faceta"]].sort_values(
        ["faceta", "serie", "x"]
    )


def cargar_dinamica() -> pd.DataFrame:
    """Leer ``results/dinamica.parquet`` (series temporales, paquete 3 de C4).

    Raises:
        FileNotFoundError: con el comando exacto que genera el archivo, igual que
            :func:`cargar`.
    """
    ruta = RESULTS / "dinamica.parquet"
    if not ruta.exists():
        raise FileNotFoundError(
            f"no existe {ruta}. Generarlo con:\n"
            f"    uv run python -m project.experiments --dinamica --procesos 0"
        )
    return pd.read_parquet(ruta)


def agregar_tiempo(
    df: pd.DataFrame,
    metrica: str = "entregas",
    *,
    serie: str = "politica",
    faceta: str | None = "lambda_dinamismo",
) -> pd.DataFrame:
    """Media y error estándar de una métrica **por tick**, sobre las semillas.

    Es :func:`agregar` con ``x="tick"``: devuelve el mismo formato largo, de modo que la
    misma primitiva :func:`lineas` dibuja la curva temporal.
    """
    return agregar(df, x="tick", metrica=metrica, serie=serie, faceta=faceta)


def robustez_orden() -> pd.DataFrame:
    """Paquete 1 de C4: ¿cambia algún signo al sortear el orden de activación?

    Compara, celda a celda (λ, c), las tres diferencias que sostienen las conclusiones
    —reparar en caliente contra en frío (``CLOSED_LOOP − COLD_RESTART``), lazo abierto
    contra cerrado (``OPEN_LOOP − CLOSED_LOOP``) y no planificar contra la mejor política
    con plan (``MODEL_BASED − max``)— entre ``principal`` (orden fijo) y ``orden``
    (orden sorteado por tick).
    """
    fijo = cargar("principal")
    sorteo = cargar("orden")
    claves = ["lambda_dinamismo", "costo_edicion"]
    fijo = fijo[
        fijo.lambda_dinamismo.isin(sorteo.lambda_dinamismo.unique())
        & fijo.costo_edicion.isin(sorteo.costo_edicion.unique())
    ]
    filas = []
    for nombre, df in (("fijo", fijo), ("sorteado", sorteo)):
        m = df.groupby([*claves, "politica"])["utilidad_neta"].mean().unstack("politica")
        con_plan = m[[str(Policy.OPEN_LOOP), str(Policy.COLD_RESTART), str(Policy.CLOSED_LOOP)]]
        d = pd.DataFrame(
            {
                "caliente_menos_frio": m[str(Policy.CLOSED_LOOP)] - m[str(Policy.COLD_RESTART)],
                "abierto_menos_cerrado": m[str(Policy.OPEN_LOOP)] - m[str(Policy.CLOSED_LOOP)],
                "modelo_menos_mejor_plan": m[str(Policy.MODEL_BASED)] - con_plan.max(axis=1),
            }
        )
        d["orden"] = nombre
        filas.append(d.reset_index())
    largo = pd.concat(filas)
    ancho = largo.pivot_table(index=claves, columns="orden").round(1)
    for col in ("caliente_menos_frio", "abierto_menos_cerrado", "modelo_menos_mejor_plan"):
        ancho[(col, "mismo_signo")] = (
            (ancho[(col, "fijo")] > 0) == (ancho[(col, "sorteado")] > 0)
        )
    return ancho.sort_index(axis=1)


def delta_hot_vs_cold(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """El valor de reparar en caliente frente a reiniciar en frío, en unidades del modelo.

    ``CLOSED_LOOP`` repara el plan en sitio; ``COLD_RESTART`` tira el trabajo en curso y
    aplica la edición en la ejecución siguiente (``info/02-design.md`` §3). La diferencia
    entre ambos es el argumento cuantitativo para diseñar motores de ejecución agéntica
    que reparen en caliente.
    """
    df = cargar("principal") if df is None else df
    medias = (
        df[df.politica.isin([str(Policy.CLOSED_LOOP), str(Policy.COLD_RESTART)])]
        .groupby(["lambda_dinamismo", "costo_edicion", "politica"])[
            ["utilidad_neta", "carga_perdida", "entregas"]
        ]
        .mean()
        .unstack("politica")
    )
    out = pd.DataFrame(index=medias.index)
    for m in ("utilidad_neta", "carga_perdida", "entregas"):
        out[f"delta_{m}"] = (
            medias[(m, str(Policy.CLOSED_LOOP))] - medias[(m, str(Policy.COLD_RESTART))]
        )
    out["delta_utilidad_pct"] = 100 * out["delta_utilidad_neta"] / medias[
        ("utilidad_neta", str(Policy.COLD_RESTART))
    ].replace(0, float("nan"))
    return out.round(2).reset_index()


def _media(df: pd.DataFrame, politica: Policy, metrica: str = "utilidad_neta") -> float:
    """Media de una métrica para una política. ``nan`` si la política no está."""
    sub = df[df.politica == str(politica)]
    return float("nan") if sub.empty else float(sub[metrica].mean())


def controles(principal: pd.DataFrame | None = None) -> pd.DataFrame:
    """Los controles de sanidad de ``info/02-design.md`` §9 evaluables sobre los CSV.

    Son el 1, 2 y 3, más el 6 (``GOVERNED`` con ``B=0`` ≡ ``OPEN_LOOP``), que es
    consecuencia directa de la regla de costo: el presupuesto solo acota las reparaciones
    proactivas, y las forzadas por un fallo se pagan igual en toda política.

    Ninguna figura vale nada si estos no pasan, así que se miran primero. Un control cuyo
    barrido no se haya corrido sale como ``NO EVALUABLE`` con el comando que lo genera —
    nunca como ``PASA`` por ausencia de evidencia.
    """
    principal = cargar("principal") if principal is None else principal
    filas: list[dict[str, Any]] = []

    # 1. λ=0 ⇒ replanificar no puede ayudar: sin dinamismo el plan inicial nunca caduca.
    est = principal[principal.lambda_dinamismo == 0]
    abierto = _media(est, Policy.OPEN_LOOP)
    cerrado = _media(est, Policy.CLOSED_LOOP)
    filas.append(
        {
            "control": "1. λ=0 ⇒ CLOSED_LOOP = OPEN_LOOP",
            "esperado": "igualdad exacta",
            "observado": f"{cerrado:.1f} vs {abierto:.1f}",
            "estado": "PASA" if abs(cerrado - abierto) < 1e-9 else "FALLA",
        }
    )

    # 2 y 3 necesitan combinaciones de (c, p, r) que ningún barrido principal fija.
    for n, titulo, esperado, comparar in (
        (
            "control2",
            "2. c=0, p=1, r=∞ ⇒ CLOSED_LOOP domina en todo λ",
            "CLOSED_LOOP ≥ OPEN_LOOP",
            "domina",
        ),
        (
            "control3",
            "3. p=0.5, c=10, λ bajo ⇒ CLOSED_LOOP peor",
            "CLOSED_LOOP < OPEN_LOOP",
            "peor",
        ),
    ):
        try:
            df = cargar(n)
        except FileNotFoundError:
            filas.append(
                {
                    "control": titulo,
                    "esperado": esperado,
                    "observado": f"falta results/{n}.csv",
                    "estado": "NO EVALUABLE",
                }
            )
            continue
        if comparar == "domina":
            por_lambda = df.groupby(["lambda_dinamismo", "politica"])[
                "utilidad_neta"
            ].mean().unstack("politica")
            diff = por_lambda[str(Policy.CLOSED_LOOP)] - por_lambda[str(Policy.OPEN_LOOP)]
            ok = bool((diff >= 0).all())
            obs = f"Δ mínimo sobre λ = {diff.min():+.1f}"
        else:
            a, c = _media(df, Policy.OPEN_LOOP), _media(df, Policy.CLOSED_LOOP)
            ok = c < a
            obs = f"{c:.1f} vs {a:.1f}"
        filas.append(
            {
                "control": titulo,
                "esperado": esperado,
                "observado": obs,
                "estado": "PASA" if ok else "FALLA",
            }
        )

    # 6. B=0 ⇒ GOVERNED ≡ OPEN_LOOP, corrida a corrida (misma semilla, mismos parámetros).
    titulo = "6. B=0 ⇒ GOVERNED = OPEN_LOOP"
    try:
        df = cargar("control4")
    except FileNotFoundError:
        filas.append(
            {
                "control": titulo,
                "esperado": "igualdad exacta por corrida",
                "observado": "falta results/control4.csv",
                "estado": "NO EVALUABLE",
            }
        )
    else:
        claves = ["rng", "lambda_dinamismo", "costo_edicion"]
        metricas = [
            "entregas",
            "utilidad_neta",
            "pasos_deliberando",
            "n_ediciones",
            "tareas_fallidas",
        ]
        a = df[df.politica == str(Policy.OPEN_LOOP)].set_index(claves)[metricas]
        g = df[df.politica == str(Policy.GOVERNED)].set_index(claves)[metricas]
        a, g = a.sort_index(), g.sort_index()
        iguales = a.index.equals(g.index) and bool((a.values == g.values).all())
        filas.append(
            {
                "control": titulo,
                "esperado": "igualdad exacta por corrida",
                "observado": (
                    f"{len(a)} pares, {int((a.values != g.values).any(axis=1).sum())} "
                    f"distintos; {g.utilidad_neta.mean():.1f} vs {a.utilidad_neta.mean():.1f}"
                    if a.index.equals(g.index)
                    else "las corridas no se emparejan"
                ),
                "estado": "PASA" if iguales else "FALLA",
            }
        )

    return pd.DataFrame(filas)


# -------------------------------------------------------------------------- dibujo


def _facetas(tidy: pd.DataFrame) -> list[str]:
    """Paneles en orden numérico cuando la faceta es un número."""
    vals = list(dict.fromkeys(tidy["faceta"]))
    try:
        return sorted(vals, key=float)
    except ValueError:
        return sorted(vals)


def _lineas_mpl(
    tidy: pd.DataFrame,
    *,
    titulo: str,
    xlab: str,
    ylab: str,
    faceta_lab: str,
    marcadores: bool = True,
) -> Any:
    """Backend matplotlib + seaborn. Figuras estáticas para el documento."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="notebook")
    facetas = _facetas(tidy)
    n = len(facetas)
    fig, axes = plt.subplots(
        1, n, figsize=(4.2 * n + 1.2, 3.8), sharey=True, squeeze=False
    )
    series = [s for s in dict.fromkeys(tidy["serie"]) if pd.notna(s)]
    colores = dict(zip(series, sns.color_palette("colorblind", len(series)), strict=True))

    for ax, f in zip(axes[0], facetas, strict=True):
        panel = tidy[tidy["faceta"] == f]
        for s in series:
            d = panel[panel["serie"] == s]
            if d.empty:
                continue
            ax.plot(
                d["x"],
                d["y"],
                marker="o" if marcadores else None,
                ms=4,
                label=str(s),
                color=colores[s],
            )
            ax.fill_between(
                d["x"], d["y"] - d["err"], d["y"] + d["err"], alpha=0.15, color=colores[s]
            )
        ax.set_xlabel(xlab)
        if f:
            ax.set_title(f"{faceta_lab} = {f}" if faceta_lab else str(f), fontsize=10)
    axes[0][0].set_ylabel(ylab)
    axes[0][-1].legend(frameon=False, fontsize=8, loc="best")
    fig.suptitle(titulo, fontsize=12, y=1.02)
    fig.tight_layout()
    return fig


def _lineas_plotly(
    tidy: pd.DataFrame,
    *,
    titulo: str,
    xlab: str,
    ylab: str,
    faceta_lab: str,
    marcadores: bool = True,
) -> Any:
    """Backend plotly. Mismo dato, interactivo, para explorar en el notebook."""
    import plotly.express as px

    d = tidy.copy()
    d["serie"] = d["serie"].astype(str)
    una = d["faceta"].eq("").all()
    fig = px.line(
        d.sort_values("x"),
        x="x",
        y="y",
        error_y="err",
        color="serie",
        facet_col=None if una else "faceta",
        markers=marcadores,
        category_orders={"serie": [str(s) for s in ORDEN_POLITICAS]},
        labels={"x": xlab, "y": ylab, "serie": ""},
        title=titulo,
    )
    if not una:
        fig.for_each_annotation(
            lambda a: a.update(text=f"{faceta_lab} = {a.text.split('=')[-1]}")
        )
    return fig


def lineas(
    tidy: pd.DataFrame,
    *,
    titulo: str,
    xlab: str,
    ylab: str,
    faceta_lab: str = "",
    backend: Backend | None = None,
    marcadores: bool = True,
) -> Any:
    """Pintar un ``DataFrame`` de :func:`agregar` con el backend activo."""
    fn = _lineas_mpl if (backend or BACKEND) == "mpl" else _lineas_plotly
    return fn(
        tidy,
        titulo=titulo,
        xlab=xlab,
        ylab=ylab,
        faceta_lab=faceta_lab,
        marcadores=marcadores,
    )


def guardar(fig: Any, ruta: Path) -> Path:
    """Escribir la figura, sea del backend que sea."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(fig, "savefig"):  # matplotlib
        fig.savefig(ruta, dpi=150, bbox_inches="tight")
    else:  # plotly
        fig.write_image(str(ruta), scale=2)
    return ruta


# ------------------------------------------------------------------------- figuras


def fig_frontera(backend: Backend | None = None) -> Any:
    """La figura central: frontera de fase en dinamismo × costo de edición."""
    df = cargar("principal")
    return lineas(
        agregar(df, x="lambda_dinamismo", faceta="costo_edicion"),
        titulo="Frontera de fase: utilidad neta por dinamismo y costo de edición",
        xlab="λ (dinamismo)",
        ylab="utilidad neta",
        faceta_lab="c",
        backend=backend,
    )


def fig_hot_vs_cold(backend: Backend | None = None) -> Any:
    """Cuánto vale reparar en caliente en vez de reiniciar en frío (CLOSED − COLD)."""
    d = delta_hot_vs_cold()
    tidy = pd.concat(
        [
            pd.DataFrame(
                {
                    "x": d["lambda_dinamismo"],
                    "y": d[f"delta_{m}"],
                    "err": 0.0,
                    "serie": etiqueta,
                    "faceta": d["costo_edicion"].astype(str),
                }
            )
            for m, etiqueta in (
                ("utilidad_neta", "Δ utilidad neta"),
                ("carga_perdida", "Δ carga perdida"),
            )
        ]
    )
    return lineas(
        tidy,
        titulo="En caliente vs. en frío (CLOSED_LOOP − COLD_RESTART)",
        xlab="λ (dinamismo)",
        ylab="diferencia",
        faceta_lab="c",
        backend=backend,
    )


def fig_competencia(backend: Backend | None = None) -> Any:
    """¿Desde qué competencia del replanificador conviene auto-editarse?"""
    df = cargar("competencia")
    return lineas(
        agregar(df, x="competencia", faceta="lambda_dinamismo"),
        titulo="Sensibilidad a la competencia del oráculo (c=5, r=3)",
        xlab="p (competencia)",
        ylab="utilidad neta",
        faceta_lab="λ",
        backend=backend,
    )


def fig_observabilidad(
    metrica: str = "latencia_deteccion", backend: Backend | None = None
) -> Any:
    """El efecto de la observabilidad parcial: ver menos, enterarse más tarde."""
    df = cargar("observabilidad")
    return lineas(
        agregar(df, x="lambda_dinamismo", metrica=metrica, serie="radio", faceta="politica"),
        titulo=f"Observabilidad parcial: {metrica.replace('_', ' ')} por radio de visión",
        xlab="λ (dinamismo)",
        ylab=metrica.replace("_", " "),
        faceta_lab="política",
        backend=backend,
    )


def fig_gobernanza(
    metrica: str = "utilidad_neta", backend: Backend | None = None
) -> Any:
    """¿Acotar las ediciones rescata al agente del thrashing?"""
    df = cargar("gobernanza")
    return lineas(
        agregar(df, x="presupuesto", metrica=metrica, faceta="lambda_dinamismo"),
        titulo=f"Gobernanza: {metrica.replace('_', ' ')} por presupuesto de ediciones",
        xlab="B (presupuesto)",
        ylab=metrica.replace("_", " "),
        faceta_lab="λ",
        backend=backend,
    )


def fig_dinamica(
    metrica: str = "entregas", backend: Backend | None = None
) -> Any:
    """Paquete 3 de C4: *cuándo* se separan las políticas, no solo cuánto."""
    return lineas(
        agregar_tiempo(cargar_dinamica(), metrica),
        titulo=f"Dinámica: {metrica.replace('_', ' ')} acumulada por tick (c=5, r=3)",
        xlab="tick",
        ylab=metrica.replace("_", " "),
        faceta_lab="λ",
        backend=backend,
        marcadores=False,
    )


def fig_trayectoria(pasos: int = 120, backend: Backend | None = None, **kwargs: Any) -> Any:
    """Una corrida concreta, para ver el mecanismo antes de mirar agregados.

    Dibuja la retícula con sus obstáculos y la traza del recolector. Solo tiene backend
    matplotlib: es un mapa, no una serie, y no comparte la primitiva de :func:`lineas`.
    """
    import matplotlib.pyplot as plt
    from project.agents import Resource
    from project.model import OASysWorld
    import seaborn as sns

    if (backend or BACKEND) == "plotly":
        raise NotImplementedError("fig_trayectoria solo dibuja con matplotlib")

    opciones = {"size": 15, "n_resources": 8, "max_steps": pasos, "rng": 0, **kwargs}
    model = OASysWorld(**opciones)
    traza = [model.collector.cell.coordinate]
    for _ in range(pasos):
        model.step()
        traza.append(model.collector.cell.coordinate)

    sns.set_theme(style="white", context="notebook")
    fig, ax = plt.subplots(figsize=(6, 6))
    obst = model.grid.obstaculo.data
    ax.imshow(obst.T, origin="lower", cmap="Greys", alpha=0.35)
    xs, ys = zip(*traza, strict=True)
    ax.plot(xs, ys, lw=1.2, alpha=0.8, color="tab:blue", label="trayectoria")
    ax.scatter(*model.base.coordinate, s=160, marker="s", color="tab:green", label="base")
    recursos = model.agents_by_type.get(Resource)
    if recursos:
        rx, ry = zip(*[r.cell.coordinate for r in recursos], strict=True)
        ax.scatter(rx, ry, s=55, color="tab:orange", label="recursos (final)")
    ax.set_title(
        f"{model.policy} — {pasos} ticks, {model.collector.entregas} entregas, "
        f"{model.collector.n_ediciones} ediciones"
    )
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_xticks([])
    ax.set_yticks([])
    return fig


# ------------------------------------------------- KB-2 y C5-B: conocimiento


def diferencia_pareada(
    df: pd.DataFrame,
    a: str,
    b: str,
    *,
    por: tuple[str, ...] = ("lambda_dinamismo", "radio"),
    metrica: str = "utilidad_neta",
) -> pd.DataFrame:
    """Diferencia ``a − b`` emparejada por semilla, con su error estándar.

    Es la comparación que piden las hipótesis de KB-2 y C5-B («por pares de semilla»):
    las dos políticas corren sobre el mismo mundo, así que la varianza entre mundos se
    cancela y queda solo la de la diferencia.

    Args:
        df: crudo, una fila por corrida, con ``politica`` y ``rng``.
        a: política (o etiqueta en ``politica``) del minuendo.
        b: política del sustraendo.
        por: columnas que separan las celdas del barrido.
        metrica: columna a comparar.

    Returns:
        Una fila por celda con ``media``, ``err``, ``n`` y ``t`` (= media / err).
    """
    claves = [*por, "rng"]
    ancho = df[df.politica.isin([a, b])].pivot_table(
        index=claves, columns="politica", values=metrica
    )
    d = (ancho[a] - ancho[b]).dropna().rename("d").reset_index()
    out = d.groupby(list(por))["d"].agg(["mean", "std", "count"])
    out["err"] = out["std"] / out["count"] ** 0.5
    out["t"] = out["mean"] / out["err"].replace(0, float("nan"))
    return out.rename(columns={"mean": "media", "count": "n"})[
        ["media", "err", "n", "t"]
    ].reset_index()


def fig_conocimiento(
    metrica: str = "utilidad_neta", backend: Backend | None = None
) -> Any:
    """KB-2 y C5-B: ¿compensa saber qué se sabe, frente a no planificar y a reparar siempre?"""
    df = cargar("conocimiento")
    return lineas(
        agregar(df, x="lambda_dinamismo", metrica=metrica, faceta="radio"),
        titulo=(
            f"Conocimiento: {metrica.replace('_', ' ')} por dinamismo y radio de visión "
            "(c=5, horizonte «llegada»)"
        ),
        xlab="λ (dinamismo)",
        ylab=metrica.replace("_", " "),
        faceta_lab="r",
        backend=backend,
    )


def datos_calibracion(
    *,
    semillas: Any = range(6),
    lambda_dinamismo: float = 0.25,
    radio: int = 3,
    pasos: int = 300,
    bins: int = 10,
    policy: str = "CLOSED_LOOP",
) -> pd.DataFrame:
    """HB5 de C5-B: diagrama de fiabilidad del filtro cuando conoce el λ verdadero.

    Se corre el modelo y, justo después de cada observación del recolector, un filtro de
    prueba con λ conocido (``CreenciaBayesiana(lam_fijo=λ)``, que la política nunca usa)
    incorpora esa misma observación. Por cada recurso rastreado y fuera de la vista, y
    cada celda fuera de la vista con probabilidad positiva, se anota la probabilidad
    asignada y si el recurso estaba de verdad ahí. Si el filtro está calibrado, en cada
    bin la frecuencia observada coincide con la probabilidad media del bin.

    Returns:
        Una fila por bin no vacío con ``p_media``, ``frecuencia``, ``n`` y ``err`` (error
        estándar binomial, que ignora la correlación entre celdas del mismo tick).
    """
    import numpy as np
    from project.filtro import CreenciaBayesiana, MallaFiltro
    from project.model import OASysWorld

    preds: list[Any] = []
    aciertos: list[Any] = []
    for s in semillas:
        m = OASysWorld(
            policy=policy,
            size=15,
            n_resources=8,
            densidad_obstaculos=0.15,
            lambda_dinamismo=lambda_dinamismo,
            radio=radio,
            max_steps=pasos,
            rng=s,
        )
        if len(m.libres) < 2:
            continue
        c = m.collector
        cre = CreenciaBayesiana(MallaFiltro(m.libres), lam_fijo=lambda_dinamismo)
        original = c.observar

        def observar(
            original: Any = original, m: Any = m, c: Any = c, cre: Any = cre
        ) -> None:
            original()
            reales = {r.rid: r.cell for r in m.recursos()}
            for rid in [r for r in cre.filtros if r not in reales]:
                cre.recoger(rid, m.steps)
            visibles = c._vision()
            vis = set(visibles)
            vistos = {rid: cell for rid, cell in reales.items() if cell in vis}
            cre.percibir(vistos, visibles, derivas=m.derivas, t=m.steps)
            fuera = np.ones(len(cre.malla), dtype=bool)
            fuera[cre.malla.indices(vis)] = False
            for rid, filtro in cre.filtros.items():
                if rid in vistos:
                    continue
                mascara = fuera & (filtro.p > 0)
                real = np.zeros(len(cre.malla), dtype=bool)
                real[cre.malla.indice[reales[rid]]] = True
                preds.append(filtro.p[mascara])
                aciertos.append(real[mascara])

        c.observar = observar
        m.run_model()

    p = np.concatenate(preds) if preds else np.empty(0)
    y = np.concatenate(aciertos) if aciertos else np.empty(0, dtype=bool)
    b = np.minimum((p * bins).astype(int), bins - 1)
    df = pd.DataFrame({"bin": b, "p": p, "y": y.astype(float)})
    out = df.groupby("bin").agg(
        p_media=("p", "mean"), frecuencia=("y", "mean"), n=("y", "size")
    )
    out["err"] = (out["frecuencia"] * (1 - out["frecuencia"]) / out["n"]) ** 0.5
    return out.reset_index()


def fig_calibracion(backend: Backend | None = None, **kwargs: Any) -> Any:
    """HB5: ¿dice la verdad el filtro cuando dice «probabilidad x»?

    Solo dibuja con matplotlib (es un diagrama de fiabilidad, no una serie de
    :func:`lineas`); con ``backend="plotly"`` devuelve igualmente la figura de matplotlib
    para que ``--figuras`` no se interrumpa. Corre una simulación pequeña cada vez
    (``kwargs`` van a :func:`datos_calibracion`).
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    d = datos_calibracion(**kwargs)
    sns.set_theme(style="whitegrid", context="notebook")
    fig, (ax, ax_n) = plt.subplots(
        1, 2, figsize=(9.5, 4.2), gridspec_kw={"width_ratios": [1.4, 1]}
    )
    ax.plot([0, 1], [0, 1], ls="--", color="grey", lw=1, label="calibración perfecta")
    ax.errorbar(
        d["p_media"],
        d["frecuencia"],
        yerr=d["err"],
        fmt="o-",
        ms=5,
        capsize=3,
        color="tab:blue",
        label="filtro (λ conocido)",
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("probabilidad asignada (media del bin)")
    ax.set_ylabel("frecuencia observada")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax_n.bar(d["bin"], d["n"], color="tab:blue", alpha=0.6)
    ax_n.set_yscale("log")
    ax_n.set_xlabel("bin de probabilidad")
    ax_n.set_ylabel("celdas evaluadas")
    fig.suptitle("Calibración del filtro de rejilla (HB5)", fontsize=12, y=1.02)
    fig.tight_layout()
    return fig


# --------------------------------------------------- paquete 4 de C4: escasez

REGIMENES_ESCASEZ: dict[str, str] = {
    "escasez": "mixto (r=3, c=5, p=0.9)",
    "escasez_inf": "replanificar gana (r=∞, c=0, p=1)",
}
"""Los dos barridos de escasez y la etiqueta de cada fila de :func:`fig_escasez`."""


def fig_escasez(metrica: str = "utilidad_neta", backend: Backend | None = None) -> Any:
    """Paquete 4 de C4: ¿depende el valor de replanificar de la abundancia de recursos?

    Una fila por régimen y una columna por λ, con ``n_resources`` en el eje horizontal.
    :func:`lineas` dibuja una sola fila, así que aquí se arma la rejilla a mano con el
    mismo estilo que :func:`_lineas_mpl`. El eje y se comparte dentro de cada fila, no
    entre filas: los dos regímenes viven en escalas distintas. ``backend`` se acepta por
    uniformidad con ``FIGURAS_CLI``; la figura es siempre de matplotlib.
    """
    del backend
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="notebook")
    tidys = {
        nombre: agregar(
            cargar(nombre), x="n_resources", metrica=metrica, faceta="lambda_dinamismo"
        )
        for nombre in REGIMENES_ESCASEZ
    }
    facetas = _facetas(tidys["escasez"])
    n = len(facetas)
    fig, axes = plt.subplots(
        len(tidys), n, figsize=(4.2 * n + 1.2, 3.8 * len(tidys)), sharey="row",
        squeeze=False,
    )
    series = [
        s
        for s in ORDEN_POLITICAS
        if any((t["serie"] == s).any() for t in tidys.values())
    ]
    colores = dict(zip(series, sns.color_palette("colorblind", len(series)), strict=True))
    ylab = metrica.replace("_", " ")

    for fila, (nombre, tidy) in zip(axes, tidys.items(), strict=True):
        for ax, f in zip(fila, facetas, strict=True):
            panel = tidy[tidy["faceta"] == f]
            for s in series:
                d = panel[panel["serie"] == s]
                if d.empty:
                    continue
                ax.plot(d["x"], d["y"], marker="o", ms=4, label=s, color=colores[s])
                ax.fill_between(
                    d["x"], d["y"] - d["err"], d["y"] + d["err"], alpha=0.15,
                    color=colores[s],
                )
            ax.set_xscale("log", base=2)
            ax.set_xticks([2, 4, 8, 16], ["2", "4", "8", "16"])
            ax.set_xlabel("n_resources")
            ax.set_title(f"λ = {f}", fontsize=10)
        fila[0].set_ylabel(f"{REGIMENES_ESCASEZ[nombre]}\n{ylab}", fontsize=9)
        fila[-1].legend(frameon=False, fontsize=8, loc="best")
    fig.suptitle(
        f"Escasez: {ylab} por número de recursos, dinamismo y régimen", fontsize=12, y=1.01
    )
    fig.tight_layout()
    return fig


FIGURAS_CLI: dict[str, Any] = {
    "01-frontera": fig_frontera,
    "02-hot-vs-cold": fig_hot_vs_cold,
    "03-competencia": fig_competencia,
    "04-observabilidad": fig_observabilidad,
    "05-gobernanza": fig_gobernanza,
    "06-conocimiento": fig_conocimiento,
    "07-fiabilidad-filtro": fig_calibracion,
    "11-escasez": fig_escasez,
}


def main() -> None:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figuras", action="store_true", help="exportar todas las figuras")
    parser.add_argument("--controles", action="store_true", help="tabla de sanidad")
    parser.add_argument("--delta", action="store_true", help="tabla caliente vs. frío")
    parser.add_argument(
        "--backend", choices=("mpl", "plotly"), default=BACKEND, help="motor de dibujo"
    )
    args = parser.parse_args()
    if not (args.figuras or args.controles or args.delta):
        parser.error("elegir al menos una de --figuras, --controles, --delta")

    if args.controles:
        print(controles().to_string(index=False))
    if args.delta:
        print(delta_hot_vs_cold().to_string(index=False))
    if args.figuras:
        for nombre, fn in FIGURAS_CLI.items():
            destino = guardar(fn(backend=args.backend), FIGURAS / f"{nombre}.png")
            print(f"{destino}")


if __name__ == "__main__":
    main()
