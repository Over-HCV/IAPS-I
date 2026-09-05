"""Barridos de parámetros con ``batch_run``.

El plan experimental está en ``docs/02-design.md`` §5. El barrido completo es grande, así
que se ejecuta por etapas: cada una aísla una pregunta y se guarda por separado.

Uso::

    uv run python -m oasys_abm.experiments --smoke
    uv run python -m oasys_abm.experiments --sweep principal
    uv run python -m oasys_abm.experiments --full

(con ``project/`` en ``PYTHONPATH``; ver ``README.md``).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from mesa.batchrunner import batch_run
from oasys_abm.agents import Policy
from oasys_abm.model import OASysWorld
import pandas as pd

RESULTS = Path(__file__).parent / "results"

TODAS = [str(p) for p in Policy]
CON_PLAN = [str(p) for p in Policy if p.planifica]

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
        # El efecto del set `ignore` de OASys: ver menos, decidir peor.
        **BASE,
        "policy": CON_PLAN,
        "lambda_dinamismo": [0.0, 0.1, 0.25, 0.5],
        "radio": [1, 3, None],
        "competencia": 0.9,
        "costo_edicion": 5,
    },
    "control2": {
        # Control de sanidad 2 (docs/02-design.md §9): con deliberación gratuita, oráculo
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
    "gobernanza": {
        # ¿Acotar las ediciones rescata al agente del thrashing?
        **BASE,
        "policy": [str(Policy.CLOSED_LOOP), str(Policy.GOVERNED)],
        "lambda_dinamismo": [0.1, 0.25, 0.5],
        "presupuesto": [3, 5, 10, 25],
        "competencia": 0.9,
        "costo_edicion": 5,
        "radio": 3,
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


def resumen(df: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """Media y desviación de las métricas clave, agrupadas."""
    metricas = [
        "entregas",
        "utilidad_neta",
        "pasos_deliberando",
        "n_ediciones",
        "n_ediciones_desperdiciadas",
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

    nombres = sorted(SWEEPS) if args.full else [args.sweep]
    for nombre in nombres:
        print(f"\n=== barrido: {nombre} ===")
        df = ejecutar(SWEEPS[nombre], procesos=procesos)
        destino = RESULTS / f"{nombre}.csv"
        df.to_csv(destino, index=False)
        print(f"{len(df)} corridas -> {destino}")


if __name__ == "__main__":
    main()
