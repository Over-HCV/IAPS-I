# Planes auto-editables: lazo abierto vs. replanificación

Proyecto final — **Inteligencia Artificial: Representación y Solución de Problemas**
(32310004), Universidad del Rosario.

## La pregunta

> ¿Bajo qué condiciones del entorno un agente que reescribe su propio plan supera a uno con
> plan estático, y a partir de qué costo de reescritura la ventaja se invierte?

La pregunta viene de un sistema real: **OASys**, un motor de ejecución agéntica en Rust donde
un agente LLM puede leer y reescribir el programa que lo ejecuta (tools `readBook` /
`editBook`). El sistema tiene esa capacidad implementada pero **sin ninguna métrica** que
diga si conviene usarla — y tres decisiones de diseño resueltas por intuición: el modo `hot`
declarado y no implementado, un `MAX_ITER = 5` puesto a dedo, y un humano como único freno
contra la replanificación improductiva.

Resulta que el problema es clásico. El Book es un plan jerárquico, `readBook` es monitoreo de
ejecución, `editBook` es replanificación, y `cold` vs `hot` es lazo abierto vs. lazo cerrado.
Este trabajo modela esa semántica en MESA y mide la frontera.

## Documentación

Leer en orden:

| Documento | Contenido |
|---|---|
| [`docs/00-rationale.md`](docs/00-rationale.md) | **Por qué este proyecto y por qué no los otros.** Alternativas evaluadas (Wumpus, coaliciones, LLM real, MESA 4.0) y la razón exacta de cada descarte. Hipótesis falsables |
| [`docs/01-mapping.md`](docs/01-mapping.md) | **Diccionario OASys ↔ Russell & Norvig ↔ MESA.** 13 filas con cita al archivo Rust real y a la sección de R&N. Las tres asimetrías entre ambas tradiciones |
| [`docs/02-design.md`](docs/02-design.md) | **Diseño formal.** PEAS, clasificación del entorno, las 6 arquitecturas de agente, métricas operacionales, plan de barrido, controles de sanidad |

## Estructura

```
book.py          Book / Line / program counter — el plan como programa
planner.py       A* y BFS sobre la retícula (escritos a mano: son contenido del curso)
oracle.py        El LLM abstraído como oráculo (competencia p, costo c)
deliberation.py  Deliberación como acción con duración, progreso e interrupción
agents.py        Las 6 arquitecturas de agente
model.py         OASysWorld(Model) — retícula, recursos móviles, DataCollector
experiments.py   Barridos con batch_run
analysis.py      Lectura de los CSV, controles de sanidad y las figuras
tests/           Invariantes y controles de sanidad
notebook.ipynb   Entregable del curso
results/         CSV de los barridos y figuras/*.png
```

## Cómo correr

Desde la raíz del repositorio:

```bash
# invariantes del plan, corrección de A* y controles de sanidad del modelo
uv run pytest project/oasys_abm/tests/

# barrido mínimo, para comprobar que el pipeline funciona
PYTHONPATH=project uv run python -m oasys_abm.experiments --smoke

# un barrido concreto, o todos; --procesos 0 usa todos los núcleos
PYTHONPATH=project uv run python -m oasys_abm.experiments --sweep principal
PYTHONPATH=project uv run python -m oasys_abm.experiments --full --procesos 0
```

Los resultados se guardan en `results/*.csv`. Los seis barridos completos son ~6.240
corridas; con `--procesos 0` tardan unos minutos.

## Cómo ver los resultados

Los CSV ya están en `results/`, así que esto funciona sin correr nada antes:

```bash
# ¿son creíbles los datos? Los tres controles de sanidad de docs/02-design.md §9
PYTHONPATH=project uv run python -m oasys_abm.analysis --controles

# cuánto vale implementar run=hot: CLOSED_LOOP menos COLD_RESTART
PYTHONPATH=project uv run python -m oasys_abm.analysis --delta

# las cinco figuras -> results/figuras/*.png
PYTHONPATH=project uv run python -m oasys_abm.analysis --figuras
```

Y el recorrido completo, con la interpretación de cada figura, está en
[`notebook.ipynb`](notebook.ipynb) — el entregable del curso:

```bash
uv run jupyter lab project/oasys_abm/notebook.ipynb
```

`analysis.py` separa los datos del dibujo: `cargar`, `agregar`, `delta_hot_vs_cold` y
`controles` devuelven `DataFrame`s, y una sola primitiva los pinta. Cambiar de backend es una
palabra:

```python
from oasys_abm import analysis as an
an.fig_frontera(backend="plotly")   # o an.BACKEND = "plotly" para todas
```

> **Por qué el `PYTHONPATH`.** El paquete no cuelga de `project/__init__.py`: ese módulo
> es la copia vendorizada de los ejemplos de Mesa y reexporta `mesa.examples.*`, que en
> Mesa 3.5.1 no incluye el `tram_model` de la rama experimental. Poniendo `project/` en la
> ruta, `oasys_abm` es un paquete de primer nivel y no arrastra esa dependencia.

## Entorno

MESA **3.5.1** (la instalada en `.venv`). La justificación técnica de no usar el checkout
4.0.0a0 de `learn/mesa` está en [`docs/00-rationale.md`](docs/00-rationale.md) §4: resumido,
lo único que 4.0 aporta es la clase `Action`, que es precisamente lo que este trabajo escribe
a mano porque es su objeto de estudio.
