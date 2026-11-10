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

Vale la pena anotar que lo que se descartó fue el **dominio** y no la representación, pues
tras el Avance 2 la base de conocimiento lógica entró al modelo como una política más
(`KNOWLEDGE_BASED`, [`../docs/roadmap-c4b.md`](../docs/roadmap-c4b.md)), sobre la misma
retícula de horizonte largo, de forma que la pregunta pasó a ser si saber qué se sabe
abarata la deliberación, que sí es una pregunta de este trabajo.

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

---

## 6. Hipótesis de las extensiones

Tras el Avance 2 el modelo creció en tres frentes, cada uno con sus hipótesis escritas en su
documento de trabajo antes de correr el barrido correspondiente
([`../docs/roadmap-c4.md`](../docs/roadmap-c4.md),
[`../docs/roadmap-c4b.md`](../docs/roadmap-c4b.md) y
[`../docs/roadmap-c5.md`](../docs/roadmap-c5.md)). Se resumen aquí con la misma disciplina que
§5: primero lo que se escribió, después el contraste, y todas las cifras son de utilidad neta
media con 30 semillas, `c=5`, `p=0.9` y `r=3` salvo que se diga, con diferencias pareadas por
semilla (± error estándar).

### Escritas antes de correr

1. **Orden de activación:** Sortear en cada tick si el agente actúa antes o después de la
   deriva no cambia la conclusión cualitativa sobre reparar en caliente frente a reiniciar en
   frío (el signo de la diferencia se conserva).
2. **Escasez:** Con recursos escasos los viajes entre recogidas son más largos y el objetivo
   pasa más tiempo expuesto a la deriva, por lo que la reparación debería valer **más** con
   escasez; si sale lo contrario, la explicación tendrá que ver con el costo de oportunidad de
   deliberar cuando sobran objetivos.
3. **Agente basado en conocimiento (KB-2):**
   - **H1:** Con λ>0, `KNOWLEDGE_BASED` (horizonte `"llegada"`) supera a `CLOSED_LOOP`.
   - **H1b:** Alcanza en cada λ a la mejor de `OPEN_LOOP` y `MODEL_BASED`, con la expectativa,
     escrita también de antemano, de que falle a λ=0.5.
   - **H2 (control exacto):** Con visión total y horizonte `"ahora"` es idéntico a
     `CLOSED_LOOP` semilla a semilla.
   - **H3:** Cobrar cada consulta en ticks (`ticks_por_ask > 0`) encoge la ventaja de H1 hasta
     invertirla, con una frontera análoga a la de `c`.
   - **H4 (mecanismo):** El horizonte `"llegada"` cambia reparaciones proactivas por
     replanificaciones forzadas por un fallo y reduce el tiempo deliberando, sin que la
     ganancia neta esté garantizada, porque ambas cuestan `c`.
4. **Agente bayesiano (C5-B):**
   - **HB1:** Con λ>0 y radio finito, `BAYESIAN` supera a `KNOWLEDGE_BASED`, porque el peor
     caso trata igual objetivos casi seguros y casi perdidos.
   - **HB2 (control exacto):** Con visión total y `"ahora"` es idéntico a `CLOSED_LOOP`.
   - **HB3:** El error $|\hat\lambda-\lambda|$ es pequeño y crece cuando hay pocos ensayos
     (`r=1`).
   - **HB4:** A λ=0.5 sigue por debajo de `MODEL_BASED`.
   - **HB5:** El filtro está calibrado: las celdas a las que asigna probabilidad $\approx x$
     contienen al recurso con frecuencia $\approx x$.
5. **Sensibilidad (C5-S):** λ domina la varianza de toda política con plan; `c` explica más
   que `p` en la diferencia `OPEN_LOOP − CLOSED_LOOP`; y `r` mueve mucho el nivel de cada
   política pero poco su diferencia.
6. **Calibración ABC (C5-A):** A partir de la telemetría de un despliegue en frío, λ se
   recupera con precisión, mientras que `p` sale mucho más ancha, porque con `OPEN_LOOP` el
   oráculo solo se consulta tras un fallo y sus errores se confunden con el dinamismo.

### Contraste con los resultados

- **Orden de activación:** Se confirma. Con el orden sorteado, la diferencia entre reparar en
  caliente y en frío conserva el signo en cinco de seis celdas (la excepción es λ=0.5 con
  `c=5`, donde las dos políticas colapsan), y la ventaja de no planificar con λ alto también,
  mientras que la diferencia entre lazo abierto y cerrado cambia de signo en tres de seis, lo
  cual es consistente con que casi empaten y refuerza que no tiene un signo estable.
- **Dinámica (sin hipótesis previa de signo):** Las políticas se separan por **ritmo** y no por
  un evento, pues sus entregas acumuladas crecen con pendientes casi constantes desde el tick
  50, y con λ≥0.25 `MODEL_BASED` va delante desde el principio; la ventaja de reparar en
  caliente sobre el frío a λ=0.1 se abre hacia el tick 130, cuando ya hay trabajo en vuelo
  que perder.
- **Escasez:** **Se refuta en los dos regímenes.** Donde replanificar gana (`c=0`, `p=1`,
  `r=∞`), la ventaja del lazo cerrado sobre el abierto crece con la abundancia (a λ=0.5, de
  +36.7 ± 4.0 con dos recursos a +62.0 ± 5.0 con dieciséis), y en el régimen mixto el lazo
  cerrado no saca ventaja consistente con λ≤0.25 y pierde más con más recursos a λ=0.5. Lo que
  sí crece con la abundancia es la ventaja de no planificar (a λ=0.5, `MODEL_BASED` −
  `OPEN_LOOP` pasa de +13.0 ± 3.1 a +96.0 ± 13.0), que es justamente la explicación por costo de
  oportunidad que se dejó escrita como alternativa.
- **H1:** Se cumple en el signo en todas las celdas, pero solo es significativa con `r=3` y
  λ=0.5 (+21.3 ± 3.8), y desaparece en la ablación `"ahora"`, por lo que la ganancia viene del
  horizonte `"llegada"` (no reparar ante derivas de las que el recurso todavía puede volver) y
  no de la elección de objetivo por peor caso. Con visión total y λ=0.5, en cambio, el
  horizonte lógico no basta para cortar el thrashing (5.0 contra 34.0 del lazo abierto).
- **H1b:** Se cumple a λ=0.1 (+5.3 ± 4.7 sobre `OPEN_LOOP`) y falla a 0.25 (−24.7 ± 9.8) y a
  0.5 (−67 ± 10.5 frente a `MODEL_BASED`), como se había anticipado.
- **H2 y HB2:** Pasan exactos, semilla a semilla, y son lo que permite atribuir cualquier
  diferencia de los barridos al criterio de reparación y no a un error de implementación.
- **H3:** Se confirma con fuerza, pues la ventaja se invierte ya con un tick por consulta
  (−5.3 ± 5.5, −17.3 ± 5.6 y −2.3 ± 2.0 frente a `CLOSED_LOOP` a λ=0.1, 0.25 y 0.5) y llega a
  −32 y −37 puntos con cinco ticks a λ=0.1 y 0.25 (a λ=0.5 el lazo cerrado ya está tan abajo
  que la caída no pasa de −4.7), de forma que **saber más solo compensa si preguntar es casi
  gratis**.
- **H4:** Se confirma. `KNOWLEDGE_BASED` hace más replanificaciones por fallo (7.3, 9.3 y 6.6
  contra 1.6, 1.6 y 1.1 del lazo cerrado a λ=0.1, 0.25 y 0.5) y menos proactivas (2.8, 6.5 y 9.5
  contra 7.7, 9.7 y 13.7), y a λ=0.5 delibera 63 ± 13.6 ticks menos, aunque a λ≤0.25 el ahorro
  de tiempo deliberando no es significativo.
- **HB1:** **Se rechaza.** Con `r=3` y λ=0.5, `BAYESIAN` queda por debajo de `KNOWLEDGE_BASED`
  (−16 ± 4.3), y la causa es la propia regla de reparación, que repara de más: a λ=0.5 hace 16.3
  reparaciones proactivas contra 9.5 de `KNOWLEDGE_BASED` y desperdicia 145.8 ediciones contra
  97.4, porque trata cada reparación como si costara `c` y comprara certeza, cuando el plan
  reparado nace desactualizado y una divergencia nueva puede interrumpirlo. La lógica gana
  justamente por ser más tacaña (solo repara cuando el recurso ya no puede estar ahí). Con la
  regla `"ahora"` (barrido `conocimiento_ahora`), `BAYESIAN` sube de 84.3 a 93.7 a λ=0.1, por
  encima de `KNOWLEDGE_BASED` con `"llegada"` (91.3) pero dentro del ruido, y baja de 15.3 a 9.3
  a λ=0.5, lo cual sitúa el problema en el criterio de reparar y no en el filtro.
- **HB3:** Se confirma: la mediana de $|\hat\lambda-\lambda|$ es 0.083 con `r=1`, 0.020 con
  `r=3` y 0.003 con visión total.
- **HB4:** Se confirma (−83 ± 10.3 frente a `MODEL_BASED` a λ=0.5).
- **HB5:** Se confirma, pues el diagrama de fiabilidad del filtro queda sobre la diagonal
  (`results/figuras/07-fiabilidad-filtro.png`).
- **Sensibilidad:** La primera hipótesis se cumple salvo en `OPEN_LOOP` dentro del barrido
  principal, donde pesa más `c` (η² 0.14 contra 0.12 de λ); la segunda **no** se cumple, ya que
  en la diferencia `OPEN_LOOP − CLOSED_LOOP` todos los η² quedan por debajo de 0.1 y ni `c` ni
  `p` explican casi nada (el ruido entre semillas y mapas domina); y la tercera se cumple a
  medias, porque `r` explica buena parte del nivel del lazo abierto (0.25) pero poco el del
  reinicio en frío (0.05), y en la diferencia llega a 0.079.
- **Calibración ABC:** Se cumple a medias. λ se recupera siempre dentro del intervalo creíble
  del 90 %, aunque con precisión moderada (por ejemplo [0.15, 0.40] con mediana 0.25 para
  λ*=0.25), y `p` no es identificable con esta telemetría, pues su posterior queda casi igual
  al prior. Aun así la recomendación bajo la posterior es nítida en los extremos (lazo cerrado
  en el 81 % de la posterior con λ*=0.1; `MODEL_BASED` en el 100 % con λ*=0.5), y con λ>0.5
  extrapola, porque los barridos llegan a 0.5.

Cabe mencionar, como lectura de conjunto, que las dos arquitecturas nuevas dejan dos
resultados negativos honestos: saber qué se sabe solo paga cuando preguntar es gratis, y
saber cuánto se sabe no paga si la regla de decisión omite un costo del mundo, por lo que en
ninguna de las dos el aporte cambia la conclusión central de que, con dinamismo alto y
deliberación cara, conviene no planificar.
