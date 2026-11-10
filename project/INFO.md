# `project/` — qué vive dónde

Este archivo es el mapa de la carpeta, mientras que la pregunta del proyecto, los
entregables y los comandos para correrlo están en [`README.md`](README.md). La carpeta
contiene dos cosas distintas que conviene no confundir: el proyecto final (todo lo que está
en la raíz de `project/` salvo `templates/`) y una copia de los ejemplos de Mesa usada como
material de referencia del curso.

## 1. El proyecto final

### Código (paquete `project`)

| Archivo | Qué contiene |
|---|---|
| `book.py` | El plan como programa editable: `Book` (líneas y contador de programa), `Line`, `LineOp` y `EditRejected`, que es la excepción con la que se rechaza una edición que reescribe líneas ya ejecutadas o que se sale del alcance de edición |
| `planner.py` | A\* y BFS sobre la retícula, escritos a mano porque son contenido del curso |
| `oracle.py` | El replanificador LLM abstraído como oráculo con competencia `p` y costo `c`, con sus dos modos de fallo plausibles (objetivo obsoleto y desvío) |
| `deliberation.py` | La deliberación como acción con duración, progreso e interrupción |
| `agents.py` | Las ocho políticas (`Policy`, con las propiedades `planifica`, `replanifica` e `infiere`), los recursos que derivan y el agente recolector `Collector`, incluidos los ganchos con los que `KNOWLEDGE_BASED` y `BAYESIAN` consultan qué saben antes de elegir objetivo y antes de pagar una reparación |
| `model.py` | `OASysWorld(Model)`: retícula, obstáculos, recursos móviles, orden de activación (fijo o sorteado con `orden_aleatorio`), conteo de derivas y de divergencias, los parámetros `horizonte_validez` y `ticks_por_ask` de las políticas que infieren, y `DataCollector` |
| `logica.py` | Motor de inferencia proposicional sin Mesa (KB-1): oraciones, enumeración de modelos (`tt_entails`), CNF, DPLL, `KnowledgeBase` con `TELL`/`ASK` y `exactly`; es el nivel de conocimiento contra el que se prueba `conocimiento.py` |
| `conocimiento.py` | La base de conocimiento de `KNOWLEDGE_BASED` (KB-2): observaciones como fluentes, axioma de deriva y región posible `R(r,t)` por recurso, mantenida con operaciones de conjuntos sobre distancias geodésicas |
| `filtro.py` | La creencia de `BAYESIAN` (C5-B): λ aprendido con Beta–Bernoulli y un filtro *forward* de rejilla por recurso, cuyo soporte coincide con la región posible |
| `experiments.py` | Los trece barridos con `batch_run` (los cuatro principales, los de los controles 2, 3 y 6, el de orden de activación, los tres de conocimiento y los dos de escasez), el runner de series temporales `correr_dinamica` y la línea de comandos que los corre |
| `analysis.py` | Lectura de los CSV y del parquet de dinámica, controles de sanidad, comparación caliente contra frío, robustez al orden de activación, diferencias pareadas por semilla y las figuras (frontera, competencia, observabilidad, gobernanza, dinámica, conocimiento, calibración del filtro y escasez) |
| `sensibilidad.py` | Análisis de sensibilidad sobre las corridas guardadas (C5-S): η² de un factor y η² parcial por barrido y política, y lo mismo para la diferencia pareada `OPEN_LOOP − CLOSED_LOOP` |
| `calibracion.py` | Calibración de (λ, p) por ABC de rechazo a partir de la telemetría de un despliegue `OPEN_LOOP` (C5-A), y la política que recomienda la frontera bajo la posterior |
| `animacion.py` | Una corrida tick a tick: traza (con región posible o mapa de probabilidad para las políticas que infieren), animación `jshtml`, figura estática y tira de instantáneas |
| `__init__.py` | Raíz del paquete; los módulos se importan como `project.<módulo>` desde la raíz del repositorio |

### Datos, pruebas y documentos

| Ruta | Qué contiene |
|---|---|
| `results/*.csv` | Una fila por corrida de cada uno de los trece barridos (16.260 en total), que es lo que lee el cuaderno |
| `results/dinamica.parquet` | Serie temporal de 600 corridas, decimada cada 5 ticks (48.600 filas), escrita por `python -m project.experiments --dinamica` |
| `results/abc.parquet` | Tabla de referencia de la calibración ABC (3.000 simulaciones de (λ, p) muestreadas del prior), escrita por `python -m project.calibracion --referencia` |
| `results/figuras/*.png` | Las figuras `00` a `11`: las de `python -m project.analysis --figuras`, `python -m project.sensibilidad --figuras` y `python -m project.calibracion --figura`, más `00-trayectoria.png` |
| `results/animaciones/*.png` | Tiras de instantáneas de `CLOSED_LOOP`, `KNOWLEDGE_BASED` y `BAYESIAN` para la presentación |
| `tests/` | 278 pruebas en 16 archivos (277 pasan y una se salta): invariantes del plan, A\* contra BFS, oráculo, deliberación, regla de costo, orden de activación, dinámica, motor lógico, región posible, filtro, escasez, sensibilidad, calibración, animación y controles de sanidad del modelo |
| `notebook.ipynb` | Cuaderno de resultados final |
| `info/` | Racional, diccionario conceptual y diseño formal, que se leen en orden (`00`, `01`, `02`) |
| `docs/avance-01/` | Avance 1 en LaTeX |
| `docs/avance-02/avance-02.ipynb` | Avance 2: versión simplificada y autocontenida del modelo, en un solo cuaderno |
| `docs/guion/` | Guion de trabajo para comunicar el proyecto y anexo sobre planificación clásica (no son entregables) |
| `docs/roadmap-c4.md`, `docs/roadmap-c4b.md`, `docs/roadmap-c5.md` | Documentos de trabajo de las extensiones posteriores al Avance 2 (sesiones 4, 4B y 5), por paquetes con checklist, hipótesis previas y resultado |
| `docs/final/` | Documento final del proyecto en LaTeX, en preparación (estructura de artículo, secciones en `secciones/`) |
| `docs/common/`, `docs/bib/`, `docs/assets/` | Preámbulo, macros, metadatos, bibliografía y logo compartidos por los documentos LaTeX; ver [`docs/README.md`](docs/README.md) |

### Cómo se importa

El paquete es `project` y se usa siempre desde la raíz del repositorio, de forma que
`uv run python -m project.experiments` y `from project import analysis` funcionan sin
modificar `PYTHONPATH` (el cuaderno sube desde su carpeta hasta encontrar la raíz y la pone
en `sys.path`). Cabe mencionar que versiones anteriores del proyecto vivían en
`project/oasys_abm/` y se importaban con `PYTHONPATH=project`, por lo que cualquier
instrucción que todavía mencione esa ruta está desactualizada.

## 2. Ejemplos de Mesa vendorizados: `templates/`

Copia local de los modelos de ejemplo de
[projectmesa/mesa](https://github.com/projectmesa/mesa) (Schelling, Boids, Game of Life,
Boltzmann, Virus on Network, Wolf-Sheep, Sugarscape, Epstein, PD Grid, Alliance Formation y
el tram model), organizada en `templates/basic/`, `templates/advanced/` y
`templates/experimental/`, y usada como material de referencia del curso, no como parte del
proyecto. Cada subcarpeta trae su propio `Readme.md` y su `app.py` de Solara, que no está
instalado en el entorno del repositorio y por lo tanto se agrega aparte al correrlos (por ejemplo
con `--with`; el comando no se probó en la versión actual):

```bash
uv run --with solara solara run project/templates/basic/schelling/app.py
```

`templates/__init__.py` reexporta los modelos desde `mesa.examples.*`, y como
`mesa.examples.experimental` no existe en la Mesa 3.5.1 del entorno, el import del tram
model es tolerante (queda en `None`) en vez de romper el paquete.
