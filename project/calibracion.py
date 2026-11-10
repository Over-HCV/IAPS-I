"""Calibración de (λ, p) por ABC de rechazo (paquete C5-A de ``docs/roadmap-c5.md``).

El guion asigna al sistema propio el papel de aportar «λ y p de producción». Este módulo lo
vuelve un procedimiento, el mismo de C5 §12 (ABC por rechazo) llevado a dos parámetros:

1. un **despliegue** corre ``OPEN_LOOP`` —el modo en frío, sin monitoreo, que es lo que
   ejecuta un motor sin reparación en caliente— con (λ*, p*) ocultos, y su telemetría
   produce los estadísticos observados (:func:`estadisticos`, :func:`observar`);
2. se muestrea (λ, p) del prior uniforme, se simula cada muestra y se guarda la *tabla de
   referencia* en ``results/abc.parquet`` (:func:`tabla_referencia`);
3. se aceptan las muestras cuyos estadísticos, estandarizados, quedan más cerca de los
   observados (:func:`abc_rechazo`): aproximan la posterior P(λ, p | telemetría);
4. bajo esa posterior se lee qué política recomienda la frontera ya barrida
   (:func:`recomendar`).

Uso, desde la raíz del repositorio::

    uv run python -m project.calibracion --referencia --procesos 0
    uv run python -m project.calibracion --demo
    uv run python -m project.calibracion --demo --verdad 0.1 0.9
    uv run python -m project.calibracion --figura
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import os
from pathlib import Path
import time
from typing import Any, NamedTuple

from project.agents import Policy
from project.analysis import FIGURAS, cargar, guardar
from project.experiments import BASE
from project.model import REPORTERS, OASysWorld
import numpy as np
import pandas as pd

RESULTS = Path(__file__).parent / "results"
RUTA_REFERENCIA = RESULTS / "abc.parquet"

DESPLIEGUE: dict[str, Any] = {
    **BASE,
    "policy": str(Policy.OPEN_LOOP),
    "costo_edicion": 5,
    "radio": 3,
}
"""Configuración fija del despliegue; solo (λ, p) quedan ocultos.

``c=5`` y ``r=3`` son los valores de los barridos ``competencia`` y de la faceta central
de ``principal``, de modo que la recomendación de :func:`recomendar` se lee en la misma
rebanada de la frontera en que se calibró.
"""

PRIOR: dict[str, tuple[float, float]] = {"lam": (0.0, 0.8), "p": (0.5, 1.0)}
"""Prior uniforme e independiente: λ ∈ [0, 0.8] y p ∈ [0.5, 1] (el rango de ``competencia``).

λ se extiende más allá del 0,5 de los barridos a propósito. Con el prior cortado en 0,5,
un despliegue con λ* = 0,5 queda en el borde: la posterior solo puede repartirse hacia
abajo y su mediana sale sesgada (0,39 en la primera versión). El precio es que para
λ > 0,5 :func:`recomendar` extrapola desde la última columna de la rejilla (λ = 0,5), y
que el prior es 1,6 veces más ancho: la tabla pasa de 2.000 a 3.000 muestras para que la
densidad de muestras cerca de la verdad, y con ella el 5 % aceptado, no se enrarezca.
"""

ESTADISTICOS = [
    "entregas",
    "tareas_fallidas",
    "n_ediciones_por_fallo",
    "divergencias_reales",
    "pasos_deliberando",
]
"""Lo que registra la telemetría de un motor en frío, cada uno dividido por ``max_steps``.

Son tasas por tick: así un despliegue observado durante otro horizonte sigue siendo
comparable con la tabla. Con ``OPEN_LOOP`` toda edición es forzada por un fallo, así que
``n_ediciones_por_fallo`` es la tasa de replanificaciones forzadas.
"""

SEMILLAS_OBSERVADO = [1000, 1001, 1002, 1003, 1004]
"""Cinco semillas del despliegue «real». Quedan fuera del rango de :data:`SEMILLAS` de
``experiments`` para que el despliegue no sea ninguna de las corridas de los barridos."""

SEMILLAS_POR_MUESTRA = 2
"""Réplicas por muestra del prior en la tabla de referencia.

El observado promedia 5 semillas y cada muestra solo 2: la tabla es más ruidosa que el
dato, lo que ensancha la posterior (el núcleo de aceptación efectivo es más ancho) pero
no la sesga. Se eligió así para que la tabla de 3.000 muestras sea barata (~8 s con 12
núcleos, ~10 ms por corrida de 400 ticks); con 5 réplicas costaría 2,5 veces más para
afinar poco, porque el 5 % aceptado ya promedia ~300 mundos.
"""

TRUTHS_DEMO = [(0.1, 0.9), (0.25, 0.7), (0.5, 0.9)]
"""Los (λ*, p*) ocultos de las demostraciones del roadmap."""


class ResultadoABC(NamedTuple):
    """Salida de :func:`abc_rechazo`."""

    posterior: pd.DataFrame
    """Muestras aceptadas: ``lam``, ``p``, los estadísticos y ``distancia``."""

    intervalos: pd.DataFrame
    """Cuantiles 5 %, 50 % y 95 % por parámetro (índice ``lam``, ``p``)."""


# ----------------------------------------------------------------- simulación


def estadisticos(fuente: OASysWorld | pd.Series | dict[str, Any]) -> np.ndarray:
    """Vector de estadísticos resumen de una corrida, en tasas por tick.

    Args:
        fuente: un modelo ya corrido, o una fila de ``batch_run`` / de un CSV de
            ``results`` (con las columnas de los reporters y ``max_steps``).
    """
    if isinstance(fuente, OASysWorld):
        crudos = [REPORTERS[e](fuente) for e in ESTADISTICOS]
        max_steps = fuente.max_steps
    else:
        crudos = [fuente[e] for e in ESTADISTICOS]
        max_steps = fuente["max_steps"]
    return np.array([float(v) / max_steps for v in crudos])


def _una_corrida(lam: float, p: float, semilla: int) -> np.ndarray:
    """Correr un despliegue completo y devolver sus estadísticos."""
    modelo = OASysWorld(
        **DESPLIEGUE, lambda_dinamismo=lam, competencia=p, rng=int(semilla)
    )
    while modelo.running:
        modelo.step()
    return estadisticos(modelo)


def simular(lam: float, p: float, semillas: list[int] | tuple[int, ...]) -> np.ndarray:
    """Estadísticos medios de un despliegue ``OPEN_LOOP`` con (λ, p) sobre ``semillas``."""
    return np.mean([_una_corrida(lam, p, s) for s in semillas], axis=0)


def _simular_tarea(tarea: tuple[float, float, tuple[int, ...]]) -> np.ndarray:
    """Envoltura de :func:`simular` con un solo argumento, para ``ProcessPoolExecutor``."""
    return simular(*tarea)


def observar(
    lam: float, p: float, semillas: list[int] | None = None
) -> np.ndarray:
    """Telemetría de un despliegue con (λ*, p*) ocultos: media sobre 5 semillas."""
    return simular(lam, p, SEMILLAS_OBSERVADO if semillas is None else semillas)


def tabla_referencia(
    n: int = 3000,
    rng: int = 0,
    *,
    semillas_por_muestra: int = SEMILLAS_POR_MUESTRA,
    procesos: int | None = None,
    ruta: Path | None = RUTA_REFERENCIA,
) -> pd.DataFrame:
    """Muestrear el prior, simular cada muestra y guardar la tabla de referencia.

    Cada muestra lleva sus propias semillas, sorteadas con el mismo generador: así la
    tabla integra también la variabilidad del mundo (obstáculos, recursos), que el
    despliegue observado no controla.

    Args:
        n: muestras del prior.
        rng: semilla del muestreo (prior y semillas de las corridas).
        semillas_por_muestra: réplicas por muestra (ver :data:`SEMILLAS_POR_MUESTRA`).
        procesos: procesos en paralelo; ``None`` = todos los núcleos.
        ruta: dónde guardar el parquet; ``None`` para no guardar.

    Returns:
        Una fila por muestra: ``lam``, ``p`` y :data:`ESTADISTICOS`.
    """
    gen = np.random.default_rng(rng)
    lam = gen.uniform(*PRIOR["lam"], size=n)
    p = gen.uniform(*PRIOR["p"], size=n)
    semillas = gen.integers(0, 2**31 - 1, size=(n, semillas_por_muestra))
    tareas = [
        (float(lam[i]), float(p[i]), tuple(int(s) for s in semillas[i]))
        for i in range(n)
    ]
    procesos = procesos or os.cpu_count() or 1
    if procesos == 1:
        filas = [_simular_tarea(t) for t in tareas]
    else:
        with ProcessPoolExecutor(max_workers=procesos) as pool:
            filas = list(
                pool.map(_simular_tarea, tareas, chunksize=max(1, n // (8 * procesos)))
            )
    tabla = pd.DataFrame(np.vstack(filas), columns=ESTADISTICOS)
    tabla.insert(0, "p", p)
    tabla.insert(0, "lam", lam)
    if ruta is not None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        tabla.to_parquet(ruta, index=False)
    return tabla


def cargar_referencia() -> pd.DataFrame:
    """Leer ``results/abc.parquet``.

    Raises:
        FileNotFoundError: con el comando exacto que genera el archivo, igual que
            :func:`project.analysis.cargar`.
    """
    if not RUTA_REFERENCIA.exists():
        raise FileNotFoundError(
            f"no existe {RUTA_REFERENCIA}. Generarlo con:\n"
            f"    uv run python -m project.calibracion --referencia --procesos 0"
        )
    return pd.read_parquet(RUTA_REFERENCIA)


# ------------------------------------------------------------------- inferencia


def _escala(columna: pd.Series) -> float:
    """Desviación típica de un estadístico en la tabla, con la MAD de respaldo.

    Si un estadístico no varía en la tabla (desviación nula) la división explotaría; la
    MAD escalada (·1,4826, consistente con la desviación bajo normalidad) es el respaldo,
    y si también es nula el estadístico no discrimina y se deja con escala 1.
    """
    sd = float(columna.std())
    if np.isfinite(sd) and sd > 0:
        return sd
    mad = 1.4826 * float((columna - columna.median()).abs().median())
    return mad if mad > 0 else 1.0


def intervalos_creibles(
    posterior: pd.DataFrame, cuantiles: tuple[float, ...] = (0.05, 0.5, 0.95)
) -> pd.DataFrame:
    """Cuantiles de la posterior de λ y p; con los de serie es el intervalo del 90 %."""
    tabla = posterior[["lam", "p"]].quantile(list(cuantiles)).T
    tabla.columns = [f"q{round(100 * q):02d}" for q in cuantiles]
    return tabla


def abc_rechazo(
    observado: np.ndarray | pd.Series,
    tabla: pd.DataFrame,
    frac: float = 0.05,
) -> ResultadoABC:
    """ABC por rechazo: aceptar la fracción ``frac`` de muestras más cercana al dato.

    Cada estadístico se divide por su escala en la tabla (:func:`_escala`) antes de
    medir la distancia euclídea. Sin ese paso mandaría el estadístico de mayor rango
    —``pasos_deliberando`` vale ``c`` veces ``n_ediciones_por_fallo``— y los demás no
    pesarían. Aceptar un cuantil de distancia, en vez de fijar un umbral ε, deja el
    tamaño de la posterior en ``frac · len(tabla)`` sin tener que afinar ε.

    Args:
        observado: estadísticos observados, en el orden de :data:`ESTADISTICOS`.
        tabla: tabla de referencia (``lam``, ``p`` y los estadísticos).
        frac: fracción aceptada.
    """
    stats = tabla[ESTADISTICOS]
    escala = np.array([_escala(stats[c]) for c in ESTADISTICOS])
    z = (stats.to_numpy() - np.asarray(observado, dtype=float)) / escala
    distancia = np.sqrt((z**2).sum(axis=1))
    k = max(1, int(round(frac * len(tabla))))
    elegidas = np.argsort(distancia, kind="stable")[:k]
    posterior = tabla.iloc[elegidas].copy()
    posterior["distancia"] = distancia[elegidas]
    posterior = posterior.reset_index(drop=True)
    return ResultadoABC(posterior, intervalos_creibles(posterior))


# --------------------------------------------------------------- recomendación


def _mejor_politica(df: pd.DataFrame, claves: list[str]) -> pd.DataFrame:
    """Política de mayor utilidad neta media en cada celda de ``claves``."""
    medias = df.groupby([*claves, "politica"])["utilidad_neta"].mean().reset_index()
    idx = medias.groupby(claves)["utilidad_neta"].idxmax()
    return medias.loc[idx, [*claves, "politica"]].reset_index(drop=True)


def _mas_cercano(valores: np.ndarray, rejilla: np.ndarray) -> np.ndarray:
    """El punto de ``rejilla`` más cercano a cada valor."""
    rejilla = np.sort(rejilla)
    return rejilla[np.abs(valores[:, None] - rejilla[None, :]).argmin(axis=1)]


def recomendar(
    posterior: pd.DataFrame,
    principal: pd.DataFrame | None = None,
    competencia: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Distribución de la política recomendada bajo la posterior.

    Es una lectura de la frontera ya barrida, no una simulación nueva. Para cada muestra
    aceptada (λ, p) se toma el punto más cercano de la rejilla de cada barrido y la
    política de mayor ``utilidad_neta`` media en él; la fracción de muestras que cae en
    cada política es su probabilidad posterior de ser la mejor. Tres lecturas:

    - ``principal`` (c=5, r=3, p=0,9 fijo): elige entre **las seis** políticas, incluidas
      ``REFLEX`` y ``MODEL_BASED``, que no planifican. Solo usa λ, así que responde «qué
      conviene con este dinamismo si el oráculo fuera el del barrido»;
    - ``competencia`` (c=5, r=3): elige solo entre **las cuatro con plan**
      (``Policy.planifica``), pero usa λ **y** p, así que es la que incorpora la
      incertidumbre sobre la competencia del oráculo;
    - ``combinada``: la decisión en dos etapas. «¿Planificar o no?» se lee de
      ``principal`` (el único barrido que compara contra las políticas sin plan); si la
      ganadora planifica, «¿cuál de las que planifican?» —en la práctica, abierto o
      cerrado— se lee de ``competencia`` en (λ, p). Si no, la recomendación es la
      ganadora sin plan de ``principal``.

    Para λ fuera de la rejilla (λ > 0,5, ver :data:`PRIOR`) se usa el punto más cercano,
    es decir, se extrapola desde λ = 0,5.

    Args:
        posterior: muestras aceptadas, con ``lam`` y ``p``.
        principal, competencia: los barridos; por defecto se leen de ``results``.

    Returns:
        Formato largo: ``fuente`` (``"principal (λ)"``, ``"competencia (λ, p)"``,
        ``"combinada"``), ``politica``, ``fraccion`` (suma 1 por fuente).
    """
    principal = cargar("principal") if principal is None else principal
    competencia = cargar("competencia") if competencia is None else competencia
    lam = posterior["lam"].to_numpy()
    p = posterior["p"].to_numpy()

    def rebanada(df: pd.DataFrame) -> pd.DataFrame:
        # `cargar` convierte `radio` en texto; se compara como texto para servir a ambos.
        return df[(df["costo_edicion"] == 5) & (df["radio"].astype(str) == "3")]

    pr = rebanada(principal)
    mejor = _mejor_politica(pr, ["lambda_dinamismo"]).set_index("lambda_dinamismo")
    lam_g = _mas_cercano(lam, mejor.index.to_numpy())
    por_principal = mejor.loc[lam_g, "politica"].to_numpy()

    co = rebanada(competencia)
    mejor = _mejor_politica(co, ["lambda_dinamismo", "competencia"])
    mejor = mejor.set_index(["lambda_dinamismo", "competencia"])["politica"]
    lam_g = _mas_cercano(lam, co["lambda_dinamismo"].unique())
    p_g = _mas_cercano(p, co["competencia"].unique())
    por_competencia = mejor.loc[list(zip(lam_g, p_g, strict=True))].to_numpy()

    planifica = np.array([Policy(pol).planifica for pol in por_principal])
    combinada = np.where(planifica, por_competencia, por_principal)

    salidas = [
        ("principal (λ)", por_principal),
        ("competencia (λ, p)", por_competencia),
        ("combinada", combinada),
    ]

    filas = []
    for fuente, politicas in salidas:
        frac = pd.Series(politicas).value_counts(normalize=True)
        filas += [
            {"fuente": fuente, "politica": pol, "fraccion": float(f)}
            for pol, f in frac.items()
        ]
    return pd.DataFrame(filas)


# ----------------------------------------------------------------------- demo


def demo(
    lam: float = 0.25,
    p: float = 0.7,
    tabla: pd.DataFrame | None = None,
    frac: float = 0.05,
) -> tuple[ResultadoABC, pd.DataFrame]:
    """Calibrar un despliegue con (λ*, p*) conocidos y leer la recomendación."""
    tabla = cargar_referencia() if tabla is None else tabla
    resultado = abc_rechazo(observar(lam, p), tabla, frac=frac)
    return resultado, recomendar(resultado.posterior)


def fig_abc(
    lam: float = 0.25,
    p: float = 0.7,
    resultado: ResultadoABC | None = None,
    tabla: pd.DataFrame | None = None,
) -> Any:
    """Posterior conjunta de (λ, p) con sus marginales y el valor verdadero marcado.

    En gris, la tabla de referencia entera (el prior simulado); en color, las muestras
    aceptadas. Si la hipótesis del roadmap se cumple, la nube aceptada es una franja
    angosta en λ y alargada en p.
    """
    import matplotlib.pyplot as plt

    tabla = cargar_referencia() if tabla is None else tabla
    if resultado is None:
        resultado = abc_rechazo(observar(lam, p), tabla)
    post, ic = resultado.posterior, resultado.intervalos

    fig = plt.figure(figsize=(7, 7))
    rejilla = fig.add_gridspec(
        2, 2, width_ratios=(4, 1), height_ratios=(1, 4), wspace=0.05, hspace=0.05
    )
    ax = fig.add_subplot(rejilla[1, 0])
    ax_x = fig.add_subplot(rejilla[0, 0], sharex=ax)
    ax_y = fig.add_subplot(rejilla[1, 1], sharey=ax)

    ax.scatter(tabla["lam"], tabla["p"], s=4, color="0.8", label="prior simulado")
    ax.scatter(post["lam"], post["p"], s=14, color="tab:blue", alpha=0.7, label="aceptadas")
    ax.scatter([lam], [p], s=180, marker="*", color="tab:red", zorder=5, label="(λ*, p*)")
    ax.set_xlim(*PRIOR["lam"])
    ax.set_ylim(*PRIOR["p"])
    ax.set_xlabel("λ (dinamismo)")
    ax.set_ylabel("p (competencia)")
    ax.legend(fontsize=8, loc="lower right", markerscale=1.5, framealpha=0.9)

    bins = 20
    ax_x.hist(post["lam"], bins=bins, range=PRIOR["lam"], color="tab:blue", alpha=0.7)
    ax_y.hist(
        post["p"], bins=bins, range=PRIOR["p"], color="tab:blue", alpha=0.7,
        orientation="horizontal",
    )
    for eje, par, verdad, linea in ((ax_x, "lam", lam, "axvline"), (ax_y, "p", p, "axhline")):
        getattr(eje, linea)(verdad, color="tab:red", ls="--")
        for q in ("q05", "q95"):
            getattr(eje, linea)(ic.loc[par, q], color="k", ls=":", lw=1)
    # Las marginales solo muestran forma: sus conteos no aportan y chocan con los ejes.
    ax_x.tick_params(labelbottom=False, labelleft=False, left=False)
    ax_y.tick_params(labelleft=False, labelbottom=False, bottom=False)
    ax_x.set_title(
        f"ABC por rechazo ({len(post)} de {len(tabla)}): "
        f"IC90 λ [{ic.loc['lam', 'q05']:.2f}, {ic.loc['lam', 'q95']:.2f}], "
        f"p [{ic.loc['p', 'q05']:.2f}, {ic.loc['p', 'q95']:.2f}]",
        fontsize=9,
    )
    return fig


def _informe(lam: float, p: float, tabla: pd.DataFrame) -> None:
    """Imprimir intervalos y recomendación de una demostración."""
    resultado, rec = demo(lam, p, tabla)
    print(f"\n=== (λ*, p*) = ({lam}, {p}) ===")
    print(resultado.intervalos.round(3).to_string())
    print(rec.round(3).to_string(index=False))


def main() -> None:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--referencia", action="store_true", help="tabla -> abc.parquet")
    parser.add_argument("--demo", action="store_true", help="calibrar un despliegue")
    parser.add_argument("--figura", action="store_true", help="figura 10-abc.png")
    parser.add_argument(
        "--verdad", nargs=2, type=float, metavar=("LAM", "P"), default=(0.25, 0.7),
        help="(λ*, p*) ocultos de --demo y --figura",
    )
    parser.add_argument("--todas", action="store_true", help="--demo con TRUTHS_DEMO")
    parser.add_argument("--n", type=int, default=3000, help="muestras del prior")
    parser.add_argument(
        "--procesos", type=int, default=0, help="procesos en paralelo; 0 = todos"
    )
    args = parser.parse_args()
    if not (args.referencia or args.demo or args.figura):
        parser.error("elegir al menos una de --referencia, --demo, --figura")

    if args.referencia:
        t0 = time.perf_counter()
        tabla = tabla_referencia(args.n, procesos=args.procesos or None)
        print(f"{len(tabla)} muestras en {time.perf_counter() - t0:.1f} s -> {RUTA_REFERENCIA}")
    tabla = cargar_referencia()
    lam, p = args.verdad
    if args.demo:
        for verdad in TRUTHS_DEMO if args.todas else [(lam, p)]:
            _informe(*verdad, tabla)
    if args.figura:
        destino = guardar(fig_abc(lam, p, tabla=tabla), FIGURAS / "10-abc.png")
        print(destino)


if __name__ == "__main__":
    main()
