"""Lectura, agregación y figuras de los barridos.

Este módulo es la capa que faltaba entre ``results/*.csv`` y una conclusión legible. Se
divide en dos partes deliberadamente separadas:

- **datos** — :func:`cargar`, :func:`agregar`, :func:`delta_hot_vs_cold` y
  :func:`controles` devuelven ``DataFrame``\\ s y no saben nada de gráficas;
- **dibujo** — :func:`lineas` recibe uno de esos ``DataFrame``\\ s en formato largo y lo
  pinta con el backend activo.

Las cinco figuras del trabajo son el mismo objeto gráfico (líneas por serie, banda de
error, facetas en rejilla), así que el backend se cambia en un solo sitio::

    analysis.BACKEND = "plotly"          # global
    analysis.fig_frontera(backend="mpl") # o por llamada

Uso::

    PYTHONPATH=project uv run python -m oasys_abm.analysis --figuras
    PYTHONPATH=project uv run python -m oasys_abm.analysis --controles
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Literal

from oasys_abm.agents import Policy
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
            f"    PYTHONPATH=project uv run python -m oasys_abm.experiments "
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


def delta_hot_vs_cold(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """El costo de que ``run=hot`` no esté implementado, en unidades del modelo.

    ``CLOSED_LOOP`` es ``run=hot`` y ``COLD_RESTART`` es lo que OASys hace hoy: reparar el
    plan en sitio contra tirar el trabajo en vuelo y reiniciar (``docs/02-design.md`` §3).
    La diferencia entre ambos es el entregable que vuelve al sistema real.
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
    """Los tres controles de sanidad de ``docs/02-design.md`` §9, evaluados.

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
    tidy: pd.DataFrame, *, titulo: str, xlab: str, ylab: str, faceta_lab: str
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
            ax.plot(d["x"], d["y"], marker="o", ms=4, label=str(s), color=colores[s])
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
    tidy: pd.DataFrame, *, titulo: str, xlab: str, ylab: str, faceta_lab: str
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
        markers=True,
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
) -> Any:
    """Pintar un ``DataFrame`` de :func:`agregar` con el backend activo."""
    fn = _lineas_mpl if (backend or BACKEND) == "mpl" else _lineas_plotly
    return fn(tidy, titulo=titulo, xlab=xlab, ylab=ylab, faceta_lab=faceta_lab)


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
    """Cuánto vale implementar ``run=hot``: CLOSED_LOOP − COLD_RESTART."""
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
        titulo="Costo de no implementar run=hot (CLOSED_LOOP − COLD_RESTART)",
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
    """El efecto del set ``ignore`` de OASys: ver menos, enterarse más tarde."""
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


def fig_trayectoria(pasos: int = 120, backend: Backend | None = None, **kwargs: Any) -> Any:
    """Una corrida concreta, para ver el mecanismo antes de mirar agregados.

    Dibuja la retícula con sus obstáculos y la traza del recolector. Solo tiene backend
    matplotlib: es un mapa, no una serie, y no comparte la primitiva de :func:`lineas`.
    """
    import matplotlib.pyplot as plt
    from oasys_abm.agents import Resource
    from oasys_abm.model import OASysWorld
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


FIGURAS_CLI: dict[str, Any] = {
    "01-frontera": fig_frontera,
    "02-hot-vs-cold": fig_hot_vs_cold,
    "03-competencia": fig_competencia,
    "04-observabilidad": fig_observabilidad,
    "05-gobernanza": fig_gobernanza,
}


def main() -> None:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figuras", action="store_true", help="exportar todas las figuras")
    parser.add_argument("--controles", action="store_true", help="tabla de sanidad")
    parser.add_argument("--delta", action="store_true", help="tabla hot vs cold")
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
