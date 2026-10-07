# 00 — Racional: por qué este proyecto (y por qué no los otros)

> Este documento existe para dejar por escrito **el porqué de cada decisión**, incluidas
> las alternativas que se descartaron y la razón exacta del descarte. Es el registro de
> la fase de planeación; el diseño formal está en [`02-design.md`](02-design.md).

---

## 1. De dónde sale la pregunta

Este proyecto no empieza en el curso. Empieza en un sistema real: **OASys**, un motor de
ejecución agéntica escrito en Rust (Axum + tokio, ~45k LOC). En OASys se escribe un
programa en un DSL propio con la jerarquía `Device → Books → Pages → Lines → Cells`, y
un motor lo ejecuta con contador de programa, pila de llamadas y un almacén de variables
compartido. Algunas celdas son celdas `AI`: invocan un agente LLM.

La capacidad central del sistema es esta: **un agente puede leer y reescribir el programa
que lo está ejecutando**, mediante dos herramientas.

| Tool | Modo por defecto | Qué hace |
|---|---|---|
| `readBook` | `Allow` | Devuelve el fuente `.os` completo del device tal como el agente puede verlo |
| `editBook` | `Ask` | Parcha el fuente reemplazando `old_str` por `new_str`, como transacción validada |

*(`backend/src/agent/tools/builtin/oasys_surface.rs`, líneas 98–121.)*

La motivación de diseño fue sostener **tareas de horizonte largo**: procesos que ni un LLM
suelto puede completar (el contexto se degrada) ni un workflow determinista puede afrontar
(el entorno cambia y el flujo es estático). Un agente que reescribe su propio flujo, en
principio, escapa a las dos limitaciones.

**El problema es que esa capacidad nunca se midió.** El estado actual del sistema:

- `run=hot` está declarado en el DSL pero **no está implementado**. El motor lo detecta y
  registra literalmente `"[Engine] run=hot declared but not implemented; running cold
  (snapshot)"` (`backend/src/engine/mod.rs:134`). Todo corre en frío: el scheduler ejecuta
  una copia previa del device (`let device_snapshot = rt.device.clone();`, línea 142) y las
  ediciones del agente solo tienen efecto en la **siguiente** corrida.
- El bucle de herramientas del agente está acotado por `const MAX_ITER: usize = 5;`
  (`backend/src/agent/executor/mod.rs:14`). Cinco. Sin ninguna justificación derivada.
- `editBook` es modo `Ask`: **un humano** es el único freno real contra que el agente entre
  en un ciclo de reescrituras improductivas.

Es decir: hay tres decisiones de diseño importantes —cuándo aplicar una edición, cuántas
veces deliberar, y quién autoriza— y las tres están resueltas por intuición o por delegación
al usuario. **No existe ninguna métrica que diga si auto-editarse ayuda o estorba.**

## 2. La observación que convierte esto en un proyecto de IA clásica

Al leer Russell & Norvig con OASys en la cabeza, aparece que **todo el sistema ya está
descrito en la literatura**, con otro vocabulario:

- Un Book es un **plan jerárquico**.
- `readBook` es **monitoreo de ejecución** (comparar el plan contra el mundo).
- `editBook` es **replanificación**.
- `@lock` + `validate_edit` son **invariantes del plan** que la reparación no puede violar.
- El set `ignore` (qué páginas ve cada agente) es **observabilidad parcial**.
- `cold` vs `hot` es exactamente **planeación de lazo abierto vs. lazo cerrado**.

La tabla completa está en [`01-mapping.md`](01-mapping.md). Lo relevante aquí es la
consecuencia: si el problema es clásico, entonces **el resultado también debería serlo**, y
la teoría clásica dice algo muy concreto sobre él.

### Por qué la pregunta no es trivial

Uno podría pensar que replanificar siempre es mejor —más información, mejor plan—. No lo es,
y la razón es estructural:

- El **beneficio** de replanificar crece con el dinamismo del entorno. Si nada cambia, el
  plan inicial sigue siendo óptimo y replanificar no compra nada.
- El **costo** de replanificar es aproximadamente constante: deliberar consume tiempo (y en
  el caso real, tokens y dinero) durante el cual el agente no actúa.

Beneficio creciente contra costo constante ⇒ **existe un punto de cruce**. Por debajo de
cierto umbral de dinamismo, el agente estático gana; por encima, gana el que se auto-edita.
Y como el costo no es cero, no basta con "replanificar cuando haga falta": existe una
**frecuencia óptima de replanificación**, que es justamente el parámetro que OASys debería
exponer en vez de tener hardcodeado `cold` y `MAX_ITER=5`.

Esa frontera es medible. Medirla es el proyecto.

### Pregunta de investigación

> ¿Bajo qué condiciones del entorno un agente que reescribe su propio plan supera a uno con
> plan estático, y a partir de qué costo de reescritura la ventaja se invierte?

Con dos salidas: el entregable del curso, y una política de diseño concreta para OASys
(cuándo activar `run=hot`, y con qué modelo de costo reemplazar `MAX_ITER=5`).

---

## 3. Alternativas consideradas y por qué se descartaron

Se evaluaron tres dominios y tres tratamientos del LLM. Se documentan los descartes porque
el criterio importa más que la conclusión.

### 3.1 Dominio: grid de recolección con A\* — **elegido**

Un agente debe recoger recursos dispersos en una retícula y entregarlos en una base. Los
recursos **se desplazan** con probabilidad λ por tick. El plan del agente es una ruta A\*
más una secuencia de subobjetivos; auto-editarse consiste en recalcular un sufijo del plan.

Razones:

1. **Usa el contenido del curso como pieza funcional, no como adorno.** Las sesiones 3 y 4
   cubren búsqueda ciega e informada, y A\* es el planificador que el agente invoca cada vez
   que se edita. La búsqueda no es un capítulo aparte del trabajo: es el motor de la
   replanificación.
2. **El dinamismo es un parámetro limpio.** λ es un único escalar que barre desde entorno
   estático (λ=0) hasta entorno muy dinámico. Sin eso no hay frontera de fase que encontrar.
3. **Escala a horizonte largo.** Muchos subobjetivos encadenados es precisamente el régimen
   donde un plan estático se degrada, que es el fenómeno que motiva OASys.
4. **La observabilidad parcial cae natural.** Un radio de visión `r` modela el set `ignore`
   de OASys sin forzar nada.

### 3.2 Dominio: Mundo de Wumpus auto-editable — **descartado**

La idea era que el agente mantuviera una base de conocimiento lógica, planificara sobre ella
y reescribiera su plan al inferir hechos nuevos. Alinea muy bien con las sesiones 5–6
(lógica, agentes basados en conocimiento, el Wumpus está explícitamente en el temario).

Se descartó por una razón de fondo, no de conveniencia: **Wumpus es un entorno episódico y
pequeño** (típicamente 4×4, episodios de decenas de pasos). El fenómeno que este trabajo
quiere medir —la degradación progresiva de un plan largo bajo un entorno que deriva, y el
*thrashing* de replanificación que aparece cuando el costo de editar compite con el de
actuar— **no se manifiesta en episodios cortos**. En un episodio de 20 pasos, replanificar
tres veces no genera una frontera de fase; genera ruido.

Dicho de otro modo: Wumpus es un excelente banco de pruebas para *representación del
conocimiento*, y un mal banco de pruebas para *economía de la deliberación*. Es buen tema
para otro trabajo, no para este.

### 3.3 Dominio: formación de coaliciones / meta-agentes — **descartado como eje, retenido como extensión**

MESA trae `mesa.experimental.meta_agents`: agentes que se componen en agentes de nivel
superior, con un gestor de membresías. Mapea de forma casi literal la composición sellada de
devices de OASys (`import device <alias>`, que convierte un device completo en una tool
invocable). El ejemplo `alliance_formation` del propio MESA ya hace el andamiaje.

Se descartó como eje porque **cambia la pregunta**. Con coaliciones, la pregunta pasa a ser
"¿cuándo conviene delegar en un sub-agente en vez de hacerlo yo?", que es interesante pero
distinta, y desplaza `cold` vs `hot` a un segundo plano. Dado que la motivación real del
trabajo es una decisión de diseño pendiente en OASys —implementar `run=hot` o no—, mantener
el foco importa más que la amplitud.

Se conserva como **extensión de fase 2**: una vez medida la frontera para un agente, la
pregunta natural siguiente es si un meta-agente supervisor que reparte subobjetivos mueve
esa frontera.

### 3.4 Tratamiento del LLM: oráculo ruidoso — **elegido**

El agente no llama a ningún modelo de lenguaje. El replanificador se modela como un
**oráculo con dos parámetros**:

- **competencia `p`** — probabilidad de que la edición propuesta sea correcta;
- **costo `c`** — ticks de deliberación que consume proponerla.

Con probabilidad `p` devuelve la reparación óptima (A\* sobre el sufijo); con probabilidad
`1−p` devuelve una reparación **degradada pero plausible**: A\* hacia una posición obsoleta
de su creencia, o una ruta con desvío. Que sea plausible —y no ruido aleatorio— es lo que
hace válida la analogía: un LLM que se equivoca no produce basura, produce algo razonable y
equivocado.

### 3.5 Tratamiento del LLM: llamadas reales en el bucle — **descartado**

El diseño experimental requiere del orden de 6 políticas × 5 valores de λ × 4 de `p` × 4 de
`c` × 30 réplicas. Con llamadas reales serían ~10⁵ invocaciones: lento, caro, y **no
reproducible**, que es lo grave. Sin reproducibilidad no hay barrido de parámetros, y sin
barrido se pierde exactamente aquello que MESA aporta sobre un demo de agentes.

Pero hay un argumento más fuerte que el presupuesto, y conviene dejarlo explícito porque es
el aporte metodológico del trabajo:

> Abstraer el LLM como un oráculo `(p, c)` **convierte una propiedad del modelo en un
> parámetro del experimento.**

Con un LLM real solo se puede responder "¿funcionó con este modelo, hoy?". Con el oráculo se
responde "¿a partir de qué competencia mínima vale la pena dejar que un agente se auto-edite,
y cuánto puede costarle cada edición?". La segunda pregunta sobrevive al cambio de modelo;
la primera caduca en seis meses. Y es la segunda la que se puede llevar a una decisión de
ingeniería en OASys.

Queda abierta como validación opcional una calibración posterior: correr N escenarios con un
modelo real, estimar `p̂` empírico, y leer la curva ya construida en ese punto.

---

## 4. Por qué MESA 3.5.1 y no 4.0.0a0

En el repositorio conviven dos versiones: la **3.5.1** instalada en `.venv`, y un checkout
del fuente **4.0.0a0** en `learn/mesa` (no instalado).

Lo que el proyecto necesita y dónde está:

| Necesidad | 3.5.1 | 4.0.0a0 |
|---|---|---|
| Retícula, vecindades, capas de propiedades | `discrete_space/` estable | igual |
| Deliberación que tarda `c` ticks y se puede cancelar | se escribe a mano (ver abajo) | clase `Action` ya hecha |
| Barrido con réplicas y semillas | `batch_run(..., iterations, rng, number_processes)` | `batchrunner` **eliminado** → API nueva `scenarios` + `Store` |
| Meta-agentes (extensión) | `experimental.meta_agents` | `meta_agents/` |
| Los 11 modelos de referencia en `project/` | funcionan | **se rompen** (4.0 eliminó `mesa/examples/`) |

Lo único que 4.0 aporta de verdad es la clase `Action` —una acción con duración, progreso
parcial e interrupción—. Y ahí está el punto: **esa clase es el objeto de estudio de este
trabajo.** "La deliberación es una acción que toma tiempo, tiene progreso parcial y puede ser
interrumpida" no es infraestructura para el proyecto; es la tesis del proyecto sobre por qué
replanificar cuesta. Importarla prehecha esconde el mecanismo que queremos medir; escribirla
es contenido del trabajo, no deuda técnica.

Se consideró también construir la deliberación sobre el simulador de eventos discretos que
3.5.1 sí trae (`mesa.experimental.devs.ABMSimulator`, con `schedule_event_relative` y
`cancel_event`). Se descartó al leer el bucle de `batch_run`, que es literalmente
`while model.running and model.steps < max_steps: model.step()`
(`mesa/batchrunner.py:206`): no sabe nada de colas de eventos, y todo el aparato
experimental del proyecto depende de él. Además una cola de eventos rinde cuando los
eventos son escasos y el tiempo es continuo, y aquí cada agente actúa en cada tick. La
deliberación se implementa entonces como una acción contada en ticks dentro del `step()`
estándar: más simple, testeable, y compatible con el barrido.

A cambio, 4.0 elimina `batch_run` (el barrido habría que reescribirlo contra una API nueva),
rompe los modelos de ejemplo, y es una versión *alpha* sobre un entregable calificado.

La decisión es por mérito técnico. Que además coincida con la versión que se usa en clase
(`content/presentation/2026_2_Intro_Mesa.ipynb` fija 3.5.1) es una consecuencia agradable,
no la razón.

---

## 5. Qué se espera encontrar

La hipótesis, escrita antes de correr nada, para que el resultado sea falsable:

1. Existe un **umbral λ\*** de dinamismo por debajo del cual el agente de lazo abierto
   iguala o supera al que se auto-edita, porque las ediciones gastan presupuesto sin comprar
   información útil.
2. El umbral λ\* **se desplaza hacia arriba cuando `c` crece**: cuanto más cara la
   deliberación, más dinámico tiene que ser el entorno para que valga la pena.
3. Por debajo de cierta competencia mínima `p`, auto-editarse es **peor que no hacerlo**: un
   replanificador malo destruye un plan que era correcto.
4. El agente con gobernanza (presupuesto de ediciones + líneas bloqueadas) supera al de lazo
   cerrado sin restricciones en régimen de alto dinamismo, porque el presupuesto actúa como
   amortiguador contra el *thrashing*.
5. La política `COLD_RESTART` —que modela el clock-edge real de OASys— tiene un costo
   medible frente a `hot`, y ese costo **es el argumento cuantitativo** para implementar
   `run=hot` o para decidir que no vale la pena.

Si (1) resulta falso —si replanificar siempre gana, incluso con λ=0 y `c` alto— la hipótesis
central del trabajo queda refutada, y eso también es un resultado publicable dentro del
informe.
