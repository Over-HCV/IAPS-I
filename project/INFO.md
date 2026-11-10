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
| `agents.py` | Las seis políticas (`Policy`), los recursos que derivan y el agente recolector |
| `model.py` | `OASysWorld(Model)`: retícula, obstáculos, recursos móviles, conteo de divergencias y `DataCollector` |
| `experiments.py` | Los siete barridos con `batch_run` (los cuatro principales y los de los controles 2, 3 y 6) y la línea de comandos que los corre |
| `analysis.py` | Lectura de los CSV, controles de sanidad, comparación caliente contra frío y las figuras |
| `animacion.py` | Una corrida tick a tick: traza, animación `jshtml` y figura estática |
| `__init__.py` | Raíz del paquete; los módulos se importan como `project.<módulo>` desde la raíz del repositorio |

### Datos, pruebas y documentos

| Ruta | Qué contiene |
|---|---|
| `results/*.csv` | Una fila por corrida de cada barrido (8.640 en total), que es lo que lee el cuaderno |
| `results/figuras/*.png` | Las figuras exportadas por `python -m project.analysis --figuras`, más `00-trayectoria.png` |
| `tests/` | 116 pruebas: invariantes del plan, A\* contra BFS, oráculo, deliberación, regla de costo, animación y controles de sanidad del modelo |
| `notebook.ipynb` | Cuaderno de resultados final |
| `info/` | Racional, diccionario conceptual y diseño formal, que se leen en orden (`00`, `01`, `02`) |
| `docs/avance-01/` | Avance 1 en LaTeX |
| `docs/avance-02/avance-02.ipynb` | Avance 2: versión simplificada y autocontenida del modelo, en un solo cuaderno |
| `docs/guion/` | Guion de trabajo para comunicar el proyecto y anexo sobre planificación clásica (no son entregables) |
| `docs/final/` | Documento final del proyecto (por crear) |
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
