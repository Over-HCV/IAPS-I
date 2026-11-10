# Roadmap C4B — Agentes basados en conocimiento en el modelo

Documento de trabajo derivado de [`content/presentation/IA_C4B.ipynb`](../../content/presentation/IA_C4B.ipynb)
(agentes basados en conocimiento, R&N cap. 7: KB-AGENT, lógica proposicional, DPLL, Wumpus y
Buscaminas en Mesa 3.5.1). Funciona igual que [`roadmap-c4.md`](roadmap-c4.md), es decir, por
paquetes acumulables que se marcan `[x]` al completarse, de forma que tras cada uno
`uv run pytest project/tests -q` debe quedar en verde. La ruta conjunta de los dos documentos está
en la sección [Orden](#orden-y-dependencias).

## La tesis

La sesión deja la puerta abierta justo donde vive este proyecto, pues la sección 5 del notebook
advierte que *«en un mundo cambiante habría que indexar los símbolos por el tiempo $t$
(**fluentes**) para que la KB pueda representar cómo cambian las cosas»*, y la Tarea 4 del
Ejercicio 1 pregunta *«¿Qué pasaría con la monotonía si los hoyos se movieran?»*. El modelo es ese
mundo cambiante, dado que sus recursos derivan a una celda vecina transitable con probabilidad λ
por tick (`agents.py:105-111`), las creencias del agente caducan sin que este lo sepa, y
`observar()` solo descarta la creencia del objetivo actual cuando ve vacía su celda
(`agents.py:208-213`), mientras que el resto de creencias obsoletas sigue en la tabla. Un agente
basado en conocimiento aquí no es un ejercicio trasladado sino la unión del cap. 7 (razonamiento
lógico) con el cap. 11 (planificación, monitoreo y reparación), por lo que las dos mitades del
curso se encuentran en un solo experimento, atado además a la pregunta central del proyecto
(cuándo conviene replanificar).

## Mapeo C4B ↔ modelo

| Concepto C4B | Contraparte en el modelo hoy | Gap |
|---|---|---|
| Conocimiento implícito (reglas, `q_values`) frente a explícito (KB) | `Collector.belief: dict[str, Any]` (`agents.py:128`), una tabla recurso → celda | No hay oraciones ni inferencia, y la tabla no guarda **cuándo** se observó cada recurso, así que no se sabe cuán vieja es una creencia |
| `TELL`/`ASK` y el ciclo KB-AGENT | `observar()` escribe la tabla (`agents.py:202-204`) y `_marcar_divergencia()` avisa (`agents.py:215-218`) | Lo único que se «pregunta» es si el objetivo sigue donde se creía; nada se deduce |
| Monotonía: lo deducido nunca caduca | `belief.pop(...)` en `agents.py:212`, `400`, `650` y `687`: actualización no monótona y silenciosa | Requiere símbolos indexados por tiempo (fluentes) |
| Refutar con lo que se ve (la celda sin brisa del Wumpus) | Solo se refuta la creencia **del objetivo** (`agents.py:208-213`); una creencia de otro recurso cuya celda está a la vista y vacía sobrevive, y `MODEL_BASED`, que nunca fija `target`, no refuta ninguna (sale en `agents.py:208`) | Falta `Vacía(c,t)` aplicada a todos los recursos |
| La tercera respuesta: `desconocido` | Al perder el objetivo (por una divergencia o por un fallo del plan) el agente **no deambula**: `_iniciar_deliberacion` re-elige el recurso conocido más cercano por distancia a su creencia (`agents.py:444`, `273-278`), sin importar la antigüedad de esa creencia. Solo renuncia a reparar si no conoce nada o va lleno, y entonces vuelve a la base con la carga o, sin carga, se queda sin plan (`agents.py:445-449`, `519-529`), mientras que solo deambula cuando no tiene plan que seguir (`agents.py:343-347`) | Todo lo que no se ve se trata como verdadero, lo cual es el mecanismo de «replanificar sobre creencia obsoleta», que tras la corrección de la regla de costo (2026-10-09) afecta también al lazo abierto, cuyas replanificaciones tras un fallo pasan por el mismo oráculo |
| Solidez verificada: «0 muertes en celda declarada segura» | El oráculo propone y la propuesta se instala tal cual (`agents.py:460-483`, `584-592`) | Lo verificable no es la reparación (ver [Descartado](#descartado-y-por-qué)) sino la región posible: la celda real del recurso debe estar siempre dentro de ella |
| «Consultas ASK» como métrica de costo | `pasos_deliberando` cuenta solo los ticks del oráculo (`agents.py:549`, `553`) | El costo de inferir no se cobra, por lo que hace falta un parámetro de ticks por consulta |
| La frontera del Buscaminas (se consulta solo lo relevante) | El disco de visión de radio `r` (`agents.py:161-174`) | Es el lugar donde la KB poda, y por eso la poda es barata |
| El dilema de la semilla 6 y la Tarea 5 (contar modelos) | — | La lógica dice dónde **puede** estar un recurso, no dónde **probablemente** está; queda como límite explícito |

## Disciplina de alcance

- **Hipótesis antes de correr:** Se aplica la misma regla de `info/00-rationale.md`, de forma que
  cada paquete trae sus hipótesis falsables escritas antes de ver un solo dato.
- **Barridos nuevos y separados:** Ningún paquete re-corre `principal` ni toca los CSV existentes
  de `results/`, por lo que las políticas nuevas viven en barridos propios, como `gobernanza`.
- **Nivel de conocimiento separado del nivel de implementación (Newell, 1982):** Qué *sabe* el
  agente (oraciones y axiomas) se documenta independiente de cómo se resuelve cada `ASK`, y la
  equivalencia entre ambos niveles se comprueba con una prueba, no se supone.
- **Equidad de costo:** Toda inferencia que el resto de políticas no hace se puede cobrar en
  ticks, del mismo modo que la regla de costo del modelo (corregida el 2026-10-09, igual que la
  del Avance 2) cobra por igual toda reparación, la dispare un fallo del plan o una divergencia
  detectada, de forma que `KNOWLEDGE_BASED` hereda esa regla sin excepciones.

---

## KB-1 — Motor de inferencia proposicional (`project/logica.py`)

**Objetivo.** Se porta el motor de C4B como módulo puro (sin Mesa y sin agentes), que sirve de
fundación a KB-2 y en particular a la prueba que contrasta sus operaciones de conjuntos contra
DPLL. El riesgo es nulo, pues nada del repositorio lo importa todavía.

**Qué se porta** (del notebook, con tipado y docstrings al estilo del proyecto):

- **Constructores de oraciones:** `Not`, `And`, `Or`, `Implies` e `Iff`, representados como
  tuplas de Python igual que en la sesión.
- **Semántica:** `symbols_of`, `pl_true(oracion, modelo)` y `models_of(oracion)`.
- **Decisión por enumeración:** `tt_entails(kb, alpha)`, que es la definición de $\models$ hecha
  código.
- **CNF:** `eliminate_implications`, `push_negations` (De Morgan), `cnf_clauses` (distribución) y
  `to_clauses` con filtro de tautologías.
- **DPLL:** `dpll(clausulas)`, con propagación de unidades y ramificación con retroceso.
- **Base de conocimiento:** `KnowledgeBase` con `tell`, `ask` (por refutación, es decir,
  $KB \wedge \neg\alpha$ insatisfacible), `ask_status` (verdadero / falso / **desconocido**) y un
  contador `n_ask`.
- **Cardinalidad:** `exactly(k, simbolos)`, la restricción «exactamente k de n» del Buscaminas.

**Checklist**

- [x] `project/logica.py` con lo anterior, en español, con referencias a R&N §7.5–7.6 en los docstrings
- [x] `project/tests/test_logica.py`:
  - [x] Ejemplo del libro (R1–R5): $KB \models \neg P_{1,2}$; $KB \models P_{2,2} \vee P_{3,1}$; $P_{2,2}$ → `desconocido`
  - [x] Acuerdo `tt_entails` ≡ `KnowledgeBase.ask` sobre ~100 oraciones aleatorias de ≤ 4 símbolos (semilla fija), como evidencia empírica de solidez y completitud
  - [x] Equivalencia semántica entre una oración y su CNF (ambas evaluadas con `pl_true` en los $2^n$ modelos)
  - [x] DPLL detecta $p \wedge \neg p$, la cláusula unitaria fuerza su valor, y la cadena de implicaciones del notebook ($x_0, x_0{\Rightarrow}x_1, \dots$) se decide rápido frente a la enumeración
  - [x] `exactly(k, n)` produce $\binom{n}{k+1}+\binom{n}{k-1}$ cláusulas, y `exactly(1, [a,b])` deja ambos símbolos en `desconocido` (el 50/50)

**Aceptación.** La suite queda en verde y `import project.logica` no arrastra dependencias de Mesa.

---

## KB-2 — El agente que se pregunta antes de pagar (`Policy.KNOWLEDGE_BASED`)

**Objetivo.** Se añade una séptima arquitectura cuyas creencias son una base de conocimiento con
fluentes, y cuya inferencia **cambia la conducta en el punto exacto donde las demás políticas
pagan**: antes de elegir objetivo y antes de pedir una reparación al oráculo (que cuesta `c`
ticks), el agente se pregunta qué sabe de verdad. La motivación sale de los datos corregidos
(2026-10-09), que la cambiaron respecto de la versión anterior de este documento: con `r=3` y
`c=5` el lazo abierto y el cerrado quedan cerca (86.0 contra 89.0 a λ=0.1 y 47.0 contra 56.0 a
λ=0.25), pero desde λ=0.25 ambos caen por debajo de `MODEL_BASED` (86.0 a λ=0.25 y 98.3 a λ=0.5,
frente a 10.0 del lazo cerrado), que actúa sobre sus creencias sin plan y nunca paga
deliberación (§4 del cuaderno). Lo que hunde a las políticas con plan cuando el entorno cambia
rápido es entonces sobre todo el tiempo de deliberación (a λ=0.5 con `c=5`, `CLOSED_LOOP` pasa
282.2 de sus 400 ticks deliberando), y la creencia obsoleta queda como causa secundaria, visible
en que con `c=0` el lazo abierto sigue arriba del cerrado a λ=0.25 (111.7 contra 86.0). Por eso
este paquete pone a prueba dos palancas a la vez y conviene leerlas por separado: el horizonte
`"llegada"` de la pregunta 3, que ataca el costo al evitar reparaciones ante derivas pequeñas, y
la elección de objetivo por peor caso de la pregunta 2, que ataca la creencia obsoleta.

**Depende de.** KB-1 (solo para la prueba cruzada contra DPLL; la política en sí no lo importa).

### Qué sabe el agente (nivel de conocimiento)

- **Percepción como fluentes:** Cada tick se hace `TELL(Visto(r,c,t))` por cada recurso a la
  vista, y `TELL(Vacía(c,t))` por cada celda a la vista que no contiene al recurso en cuestión
  (en rigor el fluente es $\neg En(r,c,t)$ para cada recurso no visto en `c`, y `Vacía` es la
  abreviatura cuando la celda no tiene ninguno). Recoger un recurso se registra como
  `TELL(Recogido(r,t))`.
- **Monotonía conservada:** Las observaciones nunca se retiran, porque una oración como
  `Visto(r,c,t)` sigue siendo verdadera (lo era *entonces*), de forma que lo que caduca es la
  conclusión «está ahí **ahora**», que ya no se afirma sino que se **deriva**. Es la respuesta
  empírica a la Tarea 4 de C4B, pues la monotonía no se rompe cuando los hoyos se mueven, se indexa.
- **Axioma de deriva (conocimiento de fondo):** Como `Resource.step` mueve el recurso a lo sumo a
  una vecina **no obstáculo** por tick (`agents.py:105-111`), se cumple
  $En(r,c,t) \Rightarrow \bigvee_{c' \in N^{+}(c)} En(r,c',t{+}1)$, con $N^{+}(c)$ la propia celda
  más sus vecinas transitables. La distancia relevante es entonces la **geodésica** (BFS sobre
  celdas transitables) y no la de Manhattan, que sobreestima la región junto a los obstáculos
  (sigue siendo sólida, pero floja). Igual que la regla de la brisa en el Wumpus, el axioma es una
  ley del mundo que el agente conoce, por lo que con λ=0 se instancia como «los recursos no se
  mueven».

### Las tres preguntas `ASK`

1. **¿Dónde puede estar r ahora?** La región posible $R(r,t)$ se mantiene de forma incremental:
   al ver `r` en `c` se fija $R = \{c\}$, y en cada tick sin verlo se expande un paso
   ($R \cup N(R)$) y se le restan las celdas vistas en ese tick sin `r`. Es la estimación de
   estado de R&N §4.4 escrita como axiomas de estado sucesor (§7.7), y su costo es una expansión
   de vecinos por recurso y tick.
2. **¿Qué recurso tengo asegurado?** El objetivo se elige por el **peor caso**, es decir, por
   $\max_{x \in R(r,t)} d(\text{agente}, x)$, y no por la distancia a la creencia. Así una
   creencia vieja, cuya región ya es ancha, pierde frente a una observación reciente un poco más
   lejana, lo cual ataca directamente el hueco de la tabla (hoy se elige por distancia a la
   creencia sin importar su antigüedad, `agents.py:273-278`). El término de distancia usa el mismo
   `_dist` de Manhattan que el resto de políticas (`agents.py:693-700`) para que el control H2 sea
   exacto, y la regla sustituye a las tres elecciones ávidas que hoy existen (`agents.py:278`,
   `396`, `507`). Solo son candidatos los recursos cuya última celda observada sigue dentro de su
   región, y el destino del plan sigue siendo esa celda, por lo que lo único que cambia es el
   orden en que se persiguen.
3. **¿Sigue siendo ejecutable mi plan?** La respuesta tiene tres valores (válido / inválido /
   desconocido) y solo *inválido* dispara una reparación, mientras que *desconocido* mantiene el
   plan. Se evalúa en los mismos eventos en que hoy se marca la divergencia (`agents.py:205-206`
   y `211-213`), justo antes de pagar `c` (`agents.py:336-339` y `542-551`), con dos horizontes
   posibles (parámetro `horizonte_validez`, leído solo por esta política, del mismo modo que
   `presupuesto` solo lo lee `GOVERNED` en `agents.py:137-139`):
   - **`"ahora"`:** El plan es inválido si su celda objetivo ya no está en $R(r,t)$. Vale la pena
     anotarlo porque es un resultado en sí mismo: con este horizonte la pregunta reproduce
     **exactamente** las dos reglas de detección actuales (objetivo visto en otro sitio y celda
     creída vista vacía), es decir, el monitor de hoy es la lectura a nivel de implementación de
     esta consulta.
   - **`"llegada"`:** Si quedan `k` líneas `GOTO` antes del `PICK` (una línea por tick,
     `agents.py:611-633`), el plan es inválido solo si la celda objetivo cae fuera de la expansión
     de `k` pasos de $R(r,t)$, es decir, si el recurso ya no puede estar ahí cuando el agente
     llegue. Es el horizonte que cambia la conducta, pues un recurso visible que se desplazó una
     celda ya no dispara una reparación de `c` ticks mientras todavía pueda volver, lo cual apunta
     directamente al thrashing que midieron el Avance 2 y la §8 del cuaderno.

### Por qué no la «intersección de bolas» ni el «punto más cercano de la región»

- **La intersección es redundante:** Con dos avistamientos $(c_1,t_1)$ y $(c_2,t_2)$, $t_1<t_2$,
  el axioma obliga a $d(c_1,c_2) \le t_2-t_1$, de modo que por desigualdad triangular la bola de
  la última observación, de radio $t-t_2$, está contenida en la de la anterior, de radio $t-t_1$.
  La intersección de todas las bolas es siempre la última, y lo que de verdad poda son las celdas
  vistas sin el recurso **después** de esa observación, así como los obstáculos si la distancia
  es geodésica. Cabe mencionar además que restar a la bola *todas* las celdas vistas vacías desde
  la última observación no es sólido, pues el recurso pudo entrar en una de ellas después de que
  se viera vacía, por lo que la poda tiene que hacerse tick a tick como en la pregunta 1.
- **El punto más cercano es degenerado:** El agente descubre la pérdida porque caminó hasta ver
  la celda vieja (`agents.py:211`), así que ya está dentro de la bola. Sin poda, el punto más
  cercano de la región es su propia celda; con poda, es cualquier celda en el borde de su disco
  de visión, elegida por desempate entre muchas equidistantes, lo cual no es más que deambular
  con otro nombre. Por eso la pregunta 2 usa la región para **ordenar** objetivos y no para
  inventar destinos.

### Nivel de implementación y costo

- **Operaciones de conjuntos, no cláusulas:** Las tres consultas se resuelven con conjuntos de
  celdas sobre la retícula (expansión, resta y pertenencia), ya que codificar
  $En(r,c,t)$ para cada recurso, celda y tick explotaría en cláusulas. La conexión con el curso se
  conserva con una prueba que, en retículas pequeñas, codifica las mismas observaciones y el
  axioma de deriva con `exactly(1, ...)` por tick en `project/logica.py`, y comprueba que DPLL
  responde `falso` exactamente en las celdas fuera de $R(r,t)$ y `desconocido` dentro.
- **Costo de preguntar:** El parámetro `ticks_por_ask` (por defecto 0) cobra en ticks quieto cada
  consulta 2 o 3 que se hace en un evento de divergencia, y esos ticks suman a
  `pasos_deliberando`, de forma que entran en la utilidad neta igual que los del oráculo. La
  actualización de la región (pregunta 1) es monitoreo por tick y queda gratuita, igual que hoy
  lo es `observar()` para todas las políticas (`agents.py:224`).
- **Métrica visible:** El reporter `n_consultas` cuenta las consultas 2 y 3, del mismo modo que el
  notebook reporta las «Consultas ASK resueltas con DPLL».

### Hipótesis (antes de correr)

Las hipótesis se reescribieron tras la corrección de la regla de costo (2026-10-09), pues la
versión anterior medía a `KNOWLEDGE_BASED` contra una brecha de dominancia del lazo abierto que
resultó ser en buena parte un artefacto, y dejaba fuera a `MODEL_BASED`, que hoy es la vara más
exigente.

- **H1 (contra el lazo cerrado):** Con $r \in \{1, 3\}$ y λ>0, `KNOWLEDGE_BASED` (horizonte
  `"llegada"`) supera a `CLOSED_LOOP` en `utilidad_neta`, comparando por pares de semilla. Ya no
  se mide como la fracción $(KB - CL)/(OL - CL)$ de la distancia con `OPEN_LOOP`, porque con
  `r=3` y `c=5` esa distancia es pequeña y cambia de signo (el cerrado va arriba a λ=0.1 y 0.25,
  89.0 contra 86.0 y 56.0 contra 47.0, y abajo a λ=0.5, 10.0 contra 27.0), de modo que el
  cociente se vuelve inestable justo donde importa. Con `r=1` las políticas con plan casi no se
  separan (47.9 contra 48.0 promediando λ, §7 del cuaderno), por lo que H1 tiene poco margen ahí.
- **H1b (contra la mejor política sin reparación proactiva):** Con `r=3`, `KNOWLEDGE_BASED`
  alcanza en cada λ a la mejor de `OPEN_LOOP` y `MODEL_BASED`. Se deja escrito de antemano qué se
  espera: a λ=0.1 la vara es alcanzable (72.0 de `MODEL_BASED` frente a 86.0 y 89.0 de las
  políticas con plan), a λ=0.25 alcanzar 86.0 sería el resultado fuerte del paquete, y a λ=0.5 lo
  más probable es que H1b falle (98.3 de `MODEL_BASED` frente a 27.0 del mejor planificador),
  porque el horizonte `"llegada"` evita reparaciones proactivas pero no las replanificaciones
  pagadas tras cada fallo. Que falle ahí no invalida el paquete, ya que responde la pregunta de
  si saber más compensa frente a no planificar.
- **H2 (control exacto):** Con `r=∞` y horizonte `"ahora"`, la región de cada recurso es un punto
  en cada decisión (el agente observa antes de que los recursos deriven, `model.py:255-260`), el
  peor caso coincide con la distancia a la creencia y la consulta 3 coincide con el monitor
  actual, por lo que `KNOWLEDGE_BASED` ≡ `CLOSED_LOOP` semilla a semilla, incluidas las
  replanificaciones por fallo, que hereda tal cual. Con λ=0 lo mismo vale en todo radio, y por el
  control 1 del cuaderno también ≡ `OPEN_LOOP`.
- **H3:** Con `ticks_por_ask > 0` la ventaja de H1 se encoge y aparece un valor a partir del cual
  se invierte, es decir, una frontera análoga a la de `c`.
- **H4 (mecanismo):** Frente a `CLOSED_LOOP`, el horizonte `"llegada"` cambia reparaciones
  proactivas por replanificaciones forzadas por un fallo (más `n_ediciones_por_fallo`, menos
  `n_ediciones` proactivas) y reduce `pasos_deliberando`. Como ambas cuestan `c`, la ganancia neta
  no está garantizada: el plan que se mantuvo por `desconocido` y luego falla se paga igual, solo
  que más tarde y tras caminar hasta la celda vacía, por lo que H1 solo se sostiene si las
  reparaciones evitadas superan a los fallos añadidos.

Vale la pena anotar dos amenazas antes de correr. La primera es que con `r=∞` y horizonte
`"llegada"` la equivalencia de H2 **no** vale por diseño, ya que el agente deja de reparar ante
derivas pequeñas de un objetivo visible, y esa comparación es justo la que dice si el criterio
lógico corta el thrashing, con la salvedad de que la vara no es solo `CLOSED_LOOP` sino también
`GOVERNED` (a λ=0.5 y `r=3`, `B=3` rinde 23.7 contra 10.0 del cerrado, pero `B=0`, que es
exactamente `OPEN_LOOP`, rinde 27.0, §8 del cuaderno), de modo que cortar el thrashing por la vía
lógica tiene que rendir más que simplemente no reparar de forma proactiva. La segunda es que la
asimetría que la versión anterior de este documento señalaba aquí (replanificación gratuita tras
un fallo) ya no existe, pues `_fallar_tarea` solo deja pendiente la replanificación
(`agents.py:666-689`) y `_paso_planificado` la paga en el tick siguiente con
`_iniciar_deliberacion(por_fallo=True)` (`agents.py:331-335`), pero el intercambio que describe
H4 sigue confundiendo las dos palancas del paquete. Por eso se corre también el horizonte
`"ahora"` en radios finitos, que no cambia *cuándo* se repara y aísla el aporte de las preguntas
1 y 2.

### Límite honesto

La lógica dice dónde **puede** estar un recurso, no dónde **probablemente** está, de modo que el
peor caso trata igual una celda en el centro de la región que una en su borde, y el horizonte
`"llegada"` puede mantener un plan que es posible pero improbable. Es el mismo límite del dilema
de la semilla 6 en C4B, donde la KB responde `desconocido` para todas las candidatas aunque una
explique ambas brisas en 4 de 5 modelos, y la sesión lo deja para la Tarea 5 (contar modelos).
Aquí la extensión natural, con λ conocido, es probabilística: la probabilidad de que el recurso
siga en su última celda tras $\Delta t$ ticks es al menos $(1-\lambda)^{\Delta t}$, y la
distribución sobre la región sale de propagar la caminata aleatoria (R&N cap. 12–13). Queda fuera
de alcance y así debe decirlo el cuaderno.

**Checklist**

- [x] `Policy.KNOWLEDGE_BASED` en `agents.py` (con `planifica` y `replanifica` verdaderos), y una nota en `info/02-design.md` §3 que diga que hereda la reparación en caliente de `CLOSED_LOOP`
- [x] KB del agente: observaciones `Visto`/`Vacía`/`Recogido` con su tick, y región $R(r,t)$ incremental por recurso
- [x] Pregunta 2 (peor caso) en las tres elecciones de objetivo (`agents.py:278`, `396`, `507`)
- [x] Pregunta 3 con `horizonte_validez ∈ {"ahora", "llegada"}`, interceptando la divergencia antes de `_iniciar_deliberacion` (`agents.py:336-339`) y antes de interrumpir una deliberación (`agents.py:542-551`)
- [x] Parámetros `horizonte_validez` y `ticks_por_ask` en `OASysWorld.__init__`; reporter `n_consultas` en `REPORTERS` (`model.py:272`)
- [x] `project/tests/test_conocimiento.py`:
  - [x] Sin observaciones, tras `k` ticks la región es la bola geodésica de radio `k`, y junto a una pared es estrictamente menor que la de Manhattan
  - [x] Una celda vista vacía en $t'$ se excluye en $t'$ pero vuelve a ser posible después si es alcanzable (la poda ingenua «bola menos vacías» falla esta prueba)
  - [x] La bola del segundo avistamiento está contenida en la del primero (propiedad, con semillas)
  - [x] **Solidez:** en N corridas con λ>0 y `r` finito, la celda real de cada recurso rastreado está en su región en todo tick (la versión honesta del «0 muertes en celda declarada segura»)
  - [x] Prueba cruzada con DPLL en una retícula de 4×4 y 3 ticks: `falso` fuera de la región, `desconocido` dentro
  - [x] Horizonte `"ahora"` dispara exactamente en los mismos ticks que las reglas de `agents.py:205` y `211`
  - [x] H2: con `r=None` y `"ahora"`, métricas idénticas a `CLOSED_LOOP` en varias semillas y λ>0; con λ=0, idénticas en todo radio
- [x] Barridos (c=5, p=0.9, `BASE`, 30 semillas):
  - [x] `SWEEPS["conocimiento"]`: `{MODEL_BASED, OPEN_LOOP, CLOSED_LOOP, KNOWLEDGE_BASED}` × λ {0.0, 0.1, 0.25, 0.5} × radio {1, 3, None}, horizonte `"llegada"`, `ticks_por_ask=0` → 4×4×3×30 = **1.440 corridas** (las filas de `OPEN_LOOP` y `CLOSED_LOOP` deben reproducir `observabilidad.csv` exactamente y las de `MODEL_BASED` con `r=3` las de `principal.csv`, lo cual sirve de regresión; `MODEL_BASED` entra porque es la vara de H1b y `observabilidad` no la barre en radio)
  - [x] `SWEEPS["conocimiento_ahora"]`: `KNOWLEDGE_BASED` con horizonte `"ahora"` × λ × radio → 4×3×30 = **360 corridas** (H2 y la ablación)
  - [x] `SWEEPS["conocimiento_costo"]`: `KNOWLEDGE_BASED` con `"llegada"` × `ticks_por_ask` {1, 2, 5} × λ {0.1, 0.25, 0.5}, `r=3` → 3×3×30 = **270 corridas** (H3)
  - [x] Total **2.070 corridas**; actualizar la tabla de barridos de `project/README.md`
- [x] `fig_conocimiento()` en `analysis.py` reutilizando `lineas` (`analysis.py:337`): x=λ, serie=política, faceta=radio
- [ ] Sección del cuaderno con hipótesis, figura, veredicto, la lectura de H1 y H1b frente a la ablación `"ahora"`, el desglose de H4 (`n_ediciones_por_fallo` frente a las proactivas, y `pasos_deliberando`), el límite honesto y la respuesta a la Tarea 4 de C4B

**Resultado (2026-11-06).** Con `BAYESIAN` de [`roadmap-c5.md`](roadmap-c5.md) incluido, los barridos
quedaron en 1.800 (`conocimiento`), 720 (`conocimiento_ahora`) y 540 (`conocimiento_costo`)
corridas en vez de 1.440/360/270. Controles exactos: H2 pasa semilla a semilla (con `r=∞` y
`"ahora"`, y con λ=0 en todo radio), la región contiene la celda real en todo tick, y DPLL en
4×4 responde `falso` fuera y `desconocido` dentro. Las filas OL/CL/MB del barrido reproducen
`observabilidad.csv` y `principal.csv` (0 distintas). Veredictos, por pares de semilla con `r=3`:
H1 tiene el signo esperado en todas las celdas pero solo es significativa a λ=0.5 (+21.3 ± 3.8
sobre `CLOSED_LOOP`), y desaparece en la ablación `"ahora"`, de modo que la ganancia viene del
horizonte `"llegada"`; H1b se cumple a λ=0.1 (+5.3 ± 4.7 sobre `OPEN_LOOP`) y falla a 0.25 y
0.5 frente a `MODEL_BASED` (−24.7 y −67); H3 se confirma con fuerza (la ventaja ya se invierte
con un tick por consulta); H4 se confirma (más replanificaciones por fallo, menos proactivas y
63 ± 13.6 ticks menos deliberando a λ=0.5). Desviaciones de implementación: `"ahora"` compara
contra la celda creída recién refutada (la del `PICK` rompía H2 por desincronización entre plan
y creencia); la creencia refutada se conserva y se notifica una sola vez; los barridos
originales quedan congelados a las seis políticas, y `model.py` cuenta las derivas entre
observaciones (con `orden_aleatorio` pueden ser 0, 1 o 2).

**Aceptación.** H2 pasa exacto (semilla a semilla), la prueba de solidez y la prueba cruzada con
DPLL pasan, y H1, H1b, H3 y H4 se evalúan con 30 réplicas y banda de error, diciendo
explícitamente qué parte de la diferencia sobrevive en la ablación `"ahora"` y, si H1b falla,
en qué λ lo hace.

---

## KB-3 — Capa visual de la región posible (extra de presentación)

**Objetivo.** La «curva de conocimiento» del Wumpus no discrimina entre arquitecturas en este
modelo (las creencias de `CLOSED_LOOP` tampoco expiran salvo al ver, así que la fracción de
recursos con ubicación conocida no distingue a nadie), por lo que se descarta como experimento y
se conserva lo que sí comunica: **dibujar la región posible** de cada recurso en la animación,
junto al rombo de la creencia, de forma que se vea crecer mientras el recurso no está a la vista,
recortarse por el disco de visión y colapsar a un punto al volver a verlo.

**Depende de.** KB-2. No lleva barrido ni hipótesis.

**Checklist**

- [x] Campo `regiones: dict[str, tuple[coord, ...]]` en `Frame` (`animacion.py:78`), lleno solo para `KNOWLEDGE_BASED` en `_capturar` (`animacion.py:202`)
- [x] `_panel_grid` (`animacion.py:330`) sombrea la región con alfa bajo, en el color de la creencia, y la serie se dibuja aunque vaya vacía para que la leyenda no salte
- [x] Test: el panel dibuja la región sin error y la celda real cae dentro (reutiliza la prueba de solidez de KB-2)
- [ ] Celda del cuaderno con `anim.mostrar(policy="KNOWLEDGE_BASED", ...)` y una lectura de dos líneas

**Resultado (2026-11-06).** Hecho para las dos políticas: región plana para
`KNOWLEDGE_BASED` y mapa de calor para `BAYESIAN`, en naranja (el gris de la creencia no se
distinguía de los obstáculos), empujadas por las derivas pendientes porque el agente observa
antes de la deriva de cada tick. Tiras exportadas en `results/animaciones/tira-knowledge-based.png`
y `tira-bayesian.png` (`rng=3`, λ=0.25, `c=5`, `r=3`).

**Aceptación.** La película se entiende sin narración: dónde puede estar cada recurso y por qué
el agente eligió el que eligió.

---

## Descartado y por qué

### KB-4 — Reparación verificada

La idea era que la KB validara cada propuesta del oráculo antes de instalarla, trasladando la
solidez verificada de C4B, con tres chequeos: [a] la ruta no atraviesa celdas que se sabe
bloqueadas, [b] el objetivo cae dentro de la región posible y [c] la continuación no depende de
recursos ya recogidos. Se descarta porque **no tiene potencia por construcción**, es decir, el
oráculo no produce los errores que los chequeos podrían refutar:

- **[a] nunca dispara:** El oráculo traza toda ruta con `astar` sobre `passable`
  (`oracle.py:119-128`), y el modelo le pasa ese predicado y las celdas libres
  (`model.py:96-104`), mientras que el punto intermedio del desvío también se filtra con `_ok`
  (`oracle.py:161`, `211-213`). El desvío (`oracle.py:178-209`) es una ruta válida y transitable,
  solo más larga.
- **[b] no rechaza el objetivo obsoleto:** El fallo `STALE_TARGET` construye la ruta hacia
  `believed_goal` (`oracle.py:233-235` y `239-245`), que es la creencia del agente
  (`agents.py:459`, `466`), es decir, la última observación, que por construcción está dentro de
  la región posible. Cabe una excepción: si el objetivo re-elegido en `agents.py:444` es un
  recurso cuya celda creída está a la vista y vacía (posible porque solo se refuta la creencia del
  objetivo, `agents.py:208-213`), [b] sí lo rechazaría, pero ese es un defecto de la elección de
  objetivo que KB-2 corrige antes y más barato con `Vacía(c,t)`.
- **[c] no puede fallar:** La cola sale de `_cadena_desde`, que excluye el objetivo
  (`agents.py:468`, `497-501`) y parte de `_conocidos`, que excluye lo que se lleva
  (`agents.py:270`), mientras que lo recogido además sale de la tabla (`agents.py:650`).

Con eso se esperaría H1 nula y H2 trivial, por lo que el barrido de 720 corridas no compraría
nada. **Condición de reactivación:** Se retoma solo si el oráculo gana un modo de fallo que una KB
pueda refutar, por ejemplo rutas que atraviesan obstáculos u objetivos fuera de toda región
posible, y en ese caso el diseño original (parámetro `verificacion`, contador `n_rechazos`,
comparación pareada por semilla) sigue sirviendo.

---

## Orden y dependencias

Los dos roadmaps se recorren como **una sola ruta**:

```
1 (orden aleatorio) → 3 (curvas temporales) → KB-1 (motor) → KB-2 (KNOWLEDGE_BASED) → 4 (escasez) → 5 (narrativa)
extras de presentación, en cualquier momento tras sus dependencias:  2 (tira)   KB-2 ──→ KB-3 (capa de región)
```

El Paquete 1 va primero porque es el único que toca el orden del ciclo en `model.py` y conviene
aislar su regresión, y el 3 va después porque su runner por tick sirve para leer *cuándo* se
separan `KNOWLEDGE_BASED` y `CLOSED_LOOP`. KB-1 no toca nada del experimento y prepara la prueba
cruzada de KB-2, que es el aporte con hipótesis propia de este documento. El 4 va tras KB-2 para
poder incluir la política nueva si H1 se sostiene, y el 5 cierra porque su narrativa cita las
figuras de 3, 4 y KB-2. El 2 y KB-3 son material para la presentación y no bloquean nada.

## Referencias

- Sesión: `content/presentation/IA_C4B.ipynb` (KB-AGENT, `TELL`/`ASK`, entailment, CNF+DPLL,
  Wumpus y el dilema de la semilla 6, Buscaminas, `exactly(k)`, Tareas 4 y 5).
- Russell, S. y Norvig, P. (2020), *AIMA* 4.ª ed., §4.4 (estados de creencia), cap. 7 (agentes
  lógicos, en particular §7.7 sobre fluentes), §11.5 (reparación de planes) y cap. 12–13
  (la extensión probabilística).
- Newell, A. (1982). The knowledge level. *Artificial Intelligence*, 18(1), 87–127.
- Davis, M., Logemann, G. y Loveland, D. (1962). A machine program for theorem-proving.
  *Communications of the ACM*, 5(7), 394–397.
- Kaye, R. (2000). Minesweeper is NP-complete. *The Mathematical Intelligencer*, 22(2), 9–15.
