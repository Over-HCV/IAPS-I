"""Análisis de sensibilidad sobre las corridas guardadas (paquete C5-S).

Responde, sin correr nada, qué parámetro mueve más la utilidad de cada política: para cada
barrido y cada política, la fracción de la varianza de ``utilidad_neta`` que explica cada
factor barrido. Y lo mismo para la diferencia pareada por semilla ``OPEN_LOOP −
CLOSED_LOOP``, que es la pregunta del proyecto (``docs/roadmap-c5.md`` §C5-S).

Dos medidas, ambas en [0, 1]:

- **η² de un factor** — :math:`SS_{\\text{entre}} / SS_{\\text{total}}`: la varianza que
  desaparece al reemplazar cada corrida por la media de su nivel. En un diseño factorial
  balanceado los η² de los factores principales suman a lo sumo 1; el resto es
  interacción más ruido de semilla.
- **η² parcial** — :math:`SS_{\\text{efecto}} / (SS_{\\text{efecto}} + SS_{\\text{res}})`
  sobre un modelo aditivo (solo efectos principales) ajustado por mínimos cuadrados, con
  sumas de tipo II. Descuenta la varianza que ya explican los otros factores; con un solo
  factor coincide con η².

Uso, desde la raíz del repositorio::

    python -m project.sensibilidad
    python -m project.sensibilidad --figuras
"""

from __future__ import annotations

import argparse
from typing import Any, NamedTuple

import numpy as np
import pandas as pd

from project.analysis import (
    BACKEND,
    FIGURAS,
    ORDEN_POLITICAS,
    Backend,
    cargar,
    guardar,
)

BARRIDOS: dict[str, list[str]] = {
    "principal": ["lambda_dinamismo", "costo_edicion"],
    "competencia": ["lambda_dinamismo", "competencia"],
    "observabilidad": ["lambda_dinamismo", "radio"],
    "gobernanza": ["lambda_dinamismo", "presupuesto"],
}
"""Factores que varía cada barrido. Replica las listas de ``experiments.SWEEPS`` (salvo
``policy``, que aquí es la variable de agrupación, no un factor); un test vigila que no se
desincronicen."""

ETIQUETAS: dict[str, str] = {
    "lambda_dinamismo": "λ (dinamismo)",
    "costo_edicion": "c (costo de edición)",
    "competencia": "p (competencia)",
    "radio": "r (radio de visión)",
    "presupuesto": "B (presupuesto)",
}
"""Nombre corto de cada factor en tablas y figuras, con la notación de ``info/``."""

CONTRASTE = ("OPEN_LOOP", "CLOSED_LOOP")
"""El contraste pareado por defecto: lazo abierto menos lazo cerrado."""


# --------------------------------------------------------------------------- datos


def _ss_total(y: pd.Series) -> float:
    """Suma de cuadrados alrededor de la media global."""
    return float(((y - y.mean()) ** 2).sum())


def eta2(df: pd.DataFrame, factor: str, metrica: str = "utilidad_neta") -> float:
    """η² de un factor: :math:`SS_{\\text{entre}} / SS_{\\text{total}}`.

    Args:
        df: una fila por corrida.
        factor: columna cuyos niveles definen los grupos.
        metrica: columna respuesta.

    Returns:
        Un número en [0, 1]; ``0`` si la métrica no varía (no hay varianza que explicar).
    """
    d = df[[factor, metrica]].dropna(subset=[metrica])
    y = d[metrica].astype(float)
    total = _ss_total(y)
    if total == 0:
        return 0.0
    medias = d.groupby(factor, dropna=False)[metrica].transform("mean")
    entre = float(((medias - y.mean()) ** 2).sum())
    return entre / total


def _diseno(df: pd.DataFrame, factores: list[str]) -> np.ndarray:
    """Matriz de diseño aditiva: intercepto más indicadores (referencia = primer nivel)."""
    columnas = [np.ones(len(df))]
    for f in factores:
        dummies = pd.get_dummies(df[f].astype(str), drop_first=True, dtype=float)
        columnas.extend(dummies[c].to_numpy() for c in dummies.columns)
    return np.column_stack(columnas)


def _rss(X: np.ndarray, y: np.ndarray) -> float:
    """Suma de cuadrados residual del ajuste por mínimos cuadrados."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ beta
    return float(r @ r)


def eta2_parcial(
    df: pd.DataFrame, factores: list[str], metrica: str = "utilidad_neta"
) -> dict[str, float]:
    """η² parcial de cada factor en el modelo aditivo de efectos principales.

    Usa sumas de cuadrados de tipo II: el efecto de un factor es lo que crece la suma
    residual al quitarlo del modelo completo. En un diseño balanceado coincide con el
    :math:`SS_{\\text{entre}}` de :func:`eta2`, pero el denominador descarta la varianza de
    los demás factores.

    Returns:
        ``{factor: η² parcial}``; ``0`` para un factor sin efecto o sin varianza residual
        ni de efecto.
    """
    d = df.dropna(subset=[metrica])
    y = d[metrica].to_numpy(dtype=float)
    rss_completo = _rss(_diseno(d, factores), y)
    out: dict[str, float] = {}
    for f in factores:
        otros = [g for g in factores if g != f]
        efecto = max(_rss(_diseno(d, otros), y) - rss_completo, 0.0)
        denom = efecto + rss_completo
        out[f] = efecto / denom if denom > 0 else 0.0
    return out


def _con_varianza(df: pd.DataFrame, factores: list[str]) -> list[str]:
    """Los factores con más de un nivel en ``df``: los únicos que pueden explicar algo."""
    return [f for f in factores if f in df.columns and df[f].nunique(dropna=False) > 1]


def sensibilidad(
    df: pd.DataFrame,
    factores: list[str],
    metrica: str = "utilidad_neta",
    por: str = "politica",
) -> pd.DataFrame:
    """η² y η² parcial de cada factor, dentro de cada grupo de ``por``.

    Args:
        df: una fila por corrida.
        factores: columnas candidatas; se descartan las que tienen un solo nivel.
        metrica: columna respuesta.
        por: columna que separa los análisis (por defecto, una tabla por política).

    Returns:
        Formato largo con columnas ``[por, "factor", "eta2", "eta2_parcial"]``.
    """
    filas: list[dict[str, Any]] = []
    for grupo, sub in df.groupby(por, sort=False):
        fs = _con_varianza(sub, factores)
        parcial = eta2_parcial(sub, fs, metrica) if fs else {}
        for f in fs:
            filas.append(
                {
                    por: grupo,
                    "factor": f,
                    "eta2": eta2(sub, f, metrica),
                    "eta2_parcial": parcial[f],
                }
            )
    out = pd.DataFrame(filas, columns=[por, "factor", "eta2", "eta2_parcial"])
    if por == "politica":
        orden = [p for p in ORDEN_POLITICAS if p in set(out[por])]
        out[por] = pd.Categorical(out[por], categories=orden, ordered=True)
        out = out.sort_values([por, "factor"], kind="stable").reset_index(drop=True)
        out[por] = out[por].astype(str)
    return out


class Delta(NamedTuple):
    """Resultado de :func:`sensibilidad_delta`."""

    eta2: pd.DataFrame
    """``[factor, eta2, eta2_parcial]`` de la diferencia pareada."""
    medias: pd.DataFrame
    """``[factor, nivel, media, err, n]``: diferencia media por nivel de cada factor."""
    pares: pd.DataFrame
    """Una fila por par (semilla × celda) con la columna ``delta``."""


def pares(
    df: pd.DataFrame,
    a: str = CONTRASTE[0],
    b: str = CONTRASTE[1],
    *,
    claves: list[str],
    metrica: str = "utilidad_neta",
    por: str = "politica",
) -> pd.DataFrame:
    """Emparejar las corridas de ``a`` y ``b`` que comparten ``claves`` y calcular ``a − b``.

    Raises:
        ValueError: si alguna combinación de ``claves`` se repite dentro de una política
            (el par sería ambiguo) o si falta alguna de las dos políticas.
    """
    sub = df[df[por].isin([a, b])]
    faltan = {a, b} - set(sub[por])
    if faltan:
        raise ValueError(f"faltan las políticas {sorted(faltan)} para el contraste")
    if sub.duplicated([*claves, por]).any():
        raise ValueError(f"las claves {claves} no identifican una corrida por política")
    ancho = sub.pivot(index=claves, columns=por, values=metrica).dropna()
    ancho["delta"] = ancho[a] - ancho[b]
    return ancho.reset_index()


def sensibilidad_delta(
    df: pd.DataFrame,
    a: str = CONTRASTE[0],
    b: str = CONTRASTE[1],
    factores: list[str] | None = None,
    metrica: str = "utilidad_neta",
    *,
    semilla: str = "rng",
) -> Delta:
    """Sensibilidad de la diferencia pareada ``a − b``.

    Cada corrida de ``a`` se empareja con la de ``b`` que tiene la misma semilla y los
    mismos valores de todos los factores; el ruido común de semilla (el mismo mundo, los
    mismos eventos) se cancela en la resta, y lo que queda se descompone por factor.

    Args:
        df: una fila por corrida, con ambas políticas.
        a, b: políticas del contraste.
        factores: columnas barridas; ``None`` para todas las de :data:`ETIQUETAS`
            presentes en ``df``.
        metrica: columna respuesta.
        semilla: columna de la semilla.
    """
    factores = list(ETIQUETAS) if factores is None else factores
    factores = [f for f in factores if f in df.columns]
    par = pares(df, a, b, claves=[*factores, semilla], metrica=metrica)
    fs = _con_varianza(par, factores)
    parcial = eta2_parcial(par, fs, "delta") if fs else {}
    tabla = pd.DataFrame(
        [
            {"factor": f, "eta2": eta2(par, f, "delta"), "eta2_parcial": parcial[f]}
            for f in fs
        ],
        columns=["factor", "eta2", "eta2_parcial"],
    )
    medias = []
    for f in fs:
        g = par.groupby(f)["delta"].agg(["mean", "std", "count"]).reset_index()
        g["err"] = g["std"] / g["count"] ** 0.5
        g = g.rename(columns={f: "nivel", "mean": "media", "count": "n"})
        g.insert(0, "factor", f)
        medias.append(g[["factor", "nivel", "media", "err", "n"]])
    medias_df = (
        pd.concat(medias, ignore_index=True)
        if medias
        else pd.DataFrame(columns=["factor", "nivel", "media", "err", "n"])
    )
    return Delta(eta2=tabla, medias=medias_df, pares=par)


def _cargar_si_existe(nombre: str) -> pd.DataFrame | None:
    """:func:`cargar`, o ``None`` si el barrido no se ha corrido."""
    try:
        return cargar(nombre)
    except FileNotFoundError:
        return None


def tabla_sensibilidad(
    metrica: str = "utilidad_neta", barridos: dict[str, list[str]] | None = None
) -> pd.DataFrame:
    """η² por barrido, política y factor sobre los CSV guardados.

    Los barridos que falten se omiten (no hay nada que leer). Columnas: ``barrido``,
    ``politica``, ``factor``, ``eta2``, ``eta2_parcial``.
    """
    barridos = BARRIDOS if barridos is None else barridos
    partes = []
    for nombre, factores in barridos.items():
        df = _cargar_si_existe(nombre)
        if df is None:
            continue
        t = sensibilidad(df, factores, metrica)
        t.insert(0, "barrido", nombre)
        partes.append(t)
    if not partes:
        return pd.DataFrame(columns=["barrido", "politica", "factor", "eta2", "eta2_parcial"])
    return pd.concat(partes, ignore_index=True)


def tabla_sensibilidad_delta(
    metrica: str = "utilidad_neta",
    a: str = CONTRASTE[0],
    b: str = CONTRASTE[1],
    barridos: dict[str, list[str]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """La versión pareada de :func:`tabla_sensibilidad`, para los barridos con ``a`` y ``b``.

    Returns:
        ``(eta2, medias)``, ambos con una columna ``barrido`` y la columna ``contraste``
        en la primera.
    """
    barridos = BARRIDOS if barridos is None else barridos
    etas, medias = [], []
    for nombre, factores in barridos.items():
        df = _cargar_si_existe(nombre)
        if df is None or not {a, b} <= set(df["politica"]):
            continue
        r = sensibilidad_delta(df, a, b, factores, metrica)
        e = r.eta2.copy()
        e.insert(0, "contraste", f"{a} − {b}")
        e.insert(0, "barrido", nombre)
        m = r.medias.copy()
        m.insert(0, "barrido", nombre)
        etas.append(e)
        medias.append(m)
    cols_e = ["barrido", "contraste", "factor", "eta2", "eta2_parcial"]
    cols_m = ["barrido", "factor", "nivel", "media", "err", "n"]
    return (
        pd.concat(etas, ignore_index=True) if etas else pd.DataFrame(columns=cols_e),
        pd.concat(medias, ignore_index=True) if medias else pd.DataFrame(columns=cols_m),
    )


# ------------------------------------------------------------------------- figuras


def _barras_mpl(
    tabla: pd.DataFrame, *, y: str, titulo: str, xlab: str = "η²"
) -> Any:
    """Barras horizontales agrupadas: una faceta por barrido, una barra por factor."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="notebook")
    barridos = list(dict.fromkeys(tabla["barrido"]))
    factores = list(dict.fromkeys(f for f in ETIQUETAS if f in set(tabla["factor"])))
    colores = dict(zip(factores, sns.color_palette("colorblind", len(factores)), strict=True))
    filas_max = max(tabla.groupby("barrido")[y].nunique().max(), 1)
    n = len(barridos)
    fig, axes = plt.subplots(
        1, n, figsize=(3.8 * n + 1.2, 0.55 * filas_max + 1.8), sharex=True, squeeze=False
    )
    for ax, nombre in zip(axes[0], barridos, strict=True):
        panel = tabla[tabla["barrido"] == nombre]
        cats = list(dict.fromkeys(panel[y]))
        if y == "politica":
            cats = [p for p in ORDEN_POLITICAS if p in cats]
        presentes = [f for f in factores if f in set(panel["factor"])]
        alto = 0.8 / max(len(presentes), 1)
        for j, f in enumerate(presentes):
            d = panel[panel["factor"] == f].set_index(y).reindex(cats)
            pos = np.arange(len(cats)) + (j - (len(presentes) - 1) / 2) * alto
            ax.barh(pos, d["eta2"].fillna(0), height=alto, color=colores[f], label=ETIQUETAS[f])
            for p, v in zip(pos, d["eta2"].fillna(0), strict=True):
                ax.text(v + 0.01, p, f"{v:.2f}", va="center", fontsize=7)
        ax.set_yticks(np.arange(len(cats)), cats, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlim(0, 1.12)
        ax.set_xlabel(xlab)
        ax.set_title(nombre, fontsize=10)
    manejadores = {}
    for ax in axes[0]:
        for h, lab in zip(*ax.get_legend_handles_labels(), strict=True):
            manejadores.setdefault(lab, h)
    fig.legend(
        manejadores.values(),
        manejadores.keys(),
        frameon=False,
        fontsize=8,
        loc="lower center",
        ncol=len(manejadores),
        bbox_to_anchor=(0.5, -0.02),
    )
    fig.suptitle(titulo, fontsize=12, y=1.02)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return fig


def fig_sensibilidad(
    backend: Backend | None = None, tabla: pd.DataFrame | None = None
) -> Any:
    """η² de cada factor sobre ``utilidad_neta``, por política, una faceta por barrido."""
    if (backend or BACKEND) == "plotly":
        raise NotImplementedError("fig_sensibilidad solo dibuja con matplotlib")
    tabla = tabla_sensibilidad() if tabla is None else tabla
    return _barras_mpl(
        tabla,
        y="politica",
        titulo="¿Qué factor mueve la utilidad neta de cada política? (η² de un factor)",
    )


def fig_sensibilidad_delta(
    backend: Backend | None = None,
    tabla: pd.DataFrame | None = None,
    medias: pd.DataFrame | None = None,
) -> Any:
    """La diferencia pareada ``OPEN_LOOP − CLOSED_LOOP``, una columna por barrido.

    Arriba, el η² de cada factor sobre la diferencia; abajo, la diferencia media (± error
    estándar) en cada nivel de cada factor. El η² dice cuánto de la variación del
    contraste explica el factor; las medias dicen hacia dónde lo empuja.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    if (backend or BACKEND) == "plotly":
        raise NotImplementedError("fig_sensibilidad_delta solo dibuja con matplotlib")
    if tabla is None or medias is None:
        t, m = tabla_sensibilidad_delta()
        tabla = t if tabla is None else tabla
        medias = m if medias is None else medias

    sns.set_theme(style="whitegrid", context="notebook")
    barridos = list(dict.fromkeys(tabla["barrido"]))
    factores = [f for f in ETIQUETAS if f in set(tabla["factor"])]
    colores = dict(zip(factores, sns.color_palette("colorblind", len(factores)), strict=True))
    niveles_max = max(medias.groupby("barrido").size().max(), 1)
    n = len(barridos)
    fig, axes = plt.subplots(
        2,
        n,
        figsize=(4.2 * n + 1.2, 2.0 + 0.32 * niveles_max + 1.6),
        squeeze=False,
        gridspec_kw={"height_ratios": [1.0, max(niveles_max / 4, 1.5)]},
    )
    for j, nombre in enumerate(barridos):
        arriba, abajo = axes[0][j], axes[1][j]
        e = tabla[tabla["barrido"] == nombre].set_index("factor")
        fs = [f for f in factores if f in e.index]
        pos = np.arange(len(fs))
        valores = e.loc[fs, "eta2"].to_numpy(dtype=float)
        arriba.barh(pos, valores, color=[colores[f] for f in fs], height=0.6)
        for p, v in zip(pos, valores, strict=True):
            arriba.text(v + 0.005, p, f"{v:.3f}", va="center", fontsize=8)
        arriba.set_yticks(pos, [ETIQUETAS[f] for f in fs], fontsize=8)
        arriba.invert_yaxis()
        arriba.set_xlim(0, max(0.25, 1.3 * float(tabla["eta2"].max())))
        arriba.set_xlabel("η² de la diferencia", fontsize=9)
        arriba.set_title(nombre, fontsize=10)

        m = medias[medias["barrido"] == nombre]
        m = m[m["factor"].isin(fs)]
        m = m.assign(_o=m["factor"].map(fs.index)).sort_values("_o", kind="stable")
        pos = np.arange(len(m))
        abajo.barh(
            pos,
            m["media"],
            xerr=m["err"],
            color=[colores[f] for f in m["factor"]],
            height=0.6,
            error_kw={"elinewidth": 0.8, "capsize": 2},
        )
        etiquetas = [
            f"{ETIQUETAS[f].split()[0]} = {nv}" for f, nv in zip(m["factor"], m["nivel"], strict=True)
        ]
        abajo.set_yticks(pos, etiquetas, fontsize=8)
        abajo.invert_yaxis()
        abajo.axvline(0, color="0.3", lw=0.8)
        abajo.set_xlabel("Δ utilidad media (± e.e.)", fontsize=9)
    a, b = CONTRASTE
    fig.suptitle(
        f"¿Qué factor explica la diferencia {a} − {b}? (pareada por semilla)",
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()
    return fig


FIGURAS_CLI: dict[str, Any] = {
    "08-sensibilidad": fig_sensibilidad,
    "09-sensibilidad-delta": fig_sensibilidad_delta,
}


def main() -> None:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figuras", action="store_true", help="exportar las figuras 08 y 09")
    parser.add_argument("--metrica", default="utilidad_neta", help="columna respuesta")
    args = parser.parse_args()

    pd.set_option("display.width", 140)
    tabla = tabla_sensibilidad(args.metrica)
    print(f"η² de un factor sobre {args.metrica}, por barrido y política\n")
    print(tabla.round(3).to_string(index=False))
    eta, medias = tabla_sensibilidad_delta(args.metrica)
    print(f"\nη² de la diferencia pareada {CONTRASTE[0]} − {CONTRASTE[1]}\n")
    print(eta.round(3).to_string(index=False))
    print("\nDiferencia media por nivel\n")
    print(medias.round(2).to_string(index=False))
    if args.figuras:
        for nombre, fn in FIGURAS_CLI.items():
            destino = guardar(fn(), FIGURAS / f"{nombre}.png")
            print(destino)


if __name__ == "__main__":
    main()
