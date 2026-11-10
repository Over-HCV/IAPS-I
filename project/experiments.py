"""Barridos de parámetros con ``batch_run``.

El plan experimental está en ``info/02-design.md`` §5. El barrido completo es grande (trece
barridos, 16.260 corridas), así que se ejecuta por etapas: cada una aísla una pregunta y se
guarda por separado en ``results/<nombre>.csv``; las series por tick van aparte, en
``results/dinamica.parquet``.

Uso, desde la raíz del repositorio::

    uv run python -m project.experiments --smoke
    uv run python -m project.experiments --sweep principal
    uv run python -m project.experiments --full
    uv run python -m project.experiments --dinamica
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from mesa.batchrunner import batch_run
from project.agents import Policy
from project.model import OASysWorld
import pandas as pd

RESULTS = Path(__file__).parent / "results"

ORIGINALES: list[Policy] = [
    Policy.REFLEX,
    Policy.MODEL_BASED,
    Policy.OPEN_LOOP,
    Policy.COLD_RESTART,
    Policy.CLOSED_LOOP,
    Policy.GOVERNED,
]
"""Las seis políticas de los barridos originales.

Se fijan a mano y no se derivan del enum: ``KNOWLEDGE_BASED`` y ``BAYESIAN`` viven en
barridos propios (``conocimiento*``), y derivar estas listas de ``Policy`` cambiaría en
silencio la definición de ``principal``, ``competencia``, ``observabilidad`` y la dinámica,
cuyos resultados ya están guardados y no se vuelven a correr.
"""

TODAS = [str(p) for p in ORIGINALES]
CON_PLAN = [str(p) for p in ORIGINALES if p.planifica]

POLITICAS_CONOCIMIENTO = [
    str(Policy.MODEL_BASED),
    str(Policy.OPEN_LOOP),
    str(Policy.CLOSED_LOOP),
    str(Policy.KNOWLEDGE_BASED),
    str(Policy.BAYESIAN),
]
"""KB-2 y C5-B: las dos políticas que infieren y sus tres varas de medir.

``MODEL_BASED`` entra porque es la vara de H1b y HB4 (actúa sobre creencias sin pagar
deliberación) y ``observabilidad`` no la barre en radio."""

QUE_INFIEREN = [str(p) for p in Policy if p.infiere]

SEMILLAS = list(range(30))
"""Semillas de las réplicas.

Van por el argumento ``rng`` de ``batch_run``, **no** dentro de ``parameters``. Es un
detalle que cuesta caro equivocar: ``batch_run`` hace ``kwargs[rng_kwarg_name] = rng_i``
sobre los kwargs ya construidos (``mesa/batchrunner.py``), de modo que una semilla puesta
en ``parameters`` se sobrescribe en silencio y todas las corridas acaban con ``rng=None``.
El barrido entonces parece funcionar, pero cada corrida usa un mundo distinto y los
resultados son ruido: parámetros que no pueden influir en una política —el costo de
edición sobre el agente reflejo, por ejemplo— aparecen cambiando su rendimiento.
"""

BASE: dict[str, Any] = {
    "size": 15,
    "n_resources": 8,
    "capacidad": 3,
    "densidad_obstaculos": 0.15,
    "max_steps": 400,
}

SWEEPS: dict[str, dict[str, Any]] = {
    "principal": {
        # La figura central: frontera de fase en dinamismo x costo de edición.
        **BASE,
        "policy": TODAS,
        "lambda_dinamismo": [0.0, 0.05, 0.1, 0.25, 0.5],
        "costo_edicion": [0, 2, 5, 10],
        "competencia": 0.9,
        "radio": 3,
    },
    "competencia": {
        # ¿Desde qué competencia del replanificador conviene auto-editarse?
        **BASE,
        "policy": CON_PLAN,
        "lambda_dinamismo": [0.0, 0.1, 0.25, 0.5],
        "competencia": [0.5, 0.7, 0.9, 1.0],
        "costo_edicion": 5,
        "radio": 3,
    },
    "observabilidad": {
        # El efecto de la observabilidad parcial: ver menos, decidir peor.
        **BASE,
        "policy": CON_PLAN,
        "lambda_dinamismo": [0.0, 0.1, 0.25, 0.5],
        "radio": [1, 3, None],
        "competencia": 0.9,
        "costo_edicion": 5,
    },
    "control2": {
        # Control de sanidad 2 (info/02-design.md §9): con deliberación gratuita, oráculo
        # perfecto y observabilidad total, el lazo cerrado no puede perder. Las tres
        # condiciones hacen falta a la vez y ningún otro barrido las fija juntas.
        **BASE,
        "policy": [str(Policy.OPEN_LOOP), str(Policy.CLOSED_LOOP)],
        "lambda_dinamismo": [0.0, 0.05, 0.1, 0.25, 0.5],
        "costo_edicion": 0,
        "competencia": 1.0,
        "radio": None,
    },
    "control3": {
        # Control de sanidad 3: un replanificador mediocre y caro debe destruir un plan
        # correcto. Si no aparece, el modelo de costo no muerde.
        **BASE,
        "policy": [str(Policy.OPEN_LOOP), str(Policy.CLOSED_LOOP)],
        "lambda_dinamismo": [0.0, 0.05],
        "costo_edicion": 10,
        "competencia": 0.5,
        "radio": 3,
    },
    "control4": {
        # Control de sanidad 4: con B=0, GOVERNED no puede reparar de forma proactiva y
        # solo le quedan las replanificaciones forzadas por un fallo, que se pagan igual
        # que las de OPEN_LOOP. Debe ser idéntica a OPEN_LOOP, corrida a corrida.
        **BASE,
        "policy": [str(Policy.OPEN_LOOP), str(Policy.GOVERNED)],
        "lambda_dinamismo": [0.1, 0.25, 0.5],
        "costo_edicion": [0, 5],
        "presupuesto": 0,
        "competencia": 0.9,
        "radio": 3,
    },
    "orden": {
        # Paquete 1 de docs/roadmap-c4.md: ¿dependen las conclusiones de que el
        # recolector actúe siempre antes de la deriva? Subconjunto de `principal` con el
        # orden sorteado por tick; lo que se compara es el signo de las diferencias.
        **BASE,
        "policy": [
            str(Policy.MODEL_BASED),
            str(Policy.OPEN_LOOP),
            str(Policy.COLD_RESTART),
            str(Policy.CLOSED_LOOP),
        ],
        "lambda_dinamismo": [0.1, 0.25, 0.5],
        "costo_edicion": [2, 5],
        "competencia": 0.9,
        "radio": 3,
        "orden_aleatorio": True,
    },
    "gobernanza": {
        # ¿Acotar las ediciones rescata al agente del thrashing? B=0 es el extremo en
        # que GOVERNED se reduce a OPEN_LOOP (B solo acota las reparaciones proactivas).
        **BASE,
        "policy": [str(Policy.CLOSED_LOOP), str(Policy.GOVERNED)],
        "lambda_dinamismo": [0.1, 0.25, 0.5],
        "presupuesto": [0, 3, 5, 10, 25],
        "competencia": 0.9,
        "costo_edicion": 5,
        "radio": 3,
    },
    "conocimiento": {
        # KB-2 (docs/roadmap-c4b.md) y C5-B (docs/roadmap-c5.md): H1, H1b, H4, HB1,
        # HB3, HB4. Las filas de OPEN_LOOP y CLOSED_LOOP reproducen exactamente las de
        # `observabilidad` y las de MODEL_BASED con r=3 las de `principal` (c=5): los
        # dos parámetros nuevos solo los leen las políticas que infieren. Es la
        # regresión de tests/test_conocimiento.py.
        **BASE,
        "policy": POLITICAS_CONOCIMIENTO,
        "lambda_dinamismo": [0.0, 0.1, 0.25, 0.5],
        "radio": [1, 3, None],
        "competencia": 0.9,
        "costo_edicion": 5,
        "horizonte_validez": "llegada",
        "ticks_por_ask": 0,
    },
    "conocimiento_ahora": {
        # La ablación: con horizonte "ahora" la pregunta 3 reproduce el monitor de
        # CLOSED_LOOP, así que no cambia *cuándo* se repara y aísla el aporte de las
        # preguntas 1 y 2 (candidatos y orden de objetivos). Con r=∞ es el control exacto
        # H2/HB2 (≡ CLOSED_LOOP semilla a semilla), que hace de `bayes_control`.
        **BASE,
        "policy": QUE_INFIEREN,
        "lambda_dinamismo": [0.0, 0.1, 0.25, 0.5],
        "radio": [1, 3, None],
        "competencia": 0.9,
        "costo_edicion": 5,
        "horizonte_validez": "ahora",
        "ticks_por_ask": 0,
    },
    "conocimiento_costo": {
        # H3: cobrar cada consulta en ticks quieto. ¿Desde qué costo de preguntar deja
        # de compensar la ventaja de H1? Una frontera análoga a la de `c`.
        **BASE,
        "policy": QUE_INFIEREN,
        "lambda_dinamismo": [0.1, 0.25, 0.5],
        "radio": 3,
        "competencia": 0.9,
        "costo_edicion": 5,
        "horizonte_validez": "llegada",
        "ticks_por_ask": [1, 2, 5],
    },
    "escasez": {
        # Paquete 4 de docs/roadmap-c4.md, régimen mixto: ¿depende el valor de
        # replanificar (y de no planificar) de la abundancia de recursos? KNOWLEDGE_BASED
        # entra porque su H1 de KB-2 se sostuvo (en parte). La celda n_resources=8
        # reproduce `principal` (c=5) y `conocimiento` (r=3): tests/test_escasez.py.
        **BASE,
        "policy": [
            str(Policy.MODEL_BASED),
            str(Policy.OPEN_LOOP),
            str(Policy.COLD_RESTART),
            str(Policy.CLOSED_LOOP),
            str(Policy.KNOWLEDGE_BASED),
        ],
        "n_resources": [2, 4, 8, 16],
        "lambda_dinamismo": [0.0, 0.1, 0.25, 0.5],
        "costo_edicion": 5,
        "competencia": 0.9,
        "radio": 3,
        "horizonte_validez": "llegada",
        "ticks_por_ask": 0,
    },
    "escasez_inf": {
        # El mismo barrido en el régimen donde replanificar gana (el de `control2`:
        # deliberación gratuita, oráculo perfecto, visión total). n_resources=8
        # reproduce `control2`.
        **BASE,
        "policy": [
            str(Policy.OPEN_LOOP),
            str(Policy.COLD_RESTART),
            str(Policy.CLOSED_LOOP),
        ],
        "n_resources": [2, 4, 8, 16],
        "lambda_dinamismo": [0.0, 0.1, 0.25, 0.5],
        "costo_edicion": 0,
        "competencia": 1.0,
        "radio": None,
    },
}

SMOKE: dict[str, Any] = {
    **BASE,
    "max_steps": 150,
    "policy": [str(Policy.OPEN_LOOP), str(Policy.CLOSED_LOOP)],
    "lambda_dinamismo": [0.0, 0.3],
    "costo_edicion": 5,
}


def ejecutar(
    parameters: dict[str, Any],
    *,
    procesos: int | None,
    semillas: list[int] | None = None,
) -> pd.DataFrame:
    """Correr un barrido y devolver la última fila de cada corrida."""
    semillas = SEMILLAS if semillas is None else semillas
    max_steps = parameters.get("max_steps", 400)
    filas = batch_run(
        OASysWorld,
        parameters=parameters,
        rng=semillas,
        max_steps=max_steps if isinstance(max_steps, int) else max(max_steps),
        data_collection_period=-1,
        number_processes=procesos,
        display_progress=True,
    )
    df = pd.DataFrame(filas)

    # Guarda contra el fallo silencioso descrito en SEMILLAS: si las semillas no
    # llegaron al modelo, el barrido entero es ruido y más vale enterarse aquí.
    if "rng" not in df.columns or df["rng"].isna().all():
        raise RuntimeError(
            "las semillas no llegaron al modelo: pásalas por el argumento `rng` de "
            "batch_run, nunca dentro de `parameters`"
        )
    return df


DINAMICA: dict[str, Any] = {
    # Paquete 3 de docs/roadmap-c4.md: la serie por tick, no solo el valor final.
    # GOVERNED sin presupuesto es CLOSED_LOOP, así que no se repite.
    **BASE,
    "policy": [str(p) for p in ORIGINALES if p is not Policy.GOVERNED],
    "lambda_dinamismo": [0.0, 0.1, 0.25, 0.5],
    "costo_edicion": 5,
    "competencia": 0.9,
    "radio": 3,
}

COLUMNAS_DINAMICA = [
    "rng",
    "politica",
    "lambda_dinamismo",
    "tick",
    "entregas",
    "utilidad_neta",
    "divergencias_reales",
    "n_ediciones",
    "pasos_deliberando",
    "carga_perdida",
]


def correr_dinamica(
    parameters: dict[str, Any] | None = None,
    *,
    cada: int = 5,
    procesos: int | None = 1,
    semillas: list[int] | None = None,
) -> pd.DataFrame:
    """Correr un barrido guardando la serie temporal de cada corrida, decimada.

    ``ejecutar`` pide a ``batch_run`` solo la última fila de cada corrida, por lo que la
    dinámica que el ``DataCollector`` ya recolecta se pierde. Aquí se pide una fila cada
    ``cada`` ticks (más el tick 0 y el último, que ``batch_run`` siempre incluye cuando
    ``max_steps`` es múltiplo de ``cada``; si no lo es, se añade a mano).

    Returns:
        Formato largo, una fila por (corrida, tick), con :data:`COLUMNAS_DINAMICA`.
    """
    parameters = DINAMICA if parameters is None else parameters
    semillas = SEMILLAS if semillas is None else semillas
    max_steps = int(parameters.get("max_steps", 400))
    filas = batch_run(
        OASysWorld,
        parameters=parameters,
        rng=semillas,
        max_steps=max_steps,
        data_collection_period=1 if max_steps % cada else cada,
        number_processes=procesos,
        display_progress=False,
    )
    df = pd.DataFrame(filas).rename(columns={"Step": "tick"})
    df["tick"] = df["tick"].astype(int)
    ultimo = df.groupby("RunId")["tick"].transform("max")
    df = df[(df["tick"] % cada == 0) | (df["tick"] == ultimo)]
    if "lambda_dinamismo" not in df.columns:
        df["lambda_dinamismo"] = parameters.get("lambda_dinamismo", 0.1)
    return df[COLUMNAS_DINAMICA].reset_index(drop=True)


def resumen(df: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """Media y desviación de las métricas clave, agrupadas."""
    metricas = [
        "entregas",
        "utilidad_neta",
        "pasos_deliberando",
        "n_ediciones",
        "n_ediciones_desperdiciadas",
        "n_ediciones_por_fallo",
        "carga_perdida",
        "latencia_deteccion",
    ]
    presentes = [m for m in metricas if m in df.columns]
    return df.groupby(por)[presentes].agg(["mean", "std"]).round(2)


def main() -> None:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--smoke", action="store_true", help="barrido mínimo de humo")
    grupo.add_argument("--sweep", choices=sorted(SWEEPS), help="un barrido concreto")
    grupo.add_argument("--full", action="store_true", help="todos los barridos")
    grupo.add_argument(
        "--dinamica",
        action="store_true",
        help="series temporales -> results/dinamica.parquet",
    )
    parser.add_argument(
        "--procesos",
        type=int,
        default=1,
        help="procesos en paralelo; 0 = todos los núcleos",
    )
    args = parser.parse_args()

    procesos = None if args.procesos == 0 else args.procesos
    RESULTS.mkdir(exist_ok=True)

    if args.smoke:
        df = ejecutar(SMOKE, procesos=procesos, semillas=[0, 1, 2])
        print(resumen(df, ["policy", "lambda_dinamismo"]).to_string())
        return

    if args.dinamica:
        df = correr_dinamica(procesos=procesos)
        destino = RESULTS / "dinamica.parquet"
        df.to_parquet(destino, index=False)
        print(f"{len(df)} filas -> {destino}")
        return

    nombres = sorted(SWEEPS) if args.full else [args.sweep]
    for nombre in nombres:
        print(f"\n=== barrido: {nombre} ===")
        df = ejecutar(SWEEPS[nombre], procesos=procesos)
        destino = RESULTS / f"{nombre}.csv"
        df.to_csv(destino, index=False)
        print(f"{len(df)} corridas -> {destino}")


if __name__ == "__main__":
    main()
