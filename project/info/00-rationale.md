# 00 — Racional: por qué este proyecto (y por qué no los otros)

> Este documento existe para dejar por escrito **el porqué de cada decisión**, incluidas
> las alternativas que se descartaron y la razón exacta del descarte. Es el registro de
> la fase de planeación; el diseño formal está en [`02-design.md`](02-design.md).

---

## 1. De dónde sale la pregunta

Este proyecto no empieza en el curso, sino en un motor de ejecución agéntica propio, OASys,
en el que un agente puede reescribir el programa que lo ejecuta. Dicho en términos de
agentes, el motor ejecuta un **plan** (un programa editable de instrucciones, con un contador
que indica cuál toca), algunas de cuyas instrucciones invocan a un agente LLM, y ese agente
puede tanto **monitorear el plan** (leerlo y compararlo con lo que observa) como
**reescribirlo** mientras se ejecuta.

La motivación de diseño fue sostener **tareas de horizonte largo**, es decir, procesos que ni
un LLM suelto puede completar (el contexto se degrada) ni un workflow determinista puede
afrontar (el entorno cambia y el flujo es estático), de forma que un agente que reescribe su
propio flujo, en principio, escapa a las dos limitaciones.

**El problema es que esa capacidad nunca se midió**, y tres decisiones de diseño quedaron
resueltas por intuición o delegadas al usuario:

- **Cuándo surte efecto una edición:** En los sistemas que aplican ediciones en la ejecución
  siguiente (reinicio en frío), la edición solo tiene efecto al reiniciar y el trabajo en
  curso se pierde, mientras que la alternativa (reparación en caliente, en la que la edición
  aplica sobre la ejecución en curso) cuesta más construirla y nadie sabía si compensa.
- **Cuántas veces deliberar:** La deliberación se acota con un tope fijo de iteraciones
  (cinco, en la instancia que motivó el trabajo) sin ninguna justificación derivada.
- **Quién autoriza:** Cuando reescribir el plan requiere autorización humana, **un humano**
  es el único freno real contra que el agente entre en un ciclo de reescrituras
  improductivas.

Es decir que hay tres decisiones de diseño importantes y **no existe ninguna métrica que diga
si auto-editarse ayuda o estorba.**

## 2. La observación que convierte esto en un proyecto de IA clásica

Al leer Russell & Norvig con ese motor en mente, aparece que **todo el mecanismo ya está
descrito en la literatura**, con otro vocabulario:

- **Plan editable:** Es un **plan jerárquico** (§11.4).
- **Monitorear el plan:** Es **monitoreo de ejecución**, es decir, comparar el plan contra el
  mundo (§11.5.3).
- **Reescribir el plan:** Es **replanificación**.
- **Alcance de edición:** La porción del plan que el agente no puede modificar corresponde a
  los **invariantes del plan** que la reparación no puede violar.
- **Contexto del agente:** Qué parte del entorno tiene el agente a la vista es
  **observabilidad parcial** (§2.3.2).
- **Reinicio en frío contra reparación en caliente:** Es exactamente **planeación de lazo
  abierto contra lazo cerrado** (§11.5).

La tabla completa está en [`01-mapping.md`](01-mapping.md). Lo relevante aquí es la
consecuencia: si el problema es clásico, entonces **el resultado también debería serlo**, y
la teoría clásica dice algo muy concreto sobre él.

### Por qué la pregunta no es trivial

Uno podría pensar que replanificar siempre es mejor —más información, mejor plan—. No lo es,
y la razón es estructural:

- El **beneficio** de replanificar crece con el dinamismo del entorno. Si nada cambia, el
  plan inicial sigue siendo óptimo y replanificar no compra nada.
- El **costo** de replanificar es aproximadamente constante: deliberar consume tiempo (y,
  con un LLM real, tokens y dinero) durante el cual el agente no actúa.

Beneficio creciente contra costo constante ⇒ **existe un punto de cruce**. Por debajo de
cierto umbral de dinamismo, el agente estático gana; por encima, gana el que se auto-edita.
Y como el costo no es cero, no basta con "replanificar cuando haga falta": existe una
**frecuencia óptima de replanificación**, que es justamente el parámetro que un motor de
ejecución agéntica debería exponer en vez de fijar por decreto el reinicio en frío y un tope
de iteraciones.

Esa frontera es medible. Medirla es el proyecto.

### Pregunta de investigación

> ¿Bajo qué condiciones del entorno un agente que reescribe su propio plan supera a uno con
> plan estático, y a partir de qué costo de reescritura la ventaja se invierte?

Con dos salidas: el entregable del curso, y el argumento cuantitativo para diseñar motores de
ejecución agéntica (cuándo compensa reparar en caliente en vez de reiniciar en frío, y con qué
modelo de costo reemplazar un tope fijo de iteraciones).

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
   donde un plan estático se degrada, que es el fenómeno que motiva el trabajo.
4. **La observabilidad parcial cae natural.** Un radio de visión `r` modela qué parte del
   entorno tiene el agente en su contexto, sin forzar nada.

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
superior, con un gestor de membresías, lo cual mapea de forma casi literal la composición de
agentes (un agente completo usado como herramienta opaca de otro). El ejemplo
`alliance_formation` del propio MESA ya hace el andamiaje.

Se descartó como eje porque **cambia la pregunta**. Con coaliciones, la pregunta pasa a ser
"¿cuándo conviene delegar en un sub-agente en vez de hacerlo yo?", que es interesante pero
distinta, y desplaza el contraste entre reinicio en frío y reparación en caliente a un
segundo plano. Dado que la motivación real del trabajo es una decisión de diseño pendiente
(si un motor de ejecución agéntica debe reparar en caliente o no), mantener el foco importa
más que la amplitud.

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
ingeniería sobre motores de ejecución agéntica.

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
| Los 11 modelos de referencia en `project/templates/` | funcionan | **se rompen** (4.0 eliminó `mesa/examples/`) |

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
(los cuadernos de clase `content/presentation/IA_C1.ipynb` e `IA_C3.ipynb` indican que
funcionan con la 3.5.1) es una consecuencia agradable, no la razón.

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
4. El agente con gobernanza (reparación en caliente con presupuesto `B` de ediciones) supera
   al de lazo cerrado sin restricciones en régimen de alto dinamismo, porque el presupuesto
   actúa como amortiguador contra el *thrashing*.
5. La política `COLD_RESTART` (que modela a los sistemas que aplican ediciones en la
   ejecución siguiente) tiene un costo medible frente a la reparación en caliente, y ese
   costo **es el argumento cuantitativo** para diseñar motores que reparen en caliente o para
   decidir que no vale la pena.

Si (1) resulta falso —si replanificar siempre gana, incluso con λ=0 y `c` alto— la hipótesis
central del trabajo queda refutada, y eso también es un resultado publicable dentro del
informe.

### Contraste con los resultados

Las hipótesis se dejan tal como se escribieron, y su contraste con los datos está en el
cuaderno [`../notebook.ipynb`](../notebook.ipynb) (§4–§9), y conviene leerlo sabiendo que una
versión anterior del modelo dejaba que el lazo abierto replanificara gratis tras un fallo, lo
cual inflaba su ventaja y la de la gobernanza (la regla corregida está en
[`02-design.md`](02-design.md) §3.2). Vale la pena anotarlo con honestidad, de forma resumida y
con las cifras del barrido corregido:

- **Hipótesis (1):** Se cumple solo en su parte trivial. Con λ=0 las políticas que planifican
  empatan, pero con `r=3` el lazo cerrado y el lazo abierto casi empatan en todo el rango (la
  diferencia va de −9 a +26 puntos y en la mayoría de las celdas cae dentro del error
  estándar), de forma que no aparece un umbral λ\* a partir del cual reparar al ver la
  divergencia supere a esperar el fallo. Con visión total y deliberación gratuita sí lo supera
  (control 2), pero con `c=5` vuelve a perder a λ alto.
- **Hipótesis (2):** El costo `c` resultó decisivo, aunque para otra frontera, pues lo que
  desplaza es el punto a partir del cual deja de convenir planificar: Con `c≥2` a λ=0.5, y con
  `c≥5` a λ=0.25, el agente reactivo basado en modelo, que nunca delibera, supera a todas las
  políticas que planifican.
- **Hipótesis (3):** El control de sanidad 3 pasa solo por el signo (85.0 contra 87.5, dentro
  del ruido), y en el barrido de competencia un replanificador mediocre (`p=0.5`) favorece
  incluso al lazo cerrado frente al abierto a λ=0.25, por lo que no se sostiene que un
  replanificador malo destruya un plan correcto en este modelo.
- **Hipótesis (4):** Se cumple solo en parte. A λ=0.5 un presupuesto `B=3` supera al lazo
  cerrado sin acotar (23.7 contra 10.0), pero el mejor presupuesto es cero (27.0, que es el
  lazo abierto), y a λ=0.1 y 0.25 el presupuesto apenas se nota, de forma que acotar funciona
  como «reparar menos» y no como un amortiguador con una cuota óptima.
- **Hipótesis (5):** Se confirma, y es la que mejor sobrevive a la corrección, dado que
  reparar en caliente supera al reinicio en frío desde λ=0.1 (de +16 a +22 puntos con `c`
  entre 2 y 5), aunque con una dependencia en `c` que no resultó monótona.
