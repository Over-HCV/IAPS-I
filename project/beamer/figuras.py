"""Figuras de la presentación final (project/beamer/figuras/).

Responsabilidad: dibujar, a tamaño de diapositiva, las figuras que el deck necesita y
que ``results/figuras/`` no trae en esa forma. Ninguna cifra se escribe a mano: todo
sale de los CSV y parquet de ``project/results/`` a través de las mismas funciones
del paquete (``analysis``, ``sensibilidad``, ``calibracion``, ``animacion``).

Se corre desde ``figuras.sh`` (que además copia las figuras de resultados que entran
tal cual). Directamente, desde la raíz del repositorio:

    PYTHONPATH=. .venv/bin/python project/beamer/figuras.py [nombre ...]

Convenciones, para que el deck se lea como un solo sistema:

- **Tamaño físico = tamaño en la diapositiva.** El papel 16:9 de beamer mide
  16 × 9 cm; el área útil bajo la banda del título es de unos 14,4 × 6,8 cm
  (5,7 × 2,7 in). Cada figura se dibuja a las pulgadas con que se va a mostrar, de
  forma que 8–9 pt en matplotlib son 8–9 pt en la diapositiva (≈ \\footnotesize).
- **Una política, un color, en todas las figuras.** La paleta ``colorblind`` de
  seaborn en el orden de la taxonomía (el mismo de ``01-frontera.png``, que es la
  única figura de resultados con las seis políticas originales a la vez). Las dos
  políticas nuevas llevan el celeste del mismo paleta (``KNOWLEDGE_BASED``) y un
  violeta (``BAYESIAN``) validado contra el fondo del tema. Además del color, cada
  política tiene su marcador (identidad nunca solo por color).
- **Fondo transparente**, tipografía TeX Gyre Heros (la del tema Midcentury), tinta
  y grilla recesivas tomadas de la paleta del tema DeepBlue.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

from project import analysis as an  # noqa: E402

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "figuras"

# ----------------------------------------------------------------------- estilo

# Tema DeepBlue de Midcentury Modern (tema/beamerthememidcenturymodern.sty).
PRIMARIO = "#002d4d"
OSCURO = "#1a2a3b"
ACENTO = "#BFE5EE"
FONDO = "#F8F6F2"
TINTA = "#1A1A1A"
TINTA2 = "#55565a"
GRILLA = "#dcd8cf"
ALERTA = "#E8637D"
AMBAR = "#DB6720"

POLITICAS = [
    "REFLEX",
    "MODEL_BASED",
    "OPEN_LOOP",
    "COLD_RESTART",
    "CLOSED_LOOP",
    "GOVERNED",
    "KNOWLEDGE_BASED",
    "BAYESIAN",
]
COLOR = {
    "REFLEX": "#0173b2",
    "MODEL_BASED": "#de8f05",
    "OPEN_LOOP": "#029e73",
    "COLD_RESTART": "#d55e00",
    "CLOSED_LOOP": "#cc78bc",
    "GOVERNED": "#ca9161",
    "KNOWLEDGE_BASED": "#56b4e9",
    "BAYESIAN": "#6a51c9",
}
MARCA = {
    "REFLEX": "v",
    "MODEL_BASED": "o",
    "OPEN_LOOP": "^",
    "COLD_RESTART": "X",
    "CLOSED_LOOP": "s",
    "GOVERNED": "P",
    "KNOWLEDGE_BASED": "D",
    "BAYESIAN": "h",
}
# Rampa secuencial de un solo tono (el azul del tema) para magnitudes ordenadas: c.
RAMPA_C = ["#a9cfe0", "#5d9cc4", "#2a6b9b", PRIMARIO]


def _fuente() -> list[str]:
    """Registrar TeX Gyre Heros desde el árbol de TeX; si no está, Helvetica."""
    try:
        ruta = subprocess.run(
            ["kpsewhich", "texgyreheros-regular.otf"], capture_output=True, text=True
        ).stdout.strip()
    except OSError:
        ruta = ""
    if ruta:
        carpeta = Path(ruta).parent
        for estilo in ("regular", "bold", "italic", "bolditalic"):
            f = carpeta / f"texgyreheros-{estilo}.otf"
            if f.exists():
                font_manager.fontManager.addfont(str(f))
        return ["TeX Gyre Heros", "Helvetica", "DejaVu Sans"]
    return ["Helvetica", "Arial", "DejaVu Sans"]


def estilo() -> None:
    """rcParams comunes: tamaños a escala de diapositiva, ejes recesivos."""
    mpl.rcdefaults()
    plt.rcParams.update(
        {
            "font.family": _fuente(),
            "font.size": 9,
            "axes.titlesize": 9.5,
            "axes.titleweight": "bold",
            "axes.titlecolor": PRIMARIO,
            "axes.labelsize": 9,
            "axes.labelcolor": TINTA,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "xtick.color": TINTA2,
            "ytick.color": TINTA2,
            "legend.fontsize": 8,
            "legend.frameon": False,
            "axes.edgecolor": "#8f8c86",
            "axes.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": GRILLA,
            "grid.linewidth": 0.5,
            "axes.facecolor": "none",
            "figure.facecolor": "none",
            "savefig.facecolor": "none",
            "savefig.transparent": True,
            "text.color": TINTA,
            "lines.linewidth": 1.6,
            "lines.markersize": 4.5,
            "axes.unicode_minus": True,
            "xtick.major.size": 2.5,
            "ytick.major.size": 2.5,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
        }
    )


def guardar(fig: Any, nombre: str, *, transparente: bool = True) -> Path:
    """PNG a 300 ppp en figuras/, recortado al contenido."""
    SALIDA.mkdir(exist_ok=True)
    ruta = SALIDA / f"{nombre}.png"
    fig.savefig(ruta, dpi=300, bbox_inches="tight", pad_inches=0.03, transparent=transparente)
    plt.close(fig)
    print(f"  {ruta.relative_to(AQUI)}")
    return ruta


def _lam(x: float) -> str:
    return f"{x:g}"


# ----------------------------------------------------------------------- datos


def _medias(df: pd.DataFrame, claves: list[str], metrica: str = "utilidad_neta") -> pd.DataFrame:
    g = df.groupby([*claves, "politica"])[metrica]
    out = g.agg(["mean", "std", "count"]).reset_index()
    out["err"] = out["std"] / out["count"] ** 0.5
    return out


def _linea(ax: Any, x: Any, y: Any, err: Any, pol: str, *, lw: float = 1.6, ms: float = 4.5,
           banda: bool = True, **kw: Any) -> None:
    ax.plot(x, y, color=COLOR[pol], marker=MARCA[pol], lw=lw, ms=ms, label=pol,
            markeredgewidth=0, zorder=3, **kw)
    if banda:
        ax.fill_between(x, np.asarray(y) - np.asarray(err), np.asarray(y) + np.asarray(err),
                        color=COLOR[pol], alpha=0.14, lw=0, zorder=2)


# --------------------------------------------------------------- 1. la frontera


def fig_frontera() -> None:
    """Utilidad contra λ con c = 2 y c = 5: la frontera es deliberar contra no deliberar."""
    df = an.cargar("principal")
    m = _medias(df, ["lambda_dinamismo", "costo_edicion"])
    pols = ["REFLEX", "MODEL_BASED", "OPEN_LOOP", "COLD_RESTART", "CLOSED_LOOP"]
    fig, axes = plt.subplots(1, 2, figsize=(5.75, 2.55), sharey=True)
    for ax, c in zip(axes, (2, 5), strict=True):
        sub = m[m.costo_edicion == c]
        for pol in pols:
            d = sub[sub.politica == pol].sort_values("lambda_dinamismo")
            _linea(ax, d.lambda_dinamismo, d["mean"], d.err, pol,
                   lw=2.4 if pol == "MODEL_BASED" else 1.4)
        ax.set_title(f"c = {c} ticks por reparación", loc="left")
        ax.set_xlabel("λ (probabilidad de deriva por tick)")
        ax.set_xticks([0, 0.1, 0.25, 0.5], ["0", "0.1", "0.25", "0.5"])
        ax.set_xlim(-0.015, 0.53)
        # el número que decide la celda λ=0.5: MB contra la mejor que planifica
        mb = sub[(sub.politica == "MODEL_BASED") & (sub.lambda_dinamismo == 0.5)]["mean"].item()
        plan = sub[sub.politica.isin(["OPEN_LOOP", "COLD_RESTART", "CLOSED_LOOP"])
                   & (sub.lambda_dinamismo == 0.5)]["mean"].max()
        ax.annotate(f"{mb:.1f}", (0.5, mb), xytext=(0, 5), textcoords="offset points",
                    ha="center", fontsize=8, color=TINTA, weight="bold")
        ax.annotate(f"{plan:.1f}", (0.5, plan), xytext=(0, 5), textcoords="offset points",
                    ha="center", fontsize=8, color=TINTA2)
    axes[0].set_ylabel("utilidad neta (10 × entregas)")
    axes[0].set_ylim(0, 118)
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.08),
               handlelength=1.6, columnspacing=1.1, fontsize=7.6)
    fig.tight_layout(w_pad=1.2)
    guardar(fig, "frontera")


def fig_frontera_completa() -> None:
    """Respaldo: las cuatro c con las seis políticas originales, misma paleta."""
    df = an.cargar("principal")
    m = _medias(df, ["lambda_dinamismo", "costo_edicion"])
    pols = POLITICAS[:6]
    fig, axes = plt.subplots(1, 4, figsize=(5.9, 2.3), sharey=True)
    for ax, c in zip(axes, (0, 2, 5, 10), strict=True):
        sub = m[m.costo_edicion == c]
        for pol in pols:
            d = sub[sub.politica == pol].sort_values("lambda_dinamismo")
            _linea(ax, d.lambda_dinamismo, d["mean"], d.err, pol, lw=1.2, ms=3,
                   ls="--" if pol == "GOVERNED" else "-")
        ax.set_title(f"c = {c}", loc="left")
        ax.set_xticks([0, 0.25, 0.5], ["0", "0.25", "0.5"])
        ax.set_xlabel("λ")
    axes[0].set_ylabel("utilidad neta")
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, ncol=6, loc="upper center", bbox_to_anchor=(0.5, 1.08),
               fontsize=6.8, handlelength=1.4, columnspacing=0.8)
    fig.tight_layout(w_pad=0.4)
    guardar(fig, "frontera-completa")


# ------------------------------------------------- 2. abierto contra cerrado


def _dif(df: pd.DataFrame, a: str, b: str, por: tuple[str, ...]) -> pd.DataFrame:
    return an.diferencia_pareada(df, a, b, por=por)


def fig_abierto_cerrado() -> None:
    """OL − CL por celda (λ, c), con ±2 EE: casi todo dentro del ruido."""
    df = an.cargar("principal")
    d = _dif(df, "OPEN_LOOP", "CLOSED_LOOP", ("lambda_dinamismo", "costo_edicion"))
    d = d[d.lambda_dinamismo > 0]
    lams = sorted(d.lambda_dinamismo.unique())
    cs = sorted(d.costo_edicion.unique())
    fig, ax = plt.subplots(figsize=(3.55, 2.6))
    ax.axhline(0, color=TINTA2, lw=0.8, zorder=1)
    ancho = 0.17
    for j, c in enumerate(cs):
        sub = d[d.costo_edicion == c].set_index("lambda_dinamismo").loc[lams]
        xs = np.arange(len(lams)) + (j - 1.5) * ancho
        fuera = (sub.media.abs() > 2 * sub.err).to_numpy()
        ax.errorbar(xs, sub.media, yerr=2 * sub.err, fmt="none", ecolor=RAMPA_C[j],
                    elinewidth=1.1, capsize=0, zorder=2)
        ax.scatter(xs[~fuera], sub.media[~fuera], s=22, facecolor=FONDO,
                   edgecolor=RAMPA_C[j], lw=1.3, zorder=3)
        ax.scatter(xs[fuera], sub.media[fuera], s=26, color=RAMPA_C[j], zorder=3)
        # una entrada de leyenda por c, siempre rellena, haya o no celdas fuera del ruido
        ax.scatter([], [], s=26, color=RAMPA_C[j], label=f"c = {c}")
    ax.set_xticks(range(len(lams)), [_lam(x) for x in lams])
    ax.set_xlabel("λ")
    ax.set_ylabel("OPEN_LOOP − CLOSED_LOOP  (± 2 EE)")
    ax.text(0.02, 0.97, "a favor del lazo abierto", transform=ax.transAxes, fontsize=7.5,
            color=TINTA2, va="top")
    ax.text(0.02, 0.03, "a favor del lazo cerrado", transform=ax.transAxes, fontsize=7.5,
            color=TINTA2, va="bottom")
    ax.set_ylim(-25, 48)
    ax.scatter([], [], s=22, facecolor=FONDO, edgecolor=TINTA2, lw=1.3,
               label="hueco: ±2 EE cruza el 0")
    ax.legend(loc="lower center", ncol=3, fontsize=7.2, handletextpad=0.2,
              columnspacing=0.8, bbox_to_anchor=(0.5, 1.0))
    ax.grid(False)
    fig.tight_layout()
    guardar(fig, "abierto-cerrado")


# --------------------------------------------------- 3. caliente contra frío


def fig_caliente_frio() -> None:
    """CL − CR por λ y c, con ± EE: el valor de no tirar el trabajo en curso."""
    df = an.cargar("principal")
    d = _dif(df, "CLOSED_LOOP", "COLD_RESTART", ("lambda_dinamismo", "costo_edicion"))
    d = d[d.lambda_dinamismo > 0]
    lams = sorted(d.lambda_dinamismo.unique())
    cs = sorted(d.costo_edicion.unique())
    fig, ax = plt.subplots(figsize=(3.55, 2.6))
    ancho = 0.19
    for j, c in enumerate(cs):
        sub = d[d.costo_edicion == c].set_index("lambda_dinamismo").loc[lams]
        xs = np.arange(len(lams)) + (j - 1.5) * ancho
        ax.bar(xs, sub.media, width=ancho * 0.88, color=RAMPA_C[j], label=f"c = {c}",
               zorder=2)
        ax.errorbar(xs, sub.media, yerr=sub.err, fmt="none", ecolor=TINTA2,
                    elinewidth=0.8, capsize=0, zorder=3)
    ax.axhline(0, color=TINTA2, lw=0.8, zorder=1)
    ax.set_xticks(range(len(lams)), [_lam(x) for x in lams])
    ax.set_xlabel("λ")
    ax.set_ylabel("CLOSED_LOOP − COLD_RESTART  (± EE)")
    ax.set_ylim(-6, 40)
    ax.legend(loc="upper left", ncol=4, fontsize=7.5, handlelength=1.0,
              handletextpad=0.3, columnspacing=0.7)
    ax.text(3 + 1.0 * ancho, 3.0, "c ≥ 5:\nambas\ncolapsan", fontsize=6.8, color=TINTA2,
            ha="center", va="bottom", linespacing=1.0)
    fig.tight_layout()
    guardar(fig, "caliente-frio")


# -------------------------------------------------------------- 4. dinámica


def fig_dinamica() -> None:
    """Entregas acumuladas por tick, λ = 0.1 y λ = 0.5 (c = 5, r = 3)."""
    din = an.cargar_dinamica()
    t = an.agregar_tiempo(din, "entregas")
    pols = ["REFLEX", "MODEL_BASED", "OPEN_LOOP", "COLD_RESTART", "CLOSED_LOOP"]
    fig, axes = plt.subplots(1, 2, figsize=(5.75, 2.5), sharey=True)
    marcas = {0.1: (130, "CLOSED_LOOP > COLD_RESTART\ndesde el tick 130"),
              0.5: (15, "MODEL_BASED > CLOSED_LOOP\ndesde el tick 15")}
    for ax, lam in zip(axes, (0.1, 0.5), strict=True):
        sub = t[t.faceta.astype(float) == lam]
        for pol in pols:
            d = sub[sub.serie == pol].sort_values("x")
            ax.plot(d.x, d.y, color=COLOR[pol], lw=2.2 if pol == "MODEL_BASED" else 1.4,
                    label=pol, zorder=3)
            ax.fill_between(d.x, d.y - d.err, d.y + d.err, color=COLOR[pol], alpha=0.14,
                            lw=0, zorder=2)
            fin = d.iloc[-1]
            ax.plot([fin.x], [fin.y], marker=MARCA[pol], color=COLOR[pol], ms=4.5, zorder=4)
        tick, texto = marcas[lam]
        ax.axvline(tick, color=PRIMARIO, lw=0.9, ls=(0, (3, 2)), zorder=1)
        ax.text(tick + 8, 9.6, texto, fontsize=7.4, color=PRIMARIO, va="top")
        ax.set_title(f"λ = {lam:g}", loc="left")
        ax.set_xlabel("tick")
        ax.set_xlim(0, 410)
        ax.set_xticks([0, 100, 200, 300, 400])
    axes[0].set_ylabel("entregas acumuladas")
    axes[0].set_ylim(0, 10.2)
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.08),
               handlelength=1.6, columnspacing=1.1, fontsize=7.6)
    fig.tight_layout(w_pad=1.2)
    guardar(fig, "dinamica")


# ------------------------------------------------- 5. agentes que infieren


def fig_kb_r3() -> None:
    """Las cinco políticas del barrido `conocimiento` con r = 3."""
    df = an.cargar("conocimiento")
    df = df[df.radio == "3"]
    m = _medias(df, ["lambda_dinamismo"])
    pols = ["MODEL_BASED", "OPEN_LOOP", "CLOSED_LOOP", "KNOWLEDGE_BASED", "BAYESIAN"]
    fig, ax = plt.subplots(figsize=(3.0, 2.6))
    for pol in pols:
        d = m[m.politica == pol].sort_values("lambda_dinamismo")
        _linea(ax, d.lambda_dinamismo, d["mean"], d.err, pol,
               lw=2.2 if pol == "KNOWLEDGE_BASED" else 1.4)
    fin = m[m.lambda_dinamismo == 0.5].set_index("politica")["mean"]
    # abreviaturas del cuadro de arquitecturas (y del documento final)
    etiquetas = {
        "MODEL_BASED": ("MB", 0),
        "KNOWLEDGE_BASED": ("KB", 4),
        "OPEN_LOOP": ("OL", -3),
        "BAYESIAN": ("BAY", 0),
        "CLOSED_LOOP": ("CL", -5),
    }
    for pol, (txt, dy) in etiquetas.items():
        ax.annotate(f"{txt} {fin[pol]:.1f}", (0.5, fin[pol]), xytext=(5, dy),
                    textcoords="offset points", va="center", fontsize=7.6,
                    color=TINTA, annotation_clip=False)
    ax.set_xticks([0, 0.1, 0.25, 0.5], ["0", "0.1", "0.25", "0.5"])
    ax.set_xlim(-0.015, 0.5)
    fig.subplots_adjust(left=0.2, right=0.78, bottom=0.16, top=0.97)
    ax.set_xlabel("λ")
    ax.set_ylabel("utilidad neta  (r = 3, c = 5)")
    ax.set_ylim(0, 108)
    guardar(fig, "kb-r3")


def fig_mecanismo() -> None:
    """A λ = 0.5, r = 3: el bayesiano repara más, desperdicia más y delibera más."""
    df = an.cargar("conocimiento")
    df = df[(df.radio == "3") & (df.lambda_dinamismo == 0.5)].copy()
    df["proactivas"] = df.n_ediciones - df.n_ediciones_por_fallo
    pols = ["CLOSED_LOOP", "KNOWLEDGE_BASED", "BAYESIAN"]
    cortos = {"CLOSED_LOOP": "CL", "KNOWLEDGE_BASED": "KB", "BAYESIAN": "BAY"}
    paneles = [
        ("proactivas", "reparaciones\nproactivas", "{:.1f}"),
        ("n_ediciones_desperdiciadas", "ediciones\ndesperdiciadas", "{:.1f}"),
        ("pasos_deliberando", "ticks deliberando\n(de 400)", "{:.0f}"),
        ("utilidad_neta", "utilidad neta", "{:.1f}"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(5.75, 1.95))
    for ax, (col, titulo, fmt) in zip(axes, paneles, strict=True):
        g = df.groupby("politica")[col].agg(["mean", "std", "count"]).loc[pols]
        g["err"] = g["std"] / g["count"] ** 0.5
        xs = np.arange(len(pols))
        ax.bar(xs, g["mean"], color=[COLOR[p] for p in pols], width=0.72, zorder=2)
        ax.errorbar(xs, g["mean"], yerr=g.err, fmt="none", ecolor=TINTA2, elinewidth=0.8,
                    zorder=3)
        tope = (g["mean"] + g.err).max()
        for x, v in zip(xs, g["mean"], strict=True):
            ax.text(x, v + tope * 0.06, fmt.format(v), ha="center", va="bottom",
                    fontsize=7.6, color=TINTA)
        ax.set_ylim(0, tope * 1.32)
        ax.set_xticks(xs, [cortos[p] for p in pols], fontsize=7.6)
        ax.set_title(titulo, fontsize=8.2, loc="center")
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.grid(False)
    fig.tight_layout(w_pad=0.6)
    guardar(fig, "mecanismo")


def fig_quien_gana() -> None:
    """La celda λ = 0.5, c = 5, r = 3, p = 0.9: siete políticas, una barra cada una."""
    k = an.cargar("conocimiento")
    k = k[(k.radio == "3") & (k.lambda_dinamismo == 0.5)]
    p = an.cargar("principal")
    p = p[(p.lambda_dinamismo == 0.5) & (p.costo_edicion == 5)]
    filas = []
    for pol, src in (("MODEL_BASED", k), ("REFLEX", p), ("KNOWLEDGE_BASED", k),
                     ("OPEN_LOOP", k), ("BAYESIAN", k), ("CLOSED_LOOP", k),
                     ("COLD_RESTART", p)):
        v = src[src.politica == pol].utilidad_neta
        filas.append((pol, v.mean(), v.std() / len(v) ** 0.5))
    t = pd.DataFrame(filas, columns=["pol", "m", "e"])
    fig, ax = plt.subplots(figsize=(3.3, 2.55))
    # las que deliberan en 0..4; las que no, separadas por un hueco para el rótulo
    ys = np.array([6.8, 5.8, 4, 3, 2, 1, 0])
    ax.barh(ys, t.m, color=[COLOR[q] for q in t.pol], height=0.66, zorder=2)
    ax.errorbar(t.m, ys, xerr=t.e, fmt="none", ecolor=TINTA2, elinewidth=0.8, zorder=3)
    for y, m, e in zip(ys, t.m, t.e, strict=True):
        ax.text(m + e + 2, y, f"{m:.1f}", va="center", fontsize=7.8, color=TINTA)
    ax.set_yticks(ys, t.pol, fontsize=7.6)
    ax.set_xlim(0, 118)
    ax.set_xlabel("utilidad neta  (λ = 0.5, c = 5, r = 3)")
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.axhline(4.9, color=TINTA2, lw=0.6, ls=":")
    ax.text(117, 4.98, "no deliberan ↑", ha="right", va="bottom", fontsize=7, color=TINTA2)
    ax.text(117, 4.82, "deliberan ↓", ha="right", va="top", fontsize=7, color=TINTA2)
    ax.set_ylim(-0.6, 7.4)
    fig.tight_layout()
    guardar(fig, "quien-gana")


def fig_kb_costo() -> None:
    """Respaldo (H3): KB − CL cuando cada consulta cuesta 0, 1, 2 o 5 ticks."""
    k = an.cargar("conocimiento")
    k = k[k.radio == "3"]
    kc = an.cargar("conocimiento_costo")
    cl = k[k.politica == "CLOSED_LOOP"].set_index(["lambda_dinamismo", "rng"]).utilidad_neta
    filas = []
    for lam in (0.1, 0.25, 0.5):
        for t in (0, 1, 2, 5):
            src = k if t == 0 else kc[kc.ticks_por_ask == t]
            kb = src[(src.politica == "KNOWLEDGE_BASED") & (src.lambda_dinamismo == lam)]
            kb = kb.set_index(["lambda_dinamismo", "rng"]).utilidad_neta
            d = (kb - cl.loc[kb.index]).to_numpy()
            filas.append((lam, t, d.mean(), d.std(ddof=1) / len(d) ** 0.5))
    t = pd.DataFrame(filas, columns=["lam", "t", "m", "e"])
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    ax.axhline(0, color=TINTA2, lw=0.8)
    for j, lam in enumerate((0.1, 0.25, 0.5)):
        s = t[t.lam == lam]
        ax.errorbar(s.t + (j - 1) * 0.12, s.m, yerr=s.e, color=RAMPA_C[j + 1], marker="o",
                    ms=4, lw=1.4, capsize=0, label=f"λ = {lam:g}")
    ax.set_xticks([0, 1, 2, 5])
    ax.set_xlabel("ticks por consulta ASK")
    ax.set_ylabel("KNOWLEDGE_BASED − CLOSED_LOOP (± EE)")
    ax.legend(loc="lower left", fontsize=7.5)
    fig.tight_layout()
    guardar(fig, "kb-costo")


# ------------------------------------------------------------ 6. escasez


def fig_escasez() -> None:
    """Dos regímenes, una pregunta: ¿vale más reparar cuando faltan objetivos?"""
    inf = an.cargar("escasez_inf")
    mix = an.cargar("escasez")
    K = [2, 4, 8, 16]
    fig, axes = plt.subplots(1, 2, figsize=(5.75, 2.45))

    def serie(ax: Any, df: pd.DataFrame, a: str, b: str, lam: float, color: str,
              ls: str, texto: str, dy: float = 0) -> None:
        d = an.diferencia_pareada(df[df.lambda_dinamismo == lam], a, b,
                                  por=("n_resources",)).set_index("n_resources").loc[K]
        ax.plot(K, d.media, color=color, ls=ls, marker="o", ms=4, lw=1.6, zorder=3)
        ax.fill_between(K, d.media - d.err, d.media + d.err, color=color, alpha=0.15, lw=0)
        ax.annotate(texto, (16, d.media.iloc[-1]), xytext=(6, dy), textcoords="offset points",
                    va="center", fontsize=7.4, color=TINTA)

    ax = axes[0]
    serie(ax, inf, "CLOSED_LOOP", "OPEN_LOOP", 0.5, COLOR["CLOSED_LOOP"], "-",
          "CL − OL\nλ = 0.5")
    serie(ax, inf, "CLOSED_LOOP", "OPEN_LOOP", 0.1, COLOR["CLOSED_LOOP"], "--",
          "CL − OL\nλ = 0.1")
    ax.set_title("Replanificar es gratis (r = ∞, c = 0, p = 1)", loc="left", fontsize=8.6)
    ax.set_ylim(0, 75)
    ax = axes[1]
    serie(ax, mix, "MODEL_BASED", "OPEN_LOOP", 0.5, COLOR["MODEL_BASED"], "-",
          "MB − OL\nλ = 0.5")
    serie(ax, mix, "MODEL_BASED", "CLOSED_LOOP", 0.25, COLOR["MODEL_BASED"], "--",
          "MB − CL\nλ = 0.25")
    ax.set_title("Replanificar cuesta (r = 3, c = 5, p = 0.9)", loc="left", fontsize=8.6)
    ax.axhline(0, color=TINTA2, lw=0.8)
    ax.set_ylim(-25, 118)
    for ax in axes:
        ax.set_xscale("log", base=2)
        ax.set_xticks(K, [str(k) for k in K])
        ax.minorticks_off()
        ax.set_xlim(1.8, 30)
        ax.set_xlabel("recursos simultáneos K")
    axes[0].set_ylabel("diferencia de utilidad (± EE)")
    fig.tight_layout(w_pad=1.0)
    guardar(fig, "escasez")


# ------------------------------------------------------------ 7. sensibilidad


def fig_sensibilidad() -> None:
    """η² por factor: sobre la utilidad de CLOSED_LOOP y sobre la diferencia OL − CL.

    Las dos facetas comparten filas (barrido × factor) y escala, para que se vea de un
    vistazo que lo que mueve el nivel no mueve la diferencia.
    """
    from project import sensibilidad as se

    tab = se.tabla_sensibilidad()
    tab = tab[tab.politica == "CLOSED_LOOP"]
    eta_d, _ = se.tabla_sensibilidad_delta()
    corto = {"lambda_dinamismo": "λ", "costo_edicion": "c", "competencia": "p",
             "radio": "r", "presupuesto": "B"}
    filas = []  # (barrido, factor)
    for b, factores in se.BARRIDOS.items():
        for f in factores:
            filas.append((b, f))
    ys, y = [], 0.0
    for i, (b, _) in enumerate(filas):
        if i and b != filas[i - 1][0]:
            y += 0.6
        ys.append(y)
        y += 1
    fig, axes = plt.subplots(1, 2, figsize=(5.75, 2.55), sharex=True, sharey=True)
    for ax, datos, titulo in ((axes[0], tab, "Utilidad de CLOSED_LOOP"),
                              (axes[1], eta_d, "Diferencia OPEN_LOOP − CLOSED_LOOP")):
        for yy, (b, f) in zip(ys, filas, strict=True):
            s_ = datos[(datos.barrido == b) & (datos.factor == f)]
            if s_.empty:
                if f == "lambda_dinamismo":
                    ax.text(0.01, yy + 0.5, "(sin OPEN_LOOP)", va="center", fontsize=6.8,
                            color=TINTA2)
                continue
            v = float(s_.eta2.iloc[0])
            ax.barh(yy, v, height=0.78, zorder=2,
                    color=PRIMARIO if f == "lambda_dinamismo" else "#a3a29e")
            ax.text(v + 0.012, yy, f"{v:.3f}" if v >= 0.0005 else "0", va="center",
                    fontsize=7, color=TINTA)
        ax.set_title(titulo, loc="left", fontsize=8.6)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x")
        ax.set_xlim(0, 0.72)
        ax.set_xlabel("η² (fracción de varianza explicada)")
    axes[0].set_yticks(ys, [f"{b}  {corto[f]}" for b, f in filas], fontsize=7.2)
    axes[0].invert_yaxis()
    fig.tight_layout(w_pad=1.2)
    guardar(fig, "sensibilidad")


# ------------------------------------------------------------------ 8. ABC


def fig_abc() -> None:
    """Posterior ABC del despliegue (λ*, p*) = (0.25, 0.7): λ se aprende, p no."""
    from project import calibracion as ca

    tabla = ca.cargar_referencia()
    lam, p = 0.25, 0.7
    res = ca.abc_rechazo(ca.observar(lam, p), tabla)
    post, ic = res.posterior, res.intervalos
    print("    IC ABC:", ic.round(2).to_dict())
    fig = plt.figure(figsize=(2.55, 2.4))
    g = fig.add_gridspec(2, 2, width_ratios=(4, 1), height_ratios=(1, 3.2),
                         wspace=0.06, hspace=0.08)
    ax = fig.add_subplot(g[1, 0])
    axx = fig.add_subplot(g[0, 0], sharex=ax)
    axy = fig.add_subplot(g[1, 1], sharey=ax)
    ax.scatter(tabla.lam, tabla.p, s=1.2, color="#c9c6bf", lw=0, label="previa simulada",
               rasterized=True)
    ax.scatter(post.lam, post.p, s=6, color=PRIMARIO, alpha=0.85, lw=0,
               label=f"aceptadas ({len(post)})")
    ax.scatter([lam], [p], s=90, marker="*", color=ALERTA, edgecolor="white", lw=0.5,
               zorder=5, label="verdad (λ*, p*)")
    ax.set_xlim(*ca.PRIOR["lam"])
    ax.set_ylim(*ca.PRIOR["p"])
    ax.set_xlabel("λ")
    ax.set_ylabel("p (competencia)")
    ax.grid(False)
    ax.legend(loc="lower right", fontsize=6.4, markerscale=1.2, handletextpad=0.1,
              borderaxespad=0.2, framealpha=0.85, frameon=True, edgecolor="none",
              facecolor=FONDO)
    axx.hist(post.lam, bins=20, range=ca.PRIOR["lam"], color=PRIMARIO, alpha=0.85)
    axy.hist(post.p, bins=20, range=ca.PRIOR["p"], color=PRIMARIO, alpha=0.85,
             orientation="horizontal")
    for eje, par, verdad, f in ((axx, "lam", lam, "axvline"), (axy, "p", p, "axhline")):
        getattr(eje, f)(verdad, color=ALERTA, lw=1.1)
        for q in ("q05", "q95"):
            getattr(eje, f)(ic.loc[par, q], color=TINTA, ls=":", lw=0.8)
    for eje in (axx, axy):
        eje.grid(False)
        eje.tick_params(labelbottom=False, labelleft=False, left=False, bottom=False)
        for s in eje.spines.values():
            s.set_visible(False)
    guardar(fig, "abc")


def fig_fiabilidad() -> None:
    """HB5: diagrama de fiabilidad del filtro (una sola faceta, a tamaño de columna)."""
    d = an.datos_calibracion()
    fig, ax = plt.subplots(figsize=(2.75, 2.45))
    ax.plot([0, 1], [0, 1], ls="--", color=TINTA2, lw=0.8, label="calibración perfecta")
    ax.errorbar(d.p_media, d.frecuencia, yerr=d.err, fmt="o-", ms=3.5, lw=1.4, capsize=0,
                color=COLOR["BAYESIAN"], label="filtro de rejilla")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([0, 0.5, 1])
    ax.set_yticks([0, 0.5, 1])
    ax.grid(axis="both")
    ax.set_xlabel("probabilidad asignada")
    ax.set_ylabel("frecuencia observada")
    ax.legend(loc="upper left", fontsize=7.2)
    fig.tight_layout()
    guardar(fig, "fiabilidad")


# --------------------------------------------------------- 9. respaldo


def fig_competencia() -> None:
    """Respaldo: utilidad contra p para OL y CL a λ = 0.25 y 0.5."""
    df = an.cargar("competencia")
    m = _medias(df, ["lambda_dinamismo", "competencia"])
    fig, axes = plt.subplots(1, 2, figsize=(5.4, 2.3), sharey=True)
    for ax, lam in zip(axes, (0.25, 0.5), strict=True):
        s = m[m.lambda_dinamismo == lam]
        for pol in ("OPEN_LOOP", "CLOSED_LOOP"):
            d = s[s.politica == pol].sort_values("competencia")
            _linea(ax, d.competencia, d["mean"], d.err, pol)
        ax.set_title(f"λ = {lam:g}", loc="left")
        ax.set_xlabel("p (competencia del oráculo)")
        ax.set_xticks([0.5, 0.7, 0.9, 1.0])
    axes[0].set_ylabel("utilidad neta (c = 5, r = 3)")
    axes[0].set_ylim(0, 75)
    axes[1].legend(loc="upper left", fontsize=7.5)
    fig.tight_layout(w_pad=1.0)
    guardar(fig, "competencia")


def fig_gobernanza() -> None:
    """Respaldo: utilidad contra el presupuesto B a λ = 0.25 y 0.5."""
    df = an.cargar("gobernanza")
    fig, axes = plt.subplots(1, 2, figsize=(5.4, 2.3), sharey=True)
    for ax, lam in zip(axes, (0.25, 0.5), strict=True):
        s = df[(df.lambda_dinamismo == lam)]
        gov = s[s.politica == "GOVERNED"].groupby("presupuesto").utilidad_neta.agg(
            ["mean", "std", "count"])
        gov["err"] = gov["std"] / gov["count"] ** 0.5
        cl = s[s.politica == "CLOSED_LOOP"].utilidad_neta.mean()
        xs = np.arange(len(gov))
        ax.errorbar(xs, gov["mean"], yerr=gov.err, color=COLOR["GOVERNED"], marker="P", lw=1.4,
                    ms=5, capsize=0, label="GOVERNED")
        ax.axhline(cl, color=COLOR["CLOSED_LOOP"], lw=1.4, ls="--", label="CLOSED_LOOP")
        ax.set_xticks(xs, [f"{int(b)}" + (" (≡ OL)" if b == 0 else "") for b in gov.index],
                      fontsize=7.4)
        ax.set_title(f"λ = {lam:g}", loc="left")
        ax.set_xlabel("presupuesto B de reparaciones proactivas")
    axes[0].set_ylabel("utilidad neta (c = 5, r = 3)")
    axes[0].set_ylim(0, 70)
    axes[1].legend(loc="upper right", fontsize=7.5)
    fig.tight_layout(w_pad=1.0)
    guardar(fig, "gobernanza")


# ------------------------------------------------- 10. el mundo, en imagen


def _tira(policy: str, pasos: list[int], nombre: str, *, semilla: int = 3,
          lam: float = 0.25, total: int = 80, alto: float = 1.95) -> None:
    """Instantáneas de una corrida con el mismo panel que la película del cuaderno."""
    from project import animacion as ani

    modelo, frames = ani.traza_corrida(total, policy=policy, lambda_dinamismo=lam,
                                       costo_edicion=5, radio=3, rng=semilla)
    print(f"    {policy}: {frames[-1].metricas['entregas']:.0f} entregas, "
          f"{frames[-1].metricas['n_ediciones']:.0f} ediciones, "
          f"{frames[-1].metricas['pasos_deliberando']:.0f} ticks deliberando en {total}")
    estilo()
    plt.rcParams["axes.grid"] = False
    fig = plt.figure(figsize=(alto * len(pasos), alto + 0.42))
    gs = fig.add_gridspec(1, len(pasos), wspace=0.05)
    for k, i in enumerate(pasos):
        ax = fig.add_subplot(gs[0, k])
        ani._panel_grid(ax, frames, i, modelo)
        if ax.get_legend() is not None:
            ax.get_legend().remove()
        for s in ax.spines.values():
            s.set_visible(True)
            s.set_color("#8f8c86")
            s.set_linewidth(0.6)
        ax.set_title(f"tick {frames[i].tick}", fontsize=8.5, color=PRIMARIO, weight="bold")
    h, lab = fig.axes[0].get_legend_handles_labels()
    fig.legend(h, lab, ncol=len(lab), loc="lower center", bbox_to_anchor=(0.5, -0.02),
               fontsize=7.2, handletextpad=0.3, columnspacing=1.0, markerscale=0.7)
    fig.subplots_adjust(left=0.005, right=0.995, top=0.9, bottom=0.12)
    guardar(fig, nombre)


def fig_tiras() -> None:
    """La región posible en tres momentos (tick 12, 20 y 64), como en el documento final."""
    _tira("KNOWLEDGE_BASED", [12, 20, 64], "tira-kb")


def fig_mundo() -> None:
    """Una instantánea de CLOSED_LOOP con una divergencia visible: el modelo en un cuadro."""
    from project import animacion as ani

    modelo, frames = ani.traza_corrida(80, policy="CLOSED_LOOP", lambda_dinamismo=0.25,
                                       costo_edicion=5, radio=3, rng=3)
    # el primer tick con flecha creencia → realidad sobre el objetivo y plan en curso
    elegido = 20
    for f in frames[8:]:
        if f.objetivo is None or not f.ruta:
            continue
        cre, real = f.creencias.get(f.objetivo), f.recursos.get(f.objetivo)
        if cre is not None and real is not None and cre != real and len(f.ruta) >= 4:
            elegido = f.tick
            break
    print(f"    mundo: tick {elegido}")
    estilo()
    plt.rcParams["axes.grid"] = False
    fig, ax = plt.subplots(figsize=(2.75, 2.95))
    ani._panel_grid(ax, frames, elegido, modelo)
    if ax.get_legend() is not None:
        ax.get_legend().remove()
    ax.set_title("")
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color("#8f8c86")
        s.set_linewidth(0.6)
    from matplotlib.patches import Patch

    h, lab = ax.get_legend_handles_labels()
    h.append(Patch(facecolor="#9ecae1", alpha=0.5, lw=0))
    lab.append("visión (r = 3)")
    fig.legend(h, lab, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.01),
               fontsize=6.8, handletextpad=0.3, columnspacing=0.8, markerscale=0.7)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.15)
    guardar(fig, "mundo")


# ------------------------------------------------------- 11. la portada


def _retícula(ancho: int, alto: int, semilla: int) -> tuple[np.ndarray, np.random.Generator]:
    rng = np.random.default_rng(semilla)
    obst = rng.random((alto, ancho)) < 0.15
    return obst, rng


def _vecinas(obst: np.ndarray, y: int, x: int) -> list[tuple[int, int]]:
    alto, ancho = obst.shape
    out = []
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        yy, xx = y + dy, x + dx
        if 0 <= yy < alto and 0 <= xx < ancho and not obst[yy, xx]:
            out.append((yy, xx))
    return out


def _difundir(obst: np.ndarray, origen: tuple[int, int], lam: float, pasos: int) -> np.ndarray:
    """La predicción del filtro (caminata aleatoria con prob. λ), sin observaciones."""
    alto, ancho = obst.shape
    P = np.zeros((alto, ancho))
    P[origen] = 1.0
    grado = np.zeros((alto, ancho))
    for y in range(alto):
        for x in range(ancho):
            if not obst[y, x]:
                grado[y, x] = len(_vecinas(obst, y, x))
    for _ in range(pasos):
        Q = np.where(grado > 0, (1 - lam) * P, P)
        for y in range(alto):
            for x in range(ancho):
                if P[y, x] > 0 and grado[y, x] > 0:
                    for yy, xx in _vecinas(obst, y, x):
                        Q[yy, xx] += lam * P[y, x] / grado[y, x]
        P = Q
    return P


def _bfs(obst: np.ndarray, a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    from collections import deque

    prev = {a: None}
    cola = deque([a])
    while cola:
        u = cola.popleft()
        if u == b:
            break
        for v in _vecinas(obst, *u):
            if v not in prev:
                prev[v] = u
                cola.append(v)
    if b not in prev:
        return [a]
    camino = [b]
    while prev[camino[-1]] is not None:
        camino.append(prev[camino[-1]])
    return camino[::-1]


def fig_portada() -> None:
    """Portada: el mundo del modelo, estilizado, en el azul del tema.

    Una retícula 32 × 18 (16:9) con obstáculos, el mapa de probabilidad del filtro
    bayesiano alrededor de tres creencias viejas, la región posible del agente lógico
    como contorno, el disco de visión, la ruta planificada y la deriva de un recurso. Se
    dibuja oscura y de bajo contraste porque va bajo el velo y el título claro.
    """
    from matplotlib.colors import LinearSegmentedColormap

    ancho, alto = 32, 18
    obst, rng = _retícula(ancho, alto, 11)
    base = (2, 3)
    agente = (6, 12)
    creencias = [(12, 20), (5, 25), (14, 7)]
    reales = [(13, 22), (4, 27), (15, 9)]
    for c in [base, agente, *creencias, *reales]:
        obst[c] = False
        for v in ((c[0] + 1, c[1]), (c[0], c[1] + 1)):
            if v[0] < alto and v[1] < ancho:
                obst[v] = False
    masa = np.zeros((alto, ancho))
    for c, k in zip(creencias, (9, 12, 7), strict=True):
        P = _difundir(obst, c, 0.35, k)
        masa = np.maximum(masa, P / P.max())

    plt.rcdefaults()
    fig = plt.figure(figsize=(6.4, 3.6))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(-0.5, ancho - 0.5)
    ax.set_ylim(-0.5, alto - 0.5)
    ax.set_aspect("auto")
    ax.axis("off")
    # fondo: degradado del azul profundo del tema a casi negro
    yy, xx = np.mgrid[0:1:200j, 0:1:356j]
    grad = 0.55 * xx + 0.45 * (1 - yy)
    fondo = LinearSegmentedColormap.from_list("f", ["#00203a", "#003557", "#06476b"])
    ax.imshow(grad, extent=(-0.5, ancho - 0.5, -0.5, alto - 0.5), cmap=fondo, origin="lower",
              aspect="auto", zorder=0)
    # probabilidad: un brillo cálido, suavizado (bicúbico) y luego celda a celda
    calor = LinearSegmentedColormap.from_list(
        "c", [(0.86, 0.40, 0.13, 0.0), (0.86, 0.40, 0.13, 0.35), (0.98, 0.72, 0.40, 0.85)])
    ax.imshow(np.sqrt(masa), extent=(-0.5, ancho - 0.5, -0.5, alto - 0.5), cmap=calor,
              origin="lower", interpolation="bicubic", aspect="auto", zorder=1, vmin=0,
              vmax=1)
    # retícula
    for x in range(ancho + 1):
        ax.axvline(x - 0.5, color="white", alpha=0.06, lw=0.4, zorder=2)
    for y in range(alto + 1):
        ax.axhline(y - 0.5, color="white", alpha=0.06, lw=0.4, zorder=2)
    # obstáculos
    from matplotlib.patches import Rectangle

    for y, x in zip(*np.nonzero(obst), strict=True):
        ax.add_patch(Rectangle((x - 0.42, y - 0.42), 0.84, 0.84, color="#5f88a6", alpha=0.32,
                               lw=0, zorder=3))
    # región posible (KB) de la creencia más vieja: contorno punteado celeste
    region = _difundir(obst, creencias[1], 0.35, 12) > 1e-4
    for y, x in zip(*np.nonzero(region), strict=True):
        for dy, dx, seg in ((1, 0, ((x - 0.5, y + 0.5), (x + 0.5, y + 0.5))),
                            (-1, 0, ((x - 0.5, y - 0.5), (x + 0.5, y - 0.5))),
                            (0, 1, ((x + 0.5, y - 0.5), (x + 0.5, y + 0.5))),
                            (0, -1, ((x - 0.5, y - 0.5), (x - 0.5, y + 0.5)))):
            yy2, xx2 = y + dy, x + dx
            dentro = 0 <= yy2 < alto and 0 <= xx2 < ancho and region[yy2, xx2]
            if not dentro:
                (x0, y0), (x1, y1) = seg
                ax.plot([x0, x1], [y0, y1], color=ACENTO, lw=0.9, alpha=0.55, zorder=4,
                        solid_capstyle="butt")
    # disco de visión (Manhattan, r = 3)
    for y in range(alto):
        for x in range(ancho):
            if abs(y - agente[0]) + abs(x - agente[1]) <= 3:
                ax.add_patch(Rectangle((x - 0.5, y - 0.5), 1, 1, color=ACENTO, alpha=0.10,
                                       lw=0, zorder=2))
    # ruta planificada: agente → creencia → base
    ruta = _bfs(obst, agente, creencias[0]) + _bfs(obst, creencias[0], base)[1:]
    ys, xs = zip(*ruta, strict=True)
    ax.plot(xs, ys, color=ACENTO, lw=1.3, ls=(0, (1.2, 1.6)), alpha=0.95, zorder=5,
            dash_capstyle="round")
    # recursos reales, creencias obsoletas y la deriva entre ambos
    for (cy, cx), (ry, rx) in zip(creencias, reales, strict=True):
        ax.scatter([cx], [cy], s=26, marker="D", facecolor="none", edgecolor="#f2c79a",
                   lw=0.8, alpha=0.9, zorder=6)
        ax.annotate("", xy=(rx, ry), xytext=(cx, cy), zorder=6,
                    arrowprops={"arrowstyle": "-|>", "color": ALERTA, "lw": 0.9,
                                "alpha": 0.9, "mutation_scale": 6})
        ax.scatter([rx], [ry], s=34, color="#f59a3c", lw=0, zorder=7)
    otros = [(9, 4), (1, 15), (16, 17), (10, 29), (2, 22)]
    for y, x in otros:
        if not obst[y, x]:
            ax.scatter([x], [y], s=26, color="#f59a3c", alpha=0.75, lw=0, zorder=7)
    ax.add_patch(Rectangle((base[1] - 0.45, base[0] - 0.45), 0.9, 0.9, color="#4DB896",
                           alpha=0.9, lw=0, zorder=7))
    ax.scatter([agente[1]], [agente[0]], s=70, color="#e9f6fa", lw=0, zorder=8)
    ax.scatter([agente[1]], [agente[0]], s=190, facecolor="none", edgecolor=ACENTO, lw=0.8,
               alpha=0.7, zorder=8)
    SALIDA.mkdir(exist_ok=True)
    fig.savefig(SALIDA / "portada.png", dpi=400, transparent=False, facecolor=PRIMARIO)
    plt.close(fig)
    print("  figuras/portada.png")


def fig_marca() -> None:
    """Marca de agua: la misma retícula de la portada, clara y sin ruta ni agente.

    tema/portada.sty la pone al 6,7 % bajo cada diapositiva. La portada oscura a ese
    alfa tiñe el fondo y deja ver la ruta detrás de las figuras; esta versión es papel
    claro con la textura de la retícula (obstáculos y líneas) y apenas el calor del
    filtro, de modo que se lee como textura y no compite con los datos.
    """
    from matplotlib.patches import Rectangle

    ancho, alto = 32, 18
    obst, _ = _retícula(ancho, alto, 11)
    plt.rcdefaults()
    fig = plt.figure(figsize=(6.4, 3.6))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(-0.5, ancho - 0.5)
    ax.set_ylim(-0.5, alto - 0.5)
    ax.axis("off")
    for x in range(ancho + 1):
        ax.axvline(x - 0.5, color=PRIMARIO, alpha=0.18, lw=0.5)
    for y in range(alto + 1):
        ax.axhline(y - 0.5, color=PRIMARIO, alpha=0.18, lw=0.5)
    for y, x in zip(*np.nonzero(obst), strict=True):
        ax.add_patch(Rectangle((x - 0.42, y - 0.42), 0.84, 0.84, color=PRIMARIO, alpha=0.55,
                               lw=0))
    fig.savefig(SALIDA / "marca.png", dpi=200, facecolor="white")
    plt.close(fig)
    print("  figuras/marca.png")


# ---------------------------------------------------------------------- main

FIGURAS = {
    "portada": fig_portada,
    "marca": fig_marca,
    "mundo": fig_mundo,
    "frontera": fig_frontera,
    "frontera-completa": fig_frontera_completa,
    "abierto-cerrado": fig_abierto_cerrado,
    "caliente-frio": fig_caliente_frio,
    "dinamica": fig_dinamica,
    "kb-r3": fig_kb_r3,
    "mecanismo": fig_mecanismo,
    "quien-gana": fig_quien_gana,
    "kb-costo": fig_kb_costo,
    "escasez": fig_escasez,
    "sensibilidad": fig_sensibilidad,
    "abc": fig_abc,
    "fiabilidad": fig_fiabilidad,
    "competencia": fig_competencia,
    "gobernanza": fig_gobernanza,
    "tiras": fig_tiras,
}


def main(nombres: list[str]) -> None:
    pedidas = nombres or list(FIGURAS)
    desconocidas = [n for n in pedidas if n not in FIGURAS]
    if desconocidas:
        sys.exit(f"figuras desconocidas: {desconocidas}; opciones: {list(FIGURAS)}")
    for n in pedidas:
        estilo()
        FIGURAS[n]()


if __name__ == "__main__":
    main(sys.argv[1:])
