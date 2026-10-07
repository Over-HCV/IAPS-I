# `project/` — proyecto final y ejemplos de referencia

Esta carpeta contiene dos cosas distintas que conviene no confundir.

## 1. El proyecto final: [`oasys_abm/`](oasys_abm/)

**Planes auto-editables: lazo abierto vs. replanificación.** Modelo basado en agentes que
mide bajo qué condiciones del entorno un agente que reescribe su propio plan supera a uno
con plan estático, y a partir de qué costo de reescritura la ventaja se invierte.

Entrar por [`oasys_abm/README.md`](oasys_abm/README.md). Los tres documentos de diseño se
leen en orden:

| Documento | Contenido |
|---|---|
| [`oasys_abm/docs/00-rationale.md`](oasys_abm/docs/00-rationale.md) | Por qué este proyecto y por qué no los otros. Hipótesis falsables |
| [`oasys_abm/docs/01-mapping.md`](oasys_abm/docs/01-mapping.md) | Diccionario OASys ↔ Russell & Norvig ↔ MESA |
| [`oasys_abm/docs/02-design.md`](oasys_abm/docs/02-design.md) | PEAS, arquitecturas de agente, métricas, plan de barrido, controles de sanidad |

Para ver resultados sin leer nada antes:

```bash
PYTHONPATH=project uv run python -m oasys_abm.analysis --controles   # ¿los datos son creíbles?
PYTHONPATH=project uv run python -m oasys_abm.analysis --figuras     # las cinco figuras
```

## 2. Ejemplos de Mesa vendorizados: `basic/`, `advanced/`, `experimental/`

Copia local de los modelos de ejemplo de
[projectmesa/mesa-examples](https://github.com/projectmesa/mesa) —Schelling, Boids, Game of
Life, Wolf-Sheep, Sugarscape, Epstein, tram model— usada como material de referencia del
curso, no como parte del proyecto. Cada subcarpeta trae su propio `Readme.md` y su `app.py`
de Solara:

```bash
uv run solara run project/basic/schelling/app.py
```

## Por qué `PYTHONPATH=project`

`project/__init__.py` reexporta `mesa.examples.*` para los ejemplos de arriba, e importa
`mesa.examples.experimental`, que no existe en la Mesa 3.5.1 del entorno. Para que el
proyecto final no arrastre esa dependencia, `oasys_abm` se usa como **paquete de primer
nivel**: se pone `project/` en la ruta de importación en vez de colgar de `project.__init__`.
