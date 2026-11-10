# Planes auto-editables: lazo abierto vs. replanificación

Proyecto final — **Inteligencia Artificial: Representación y Solución de Problemas**
(32310004), Universidad del Rosario.

Este archivo es la puerta de entrada: qué pregunta se responde, qué se entrega y cómo se
corre. El mapa de qué vive en cada archivo y carpeta de `project/` está en
[`INFO.md`](INFO.md).

## La pregunta

> ¿Bajo qué condiciones del entorno un agente que reescribe su propio plan supera a uno con
> plan estático, y a partir de qué costo de reescritura la ventaja se invierte?

La pregunta surge de un motor de ejecución agéntica propio, OASys, en el que un agente puede
reescribir el programa que lo ejecuta, y en el que esa capacidad existía sin ninguna métrica
que dijera si conviene usarla, así como con tres decisiones de diseño resueltas por intuición
(cuándo surte efecto una edición, cuántas veces se delibera y quién autoriza la reescritura).
Cabe mencionar que el problema resulta ser clásico, dado que el programa editable es un
**plan**, revisarlo contra el mundo es **monitoreo de ejecución**, reescribirlo es
**replanificación**, y aplicar la edición en la ejecución siguiente (reinicio en frío) o sobre
la ejecución en curso (reparación en caliente) es la distinción entre **lazo abierto y lazo
cerrado** de Russell & Norvig §11.5, por lo que el trabajo modela esa semántica en MESA y mide
la frontera entre ambos regímenes.

## Lo que se encontró, en breve

Cabe mencionar primero que una versión anterior del modelo dejaba que el lazo abierto
replanificara gratis tras un fallo, lo cual inflaba su ventaja y la del presupuesto de
ediciones, por lo que la regla actual cobra el mismo replanificador al mismo precio a toda
política ([`info/02-design.md`](info/02-design.md) §3.2) y las cifras siguientes salen del
barrido vuelto a correr con ella (el detalle, con sus errores estándar, está en el cuaderno).

- **Lazo abierto contra lazo cerrado:** Con observabilidad parcial (`r=3`), reparar al ver la
  divergencia y esperar a que el plan falle casi empatan, con diferencias de −9 a +26 puntos
  que en su mayoría caen dentro del error estándar de 30 réplicas.
- **Deliberar contra no deliberar:** Cuando el entorno cambia rápido y deliberar es caro, el
  agente reactivo basado en modelo, que nunca delibera, supera a todo lo que planifica (98.3
  contra 53.3 de la mejor política con plan a λ=0.5 y `c=2`).
- **En caliente contra en frío:** Reparar en caliente supera al reinicio en frío desde λ=0.1
  (de +16 a +22 puntos con `c` entre 2 y 5, y +32 a λ=0.5 con deliberación gratuita), salvo
  donde las dos políticas colapsan.
- **Observabilidad y presupuesto:** Ver más sube el nivel de todas las políticas, pero con
  `c=5` la visión total no hace ganar al lazo cerrado (114.5 contra 129.5 del lazo abierto), y
  acotar las reparaciones proactivas evita el peor caso a λ=0.5 (23.7 con `B=3` contra 10.0)
  sin superar a no repararlas en absoluto (27.0 con `B=0`).

## Entregables

| Entregable | Qué es |
|---|---|
| [`notebook.ipynb`](notebook.ipynb) | **Cuaderno de resultados final.** Importa los módulos del paquete, lee las 8.640 corridas ya guardadas en `results/` e interpreta cada figura; no vuelve a ejecutar el barrido |
| [`docs/avance-02/avance-02.ipynb`](docs/avance-02/avance-02.ipynb) | **Avance 2, versión simplificada y autocontenida.** Todo el modelo vive en el propio cuaderno (tres políticas, observabilidad total y replanificador exacto), de forma que se puede abrir sin el resto del repositorio, incluso en Colab |
| [`docs/avance-01/`](docs/avance-01/) | Avance 1 en LaTeX (contexto, agentes, variables de seguimiento y referencias) |
| [`docs/`](docs/) | Template LaTeX compartido por los documentos del curso; ver [`docs/README.md`](docs/README.md) |

## Documentación de diseño

Se lee en orden:

| Documento | Contenido |
|---|---|
| [`info/00-rationale.md`](info/00-rationale.md) | **Por qué este proyecto y no otros.** Alternativas evaluadas (Wumpus, coaliciones, LLM real, MESA 4.0) con la razón de cada descarte, e hipótesis falsables escritas antes de correr nada |
| [`info/01-mapping.md`](info/01-mapping.md) | **Diccionario concepto ↔ Russell & Norvig ↔ implementación.** Cada concepto de un motor de ejecución agéntica con su contraparte en la teoría de planificación y en el código, y las tres asimetrías entre ambas tradiciones |
| [`info/02-design.md`](info/02-design.md) | **Diseño formal.** PEAS, clasificación del entorno, las seis políticas, métricas operacionales, barridos y controles de sanidad |

## Cómo correr

Todos los comandos se ejecutan desde la raíz del repositorio, pues el paquete es `project` y
sus módulos se importan como `project.<módulo>` (no hace falta tocar `PYTHONPATH`):

```bash
# 116 pruebas: invariantes del plan, A* contra BFS, oráculo, deliberación, regla de costo y controles del modelo
uv run pytest project/tests -q

# barrido de humo (12 corridas cortas): comprueba el pipeline e imprime un resumen, no escribe CSV
uv run python -m project.experiments --smoke

# un barrido concreto, o los siete; --procesos 0 usa todos los núcleos
uv run python -m project.experiments --sweep principal --procesos 0
uv run python -m project.experiments --full --procesos 0
```

Cada barrido se guarda en `results/<nombre>.csv`, y entre los siete suman **8.640 corridas**
(30 réplicas por combinación, `T_max=400`):

| Barrido | Qué varía | Corridas |
|---|---|---|
| `principal` | 6 políticas × λ × `c` | 3.600 |
| `competencia` | 4 políticas con plan × λ × `p` | 1.920 |
| `observabilidad` | 4 políticas con plan × λ × `r` | 1.440 |
| `gobernanza` | `CLOSED_LOOP` y `GOVERNED` × λ × `B` (con `B=0`) | 900 |
| `control2` | control de sanidad 2 (`c=0`, `p=1`, `r=∞`) | 300 |
| `control3` | control de sanidad 3 (`p=0.5`, `c=10`, λ bajo) | 120 |
| `control4` | control de sanidad 6 (`B=0` ⇒ `GOVERNED` = `OPEN_LOOP`, corrida a corrida) | 360 |

Vale la pena anotar que no se cronometró el barrido completo en la versión actual, aunque
por el ritmo del barrido de humo se estima en unos pocos minutos con `--procesos 0`.

## Cómo ver los resultados

Los CSV ya están en `results/`, así que lo siguiente funciona sin correr ningún barrido antes:

```bash
# ¿son creíbles los datos? Los controles de sanidad 1, 2, 3 y 6 de info/02-design.md §9
uv run python -m project.analysis --controles

# valor de reparar en caliente frente a reiniciar en frío: CLOSED_LOOP menos COLD_RESTART
uv run python -m project.analysis --delta

# las cinco figuras de los barridos -> results/figuras/*.png
uv run python -m project.analysis --figuras

# el recorrido completo, con la interpretación de cada figura
uv run jupyter lab project/notebook.ipynb
```

`analysis.py` separa los datos del dibujo, de forma que las funciones de datos devuelven
`DataFrame`s y una sola primitiva los pinta, por lo que cambiar de backend es una palabra:

```python
from project import analysis as an
an.fig_frontera(backend="plotly")   # o an.BACKEND = "plotly" para todas
```

`animacion.py` hace lo mismo para una corrida concreta (un `Frame` por tick con posición,
creencias, plan vivo, acción ejecutada y ediciones), y `mostrar()` es lo que llama el
cuaderno, mientras que con `animacion.MODO = "estatico"` la misma corrida sale como una sola
figura.

## Entorno

MESA **3.5.1** (la instalada en `.venv`). La justificación técnica de no usar el checkout
4.0.0a0 de `learn/mesa` está en [`info/00-rationale.md`](info/00-rationale.md) §4, y en
resumen lo único que 4.0 aporta es la clase `Action` (una acción con duración e
interrupción), que es precisamente lo que este trabajo escribe a mano porque es su objeto de
estudio.
