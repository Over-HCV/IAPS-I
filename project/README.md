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
política ([`info/02-design.md`](info/02-design.md) §3.2) y las cifras siguientes salen de los
barridos vueltos a correr con ella (el detalle, con sus errores estándar, está en el cuaderno).

- **Lazo abierto contra lazo cerrado:** Con observabilidad parcial (`r=3`), reparar al ver la
  divergencia y esperar a que el plan falle casi empatan, con diferencias de −9 a +26 puntos
  que en su mayoría caen dentro del error estándar de 30 réplicas, y al sortear el orden de
  activación la diferencia cambia de signo en tres de seis celdas, por lo que no tiene un signo
  estable.
- **Deliberar contra no deliberar:** Cuando el entorno cambia rápido y deliberar es caro, el
  agente reactivo basado en modelo, que nunca delibera, supera a todo lo que planifica (98.3
  contra 53.3 de la mejor política con plan a λ=0.5 y `c=2`), y la brecha crece con la
  abundancia de recursos (a λ=0.5, de +13 con dos recursos a +96 con dieciséis).
- **En caliente contra en frío:** Reparar en caliente supera al reinicio en frío desde λ=0.1
  (de +16 a +22 puntos con `c` entre 2 y 5, y +32 a λ=0.5 con deliberación gratuita), salvo
  donde las dos políticas colapsan, y es la conclusión más robusta del trabajo, pues conserva
  el signo en cinco de seis celdas con el orden de activación sorteado.
- **Observabilidad y presupuesto:** Ver más sube el nivel de todas las políticas, pero con
  `c=5` la visión total no hace ganar al lazo cerrado (114.5 contra 129.5 del lazo abierto), y
  acotar las reparaciones proactivas evita el peor caso a λ=0.5 (23.7 con `B=3` contra 10.0)
  sin superar a no repararlas en absoluto (27.0 con `B=0`).
- **Saber qué se sabe (lógica y probabilidad):** El agente basado en conocimiento, que solo
  repara cuando su KB deduce que el plan ya no puede cumplirse a la llegada, supera al lazo
  cerrado con el signo esperado en todas las celdas, aunque solo de forma significativa con
  `r=3` y λ=0.5 (+21.3 ± 3.8), la ventaja se invierte en cuanto cada consulta cuesta un tick y
  no alcanza a `MODEL_BASED` desde λ=0.25. El agente bayesiano aprende λ mirando (mediana de
  error 0.020 con `r=3`) y su filtro está calibrado, pero **no** supera al lógico (−16 ± 4.3),
  porque su regla de reparación repara de más (16.3 reparaciones proactivas contra 9.5 a λ=0.5):
  trata cada reparación como si comprara certeza, cuando el plan reparado nace desactualizado.
- **Escasez:** La hipótesis de que reparar valdría más con recursos escasos se refuta en los
  dos regímenes medidos, pues donde replanificar gana (`c=0`, `p=1`, `r=∞`) la ventaja del lazo
  cerrado sobre el abierto crece con la abundancia (a λ=0.5, de +36.7 con dos recursos a +62.0
  con dieciséis), que es lo que predice el costo de oportunidad: con objetivos de sobra, cada
  tick perdido cuesta más entregas.
- **Qué parámetro importa:** La mayor parte de la varianza de la utilidad es ruido entre
  semillas y mapas; λ es el factor que más pesa en casi toda política con plan, mientras que
  en la diferencia entre lazo abierto y cerrado ningún factor explica más de una décima parte
  de la varianza (η² ≤ 0.09). Por calibración ABC, la telemetría de un despliegue recupera λ,
  pero no la competencia `p`, cuya posterior queda casi igual al prior.

## Entregables

| Entregable | Qué es |
|---|---|
| [`notebook.ipynb`](notebook.ipynb) | **Cuaderno de resultados final.** Importa los módulos del paquete, lee las 16.260 corridas ya guardadas en `results/` (más las series de `dinamica.parquet` y la tabla ABC de `abc.parquet`) e interpreta cada figura; no vuelve a ejecutar ningún barrido |
| [`docs/final/`](docs/final/) | **Documento final** en LaTeX, en preparación (introducción, marco, modelo, diseño, resultados, Avance 2, discusión, límites y conclusiones) |
| [`docs/avance-02/avance-02.ipynb`](docs/avance-02/avance-02.ipynb) | **Avance 2, versión simplificada y autocontenida.** Todo el modelo vive en el propio cuaderno (tres políticas, observabilidad total y replanificador exacto), de forma que se puede abrir sin el resto del repositorio, incluso en Colab |
| [`docs/avance-01/`](docs/avance-01/) | Avance 1 en LaTeX (contexto, agentes, variables de seguimiento y referencias) |
| [`docs/`](docs/) | Template LaTeX compartido por los documentos del curso; ver [`docs/README.md`](docs/README.md) |

## Documentación de diseño

Se lee en orden:

| Documento | Contenido |
|---|---|
| [`info/00-rationale.md`](info/00-rationale.md) | **Por qué este proyecto y no otros.** Alternativas evaluadas (Wumpus, coaliciones, LLM real, MESA 4.0) con la razón de cada descarte, e hipótesis falsables escritas antes de correr cada barrido, con su contraste |
| [`info/01-mapping.md`](info/01-mapping.md) | **Diccionario concepto ↔ Russell & Norvig ↔ implementación.** Cada concepto de un motor de ejecución agéntica con su contraparte en la teoría de planificación y en el código, los conceptos de lógica (C4B) y de inferencia probabilística (C5) que entraron después, y las tres asimetrías entre ambas tradiciones |
| [`info/02-design.md`](info/02-design.md) | **Diseño formal.** PEAS, clasificación del entorno, las ocho políticas, métricas operacionales, barridos y controles de sanidad |
| [`docs/roadmap-c4.md`](docs/roadmap-c4.md), [`roadmap-c4b.md`](docs/roadmap-c4b.md), [`roadmap-c5.md`](docs/roadmap-c5.md) | **Extensiones posteriores al Avance 2,** derivadas de las sesiones 4, 4B y 5: orden de activación, tira, dinámica, escasez, agente basado en conocimiento, agente bayesiano, sensibilidad y calibración, cada una con sus hipótesis previas y su resultado |

## Cómo correr

Todos los comandos se ejecutan desde la raíz del repositorio, pues el paquete es `project` y
sus módulos se importan como `project.<módulo>` (no hace falta tocar `PYTHONPATH`):

```bash
# 277 pruebas (y una que se salta): invariantes del plan, A* contra BFS, oráculo, deliberación,
# regla de costo, motor lógico, región posible, filtro, sensibilidad, ABC y controles del modelo
uv run pytest project/tests -q

# barrido de humo (12 corridas cortas): comprueba el pipeline e imprime un resumen, no escribe CSV
uv run python -m project.experiments --smoke

# un barrido concreto, o los trece; --procesos 0 usa todos los núcleos
uv run python -m project.experiments --sweep principal --procesos 0
uv run python -m project.experiments --full --procesos 0

# las series por tick (600 corridas, decimadas cada 5 ticks) -> results/dinamica.parquet
uv run python -m project.experiments --dinamica --procesos 0

# la tabla de referencia de ABC (3.000 simulaciones) -> results/abc.parquet, y una calibración
uv run python -m project.calibracion --referencia --procesos 0
uv run python -m project.calibracion --demo --verdad 0.25 0.7
```

Vale la pena anotar que si el `.venv` se movió de disco, `uv run pytest` falla con
«Failed to spawn», porque los ejecutables del entorno (como `.venv/bin/pytest`) guardan en su primera línea la
ruta absoluta del intérprete;
se arregla con `uv sync --reinstall`, y mientras tanto funciona llamar al intérprete
directamente (`.venv/bin/python -m pytest project/tests -q`).

Cada barrido se guarda en `results/<nombre>.csv`, y entre los trece suman **16.260 corridas**
(30 réplicas por combinación, `T_max=400`):

| Barrido | Qué varía | Corridas |
|---|---|---|
| `principal` | 6 políticas originales × λ × `c` | 3.600 |
| `competencia` | 4 políticas con plan × λ × `p` | 1.920 |
| `observabilidad` | 4 políticas con plan × λ × `r` | 1.440 |
| `gobernanza` | `CLOSED_LOOP` y `GOVERNED` × λ × `B` (con `B=0`) | 900 |
| `control2` | control de sanidad 2 (`c=0`, `p=1`, `r=∞`) | 300 |
| `control3` | control de sanidad 3 (`p=0.5`, `c=10`, λ bajo) | 120 |
| `control4` | control de sanidad 6 (`B=0` ⇒ `GOVERNED` = `OPEN_LOOP`, corrida a corrida) | 360 |
| `orden` | 4 políticas × λ × `c` con el orden de activación sorteado | 720 |
| `conocimiento` | `MODEL_BASED`, `OPEN_LOOP`, `CLOSED_LOOP`, `KNOWLEDGE_BASED` y `BAYESIAN` × λ × `r`, horizonte `"llegada"` | 1.800 |
| `conocimiento_ahora` | las dos políticas que infieren × λ × `r`, horizonte `"ahora"` (ablación y controles H2/HB2) | 720 |
| `conocimiento_costo` | las dos políticas que infieren × λ × `ticks_por_ask` | 540 |
| `escasez` | 5 políticas × λ × `n_resources` (régimen mixto, `r=3`, `c=5`) | 2.400 |
| `escasez_inf` | 3 políticas con plan × λ × `n_resources` (`c=0`, `p=1`, `r=∞`) | 1.440 |

Además, `results/dinamica.parquet` guarda la serie temporal de 600 corridas (48.600 filas) y
`results/abc.parquet` la tabla de referencia de la calibración. Cabe mencionar que los siete
barridos originales quedaron congelados a las seis políticas originales, de forma que
`KNOWLEDGE_BASED` y `BAYESIAN` solo aparecen en los barridos que las incluyen a propósito, y
que no se cronometró el barrido completo en la versión actual, aunque por el ritmo del barrido
de humo se estima en unos pocos minutos con `--procesos 0`.

## Cómo ver los resultados

Los CSV y los parquet ya están en `results/`, así que lo siguiente funciona sin correr ningún
barrido antes:

```bash
# ¿son creíbles los datos? Los controles de sanidad 1, 2, 3 y 6 de info/02-design.md §9
uv run python -m project.analysis --controles

# valor de reparar en caliente frente a reiniciar en frío: CLOSED_LOOP menos COLD_RESTART
uv run python -m project.analysis --delta

# las figuras de los barridos (01 a 07 y 11) -> results/figuras/*.png
uv run python -m project.analysis --figuras

# la sensibilidad (η² por factor) y sus figuras 08 y 09
uv run python -m project.sensibilidad --figuras

# la posterior ABC de (λ, p), figura 10
uv run python -m project.calibracion --figura

# el recorrido completo, con la interpretación de cada figura
uv run jupyter lab project/notebook.ipynb
```

Las figuras quedan numeradas de `00` a `11` en `results/figuras/`: la trayectoria de una
corrida (`00`, que exporta el cuaderno), la frontera, caliente contra frío, competencia,
observabilidad y gobernanza (`01`–`05`), las políticas que infieren (`06`), la calibración
del filtro bayesiano (`07`), la sensibilidad sobre cada política y sobre la diferencia entre
lazo abierto y cerrado (`08` y `09`), la posterior ABC (`10`) y la escasez (`11`). Las tiras de
instantáneas para la presentación (`CLOSED_LOOP`, `KNOWLEDGE_BASED` con su región posible y
`BAYESIAN` con su mapa de probabilidad) están en `results/animaciones/`.

`analysis.py` separa los datos del dibujo, de forma que las funciones de datos devuelven
`DataFrame`s y una sola primitiva los pinta, por lo que cambiar de backend es una palabra:

```python
from project import analysis as an
an.fig_frontera(backend="plotly")   # o an.BACKEND = "plotly" para todas
```

`animacion.py` hace lo mismo para una corrida concreta (un `Frame` por tick con posición,
creencias, región posible o mapa de probabilidad, plan vivo, acción ejecutada y ediciones), y
`mostrar()` es lo que llama el cuaderno, mientras que con `animacion.MODO = "estatico"` la
misma corrida sale como una sola figura y con `"tira"` como una fila de instantáneas.

## Entorno

MESA **3.5.1** (la instalada en `.venv`). La justificación técnica de no usar el checkout
4.0.0a0 de `learn/mesa` está en [`info/00-rationale.md`](info/00-rationale.md) §4, y en
resumen lo único que 4.0 aporta es la clase `Action` (una acción con duración e
interrupción), que es precisamente lo que este trabajo escribe a mano porque es su objeto de
estudio.
