# 02 — Diseño formal del modelo

> Especificación ejecutable del experimento. El porqué de las decisiones está en
> [`00-rationale.md`](00-rationale.md); la traducción conceptual, en
> [`01-mapping.md`](01-mapping.md).

---

## 1. La tarea: PEAS

Siguiendo R&N §2.3.1, la especificación del entorno de tarea.

| Componente | Especificación |
|---|---|
| **P** — Medida de rendimiento | Recursos entregados en la base antes de `T_max`, penalizado por el tiempo dedicado a deliberar. Formalizado en §4 |
| **E** — Entorno | Retícula `N×N` de von Neumann con obstáculos fijos; `K` recursos que se desplazan y se reponen al entregarse; una base de entrega en posición fija |
| **A** — Actuadores | `GOTO(celda)` un paso por tick; `PICK(recurso)`; `DELIVER()`; `DELIBERAR()` — que consume `c` ticks y produce un plan nuevo —; y, solo para las dos políticas que infieren (§3.4), `ASK` a su KB o a su filtro, que cuesta `ticks_por_ask` ticks quieto (0 por defecto) |
| **S** — Sensores | Contenido de las celdas dentro del radio `r` de la posición actual. Fuera de `r`, el agente solo tiene su creencia |

**Sobre `DELIBERAR` como actuador:** es la decisión de diseño central. Deliberar no es un
acto instantáneo entre ticks, sino **una acción del mismo tipo que moverse**, que ocupa
tiempo del reloj durante el cual el mundo sigue cambiando. Sin esto no hay costo que medir y
la pregunta del trabajo se vuelve trivial.

## 2. Clasificación del entorno (R&N §2.3.2)

| Propiedad | Valor | Cómo se controla |
|---|---|---|
| Observable | **Parcialmente** (totalmente si `r = ∞`) | Parámetro `r`, que modela qué parte del entorno tiene el agente en su contexto |
| Determinista | **Estocástico** | El movimiento de recursos (λ) y la competencia del oráculo (`p`) |
| Episódico | **Secuencial** | Las decisiones tempranas condicionan todo el resto — es el régimen de horizonte largo |
| Estático | **Dinámico** | Los recursos se mueven **mientras el agente delibera**. Esta es la propiedad que hace costosa la deliberación |
| Discreto | **Discreto** | Retícula y ticks enteros |
| Agentes | **Un agente** (multi-agente en extensión) | — |
| Conocido | **Conocido** | Las reglas del entorno se conocen; lo que no se conoce es el *estado*. La excepción es `BAYESIAN`, que conoce la forma de la deriva pero no λ, y lo aprende mirando (§3.4) |

El caso λ=0, r=∞ colapsa a un entorno estático y totalmente observable: ahí la planeación de
lazo abierto es óptima por construcción, y sirve como control de sanidad del experimento.

**El orden de activación es un parámetro, no un supuesto.** Por defecto el recolector actúa
en cada tick antes de que los recursos deriven, y con `orden_aleatorio=True` el orden se
sortea tick a tick con el generador del modelo (reproducible), de forma que entre dos
observaciones del agente puede haber cero, una o dos derivas (el modelo las cuenta en
`derivas`); el barrido `orden` (§5) comprueba que las conclusiones cualitativas no dependen
de esa elección.

## 3. Arquitecturas de agente

Todas las políticas comparten un mismo cuerpo de agente (`Collector` en `agents.py`), y lo
único que cambia entre ellas es la enumeración `Policy`, es decir, cómo reacciona cada una a
una divergencia entre el plan y el mundo. Entre las seis que planifican, además, la
diferencia es solo **cuándo** invocan al replanificador, no cuánto les cuesta, pues todas lo
pagan al mismo precio (§3.2). Las tres primeras siguen la taxonomía de R&N §2.4,
que es el RAE #1 de la asignatura; las tres siguientes extienden al agente basado en
objetivos con las variantes de replanificación de §11.5; y las dos últimas, que se añadieron
después del Avance 2 (`docs/roadmap-c4b.md` y `docs/roadmap-c5.md`), reparan en caliente
como (5) pero antes de elegir objetivo y antes de pagar una reparación se preguntan qué saben
de verdad, con lógica (R&N cap. 7) o con probabilidad (R&N cap. 14).

| # | Política | Descripción | R&N | Cuándo aplica la edición |
|---|---|---|---|---|
| 1 | `REFLEX` | Se mueve con avidez hacia el recurso visible más cercano, con un paso aleatorio de probabilidad ε para escapar de mínimos locales. Sin plan ni memoria | §2.4.2 reflejo simple | — (línea base, no planifica) |
| 2 | `MODEL_BASED` | Mantiene creencias sobre dónde están los recursos y persigue el más cercano según ellas; sigue siendo reactivo, sin plan explícito | §2.4.3 reflejo basado en modelo | — (no planifica) |
| 3 | `OPEN_LOOP` | Calcula un plan A\* y lo ejecuta sin realimentación, ignorando las divergencias hasta que el plan falla (un `PICK` sin recurso); solo entonces replanifica, pagando `c` ticks con el mismo replanificador que las demás | §2.4.4 basado en objetivos, lazo abierto | Al fallar, en caliente: conserva la carga |
| 4 | `COLD_RESTART` | Al detectar una divergencia (o al fallar el plan) delibera `c` ticks, y luego **suelta la carga** y arranca con el plan nuevo desde cero | lazo abierto con reinicio | En frío: en la ejecución siguiente, y el trabajo en curso se pierde |
| 5 | `CLOSED_LOOP` | Monitorea, y al divergir repara el sufijo del plan en sitio pagando `c` ticks; si aun así el plan falla, replanifica igual que (3) | §11.5.3 planeación en línea | En caliente: sobre la ejecución en curso |
| 6 | `GOVERNED` | Como (5), pero con un presupuesto de `B` reparaciones proactivas; agotado el presupuesto deja de reparar al divergir y se comporta exactamente como (3) | lazo cerrado con recursos acotados | En caliente, con presupuesto `B` |
| 7 | `KNOWLEDGE_BASED` | Como (5), pero sus creencias son una base de conocimiento con fluentes y una región posible por recurso; elige objetivo por el peor caso sobre la región y ante una divergencia solo repara si la KB deduce que el plan es *inválido* | §7.7 agente basado en conocimiento, §4.4 estimación de estado | En caliente, heredada de (5), solo si el plan es inválido |
| 8 | `BAYESIAN` | Como (7), con un filtro de probabilidad por recurso en vez de una región y λ aprendido en vez de dado; elige objetivo por costo esperado y repara por utilidad esperada | §14.2 filtrado, §16.1 utilidad esperada | En caliente, heredada de (5), solo si reparar cuesta menos en esperanza |

**Alcance de edición, común a toda política que planifica.** Todo plan termina con un
`DELIVER` marcado como bloqueado (`locked=True`), sea cual sea la política, de forma que la
entrega comprometida queda fuera del alcance de edición del agente y ninguna reparación puede
eliminarla. Cabe mencionar que esto no distingue a `GOVERNED` de `CLOSED_LOOP`, pues la única
diferencia entre ambas es el presupuesto `B`, que acota solo las reparaciones disparadas por
una divergencia (las forzadas por un fallo no se pueden evitar y no lo consumen). De ahí un
control exacto: con `B = 0`, `GOVERNED` es idéntica a `OPEN_LOOP`, semilla a semilla (§9).

**Por qué (4) merece ser una política y no una nota al pie.** `COLD_RESTART` modela a los
sistemas que aplican ediciones en la ejecución siguiente, en los que la edición del agente
solo surte efecto al reiniciar y el progreso de la ejecución actual se pierde. Su diferencia
de rendimiento contra (5) **es** el valor cuantificado de reparar en caliente en lugar de
reiniciar en frío, y ese número es el argumento cuantitativo para diseñar motores de
ejecución agéntica que reparen en caliente (o para decidir que no vale la pena).

### 3.1 Niveles de monitoreo (R&N §11.5.3)

R&N distingue tres niveles a los que un agente puede detectar que su plan ya no sirve, y en
este modelo los tres aparecen, aunque no con el mismo papel.

| Nivel | Detecta | Implementación |
|---|---|---|
| **De acción** | La precondición de la línea actual no se cumple | `PICK(A)` pero `A` no está en la celda; es como lo descubre `OPEN_LOOP`, que entonces replanifica pagando `c` ticks (§3.2) |
| **De plan** | El resto del plan ya no puede tener éxito, aunque la línea actual sí | `Collector.observar()` ve el objetivo en otra celda, o ve vacía la celda donde creía que estaba, y marca la divergencia que dispara la reparación |
| **De objetivo** | Conviene perseguir otra meta | Al iniciar una reparación se reelige como objetivo el recurso conocido más cercano, en vez de reparar a ciegas la ruta hacia uno que ya no se ve |

Vale la pena anotar que el monitoreo de objetivo solo actúa en el momento de reparar y no
dispara reparaciones por sí mismo (un recurso más cercano que entra en el radio no
interrumpe el plan), por lo que la profundidad del monitoreo como variable experimental
(monitorear más profundo detecta antes, pero dispara más ediciones) se deja como extensión.

**Sobre por qué la ceguera casi no aparece.** El diseño inicial esperaba que un radio
pequeño hiciera al agente *perderse* divergencias. Casi no ocurre, y por una razón
estructural: el plan lleva al agente precisamente a la celda donde creía que estaba el
recurso, así que tarde o temprano descubre que no está. Lo que cambia con el radio no es
*si* se entera sino **cuándo**, y mientras tanto camina hacia el sitio equivocado. De ahí
que la métrica que importa sea la latencia y no la fracción de perdidas.

### 3.2 Regla de costo

Toda política que planifica usa **el mismo replanificador al mismo precio**, y la regla
que decide qué se paga es la siguiente.

- **Los planes de rutina son gratuitos.** El plan inicial y el que sigue a una entrega sin
  que nada haya fallado se construyen con A\* determinista sobre la creencia, sin pasar por
  el oráculo ni consumir ticks: equivalen al programa que se le entrega de antemano al
  agente.
- **Toda replanificación de reparación se paga.** La dispare un **fallo del plan** (el
  agente llega a la celda y el recurso no está, o el plan ya no puede ejecutarse) o una
  **divergencia detectada** por el monitoreo, pasa por el oráculo con competencia `p` y
  consume `c` ticks de deliberación (más `κ` por tick en la utilidad neta). Se aplica en
  caliente, salvo en `COLD_RESTART`, que la aplica en frío y suelta la carga.
- **Sin objetivo no hay nada que pagar.** Si tras el fallo no queda ningún recurso conocido
  (o el agente ya va lleno), no se consulta al oráculo: el agente vuelve a la base con lo que
  lleve o, sin carga, deambula hasta descubrir algo.
- **El presupuesto `B` solo acota lo proactivo.** Las replanificaciones forzadas por un fallo
  son inevitables, cuentan en `n_ediciones` (son reescrituras del plan) y en
  `n_ediciones_por_fallo`, pero no consumen presupuesto.

Las políticas difieren entonces solo en **cuándo** invocan al replanificador: `OPEN_LOOP` al
fallar; `CLOSED_LOOP` y `GOVERNED` al detectar la divergencia (y también al fallar, si aun
así ocurre); `COLD_RESTART` en los mismos momentos, pero reiniciando en frío; y
`KNOWLEDGE_BASED` y `BAYESIAN` al detectar la divergencia solo si su consulta dice que el plan
ya no sirve, y siempre al fallar. A estas dos últimas se les cobra además, si `ticks_por_ask >
0`, cada consulta hecha en un evento de divergencia (§3.4), de forma que saber más no sale
gratis por construcción.

**Por qué esta regla y no otra.** Una versión anterior del modelo vaciaba el plan tras un
fallo y lo reconstruía al tick siguiente con A\* exacto, sin oráculo y sin costo, de modo
que `OPEN_LOOP` —que ignora las divergencias y espera a fallar— replanificaba gratis y con
competencia perfecta, mientras `CLOSED_LOOP` pagaba `c` ticks y la competencia `p` en cada
reparación. El experimento comparaba así una reparación pagada contra una gratuita, y la
ventaja del lazo abierto era en parte un artefacto de esa asimetría. Con la regla actual la
pregunta queda limpia: dado un mismo replanificador, ¿conviene invocarlo al ver la
divergencia o esperar a que el plan falle?

### 3.3 Compromiso contra oportunismo

Un resultado que el diseño no anticipaba y que conviene dejar escrito, porque matiza el
primer resultado de aprendizaje de la asignatura: **el orden de la taxonomía de R&N
depende del entorno de tarea.**

En el barrido principal (`r=3`, promediando sobre `c`), con λ=0 las cuatro políticas que
planifican rinden 93.3 de utilidad media contra 49.7 del reflejo simple y 57.0 del basado en
modelo, es decir, casi el doble, dado que hace falta previsión para rodear obstáculos y
encadenar objetivos. Progresivamente, a medida que crece el dinamismo, las políticas
reactivas mejoran, de forma que a λ=0.5 el reflejo (73.3) y sobre todo el basado en modelo
(98.3) superan a todas las políticas que planifican, incluido el lazo abierto (53.3 la mejor
de ellas, contra 43.9 del lazo cerrado y 30.4 del reinicio en frío). Vale la pena anotar que
el promedio sobre `c` esconde que con deliberación gratuita (`c=0`) el lazo abierto (120.3) y
el lazo cerrado (110.7) todavía superan al basado en modelo, mientras que con cualquier `c≥2`
este último gana por entre 45 y 86 puntos, por lo que el cruce ocurre en el costo de
deliberar y no solo en el dinamismo. La razón es que el planificador se compromete a una
cadena de objetivos y la ejecuta sin aprovechar lo que se le cruza por el camino, y además
cada replanificación le cuesta `c` ticks durante los cuales el mundo sigue moviéndose,
mientras que el agente reactivo reevalúa en cada tick sin pagar nada. Cabe mencionar que
versiones anteriores del modelo daban otras cifras (una, con otra configuración, un factor de
tres a seis a favor de planificar en el caso estático; otra, con la replanificación gratuita
del lazo abierto que §3.2 corrige, un lazo abierto que superaba también a los reactivos a
λ=0.5), y las de este párrafo son las de `results/principal.csv` con la regla actual.

Planificar compra previsión y vende oportunismo. Cuál de las dos vale más es una propiedad
del entorno, no del agente — que es exactamente la tesis del capítulo 2 de R&N.

### 3.4 Las dos políticas que infieren

`KNOWLEDGE_BASED` y `BAYESIAN` **heredan la reparación en caliente de `CLOSED_LOOP`** (mismo
monitoreo, mismo oráculo, mismo precio y misma replanificación forzada tras un fallo), y lo
único que cambian es qué creencia consultan en tres momentos: al decidir qué recursos son
candidatos, al elegir objetivo y, ante una divergencia, justo antes de pagar `c`. Cabe
mencionar que su motivación salió de los propios datos, pues a λ=0.5 con `c=5` el lazo
cerrado pasa la mayor parte de sus ticks deliberando, de forma que la pregunta es si un
criterio más fino sobre *cuándo* reparar corta ese thrashing.

**Qué sabe `KNOWLEDGE_BASED` (nivel de conocimiento, `conocimiento.py`).** Cada tick hace
`TELL` de lo que ve como fluentes indexados por tiempo (`Visto(r,c,t)`, `¬En(r,c,t)` y
`Recogido(r,t)`), y conoce como ley del mundo el axioma de deriva
$En(r,c,t) \Rightarrow \bigvee_{c' \in N^+(c)} En(r,c',t+1)$, con $N^+(c)$ la celda y sus
vecinas transitables; de λ solo sabe si es cero (entonces el axioma se instancia como «los
recursos no se mueven»). Las observaciones nunca se retiran, de forma que la monotonía se
conserva y lo que caduca es la conclusión «está ahí ahora», que pasa a derivarse. A nivel de
implementación la región posible $R(r,t)$ (lo que DPLL no puede descartar) se mantiene con
operaciones de conjuntos: al ver `r` en `c` se fija $R=\{c\}$ y en cada observación sin verlo
se expande un paso por cada deriva ocurrida y se le restan las celdas vistas, con distancia
geodésica. La equivalencia entre ambos niveles no se supone sino que se prueba contra DPLL de
`logica.py` en una retícula de 4×4 (§9). Sus tres consultas `ASK` son:

1. **¿Dónde puede estar `r` ahora?** Solo son candidatos los recursos cuya última celda
   observada sigue en su región.
2. **¿Qué recurso tengo asegurado?** El objetivo se elige por el peor caso,
   $\max_{x \in R(r,t)} d(\text{agente}, x)$, con la misma distancia de Manhattan que el resto
   de políticas, de forma que una creencia vieja, de región ancha, pierde frente a una
   observación reciente algo más lejana; el destino del plan sigue siendo la última celda
   observada, y lo único que cambia es el orden en que se persiguen los recursos.
3. **¿Sigue siendo ejecutable mi plan?** La respuesta tiene tres valores y solo *inválido*
   repara. Con `horizonte_validez="ahora"` el plan es inválido si la celda creída que el
   monitoreo acaba de refutar ya no está en $R(r,t)$, que es exactamente el monitor de
   `CLOSED_LOOP` leído a nivel de conocimiento; con `"llegada"` (el valor de los barridos),
   si quedan `k` pasos antes del `PICK`, el plan es inválido solo si la celda del `PICK` cae
   fuera de la expansión de `k` pasos de la región, es decir, si el recurso ya no puede estar
   ahí cuando el agente llegue.

**Qué sabe `BAYESIAN` (`filtro.py`).** El mismo conocimiento de fondo, salvo λ, que no recibe
y aprende con un modelo Beta–Bernoulli (prior Beta(1,1); cada recurso cuya celda previa sigue
a la vista es un ensayo: se movió o no), de modo que $\hat\lambda$ es la media posterior. Sobre
la celda de cada recurso fuera de vista mantiene un filtro *forward* de rejilla (predicción
con la caminata,
$P'(x) = (1-\hat\lambda)P(x)[\deg x>0] + P(x)[\deg x=0] + \hat\lambda\sum_{y\sim x} P(y)/\deg y$,
y corrección poniendo a cero las celdas vistas sin el recurso), cuyo soporte es exactamente la
región de `KNOWLEDGE_BASED`. Sus dos decisiones son:

1. **Objetivo por costo esperado** $d/q$, con $d$ la distancia de Manhattan a la última celda
   observada y $q$ la probabilidad de que el recurso siga ahí al llegar (el filtro propagado
   $d$ pasos).
2. **Reparar por utilidad esperada:** con `k` pasos antes del `PICK` y $q$ la probabilidad de
   encontrar el recurso en esa celda al llegar, repara si y solo si $c < (1-q)(c+k)$, pues
   mantener cuesta en esperanza la caminata perdida más la replanificación forzada y reparar
   cuesta `c` ya. Con `"ahora"` repara salvo que la celda refutada sea segura ($P=1$), y con
   visión total eso reduce `BAYESIAN` a `CLOSED_LOOP`.

**Equidad de costo.** El parámetro `ticks_por_ask` (0 por defecto) cobra en ticks quieto cada
consulta 2 o 3 hecha en un evento de divergencia, y esos ticks suman a `pasos_deliberando`, de
forma que entran en la utilidad neta igual que los del oráculo; la actualización de la región
o del filtro es monitoreo por tick y queda gratuita, igual que `observar()` para toda política.
Solo estas dos políticas leen `horizonte_validez` y `ticks_por_ask`, igual que solo `GOVERNED`
lee el presupuesto, por lo que las filas de las demás políticas en los barridos nuevos
reproducen exactamente las de los barridos originales (§9).

**Desviaciones respecto al diseño previo.** Vale la pena anotar tres, todas descubiertas por
los controles exactos. Primeramente, `"ahora"` compara contra la celda creída recién refutada y
no contra la del `PICK`, pues la versión literal rompía la equivalencia con `CLOSED_LOOP` en
28–29 de 30 semillas por desincronización entre plan y creencia; progresivamente, los ensayos
de λ cuentan solo si la celda previa del recurso sigue a la vista, porque exigir verlo en los
dos ticks sesgaba $\hat\lambda$ a la baja (0.38 con λ=0.5 y `r=1`: un recurso que sale del
disco de visión es un movimiento que no se ve); finalmente, la creencia refutada se conserva y
se notifica una sola vez, y la región y el filtro se expanden por el número real de derivas
entre observaciones y no por una por tick, lo cual importa con el orden sorteado.

**Límite honesto.** La contabilidad de costos de la regla $c < (1-q)(c+k)$ es incompleta en los
dos lados: trata la reparación como si costara `c` y comprara certeza, cuando el plan reparado
nace desactualizado (el mundo sigue moviéndose durante los `c` ticks) y una divergencia nueva
puede interrumpirlo, y trata un plan mantenido que falla como si costara solo la caminata más
`c`, sin el costo de buscar un objetivo que ya se perdió de vista. La primera omisión empuja a
reparar de más y es la que muestran los datos (a λ=0.5 y `r=3`, 16.3 reparaciones proactivas
contra 9.5 de `KNOWLEDGE_BASED`, y 145.8 ediciones desperdiciadas contra 97.4), de modo que es
la causa medida de que `BAYESIAN` no supere a `KNOWLEDGE_BASED` (`info/00-rationale.md` §6).

## 4. Métricas

Definiciones operacionales. Todas se recogen con `DataCollector` como *model reporters*.

| Métrica | Definición |
|---|---|
| `entregas` | Recursos depositados en la base |
| `pasos_utiles` | Ticks ejecutando `GOTO` / `PICK` / `DELIVER` |
| `pasos_deliberando` | Ticks dentro de una acción `DELIBERAR` (completada **o** interrumpida), la dispare un fallo o una divergencia |
| `n_ediciones` | Deliberaciones completadas, cada una de las cuales instala un plan reparado (en caliente o en frío). Incluye las replanificaciones forzadas por un fallo |
| `n_ediciones_por_fallo` | Subconjunto de `n_ediciones` disparado por un fallo del plan. Son las únicas que hace `OPEN_LOOP`, y no consumen el presupuesto `B` |
| `n_ediciones_desperdiciadas` | Ediciones seguidas de otra petición de reparación antes de ejecutar `k=2` líneas, más toda deliberación interrumpida antes de terminar, más toda edición rechazada por salirse del alcance de edición. **Es la medida operacional del *thrashing*** |
| `carga_perdida` | Recursos soltados por un reinicio en frío. Es el trabajo en curso que el reinicio en frío tira y la reparación en caliente conserva |
| `tareas_fallidas` | Veces que una línea del plan no pudo ejecutarse (un `PICK` sin recurso o un `DELIVER` sin carga). Cada una dispara una replanificación forzada, pagada salvo que no quede ningún recurso conocido |
| `divergencias_reales` | Veces que el plan dejó de ser válido en el mundo, contadas como transiciones a estado divergente |
| `divergencias_detectadas` | Subconjunto que el agente percibió. Se emparejan con las reales —una detección solo cuenta si hay una divergencia real pendiente— para que la cifra no pueda superar a la de reales y la ceguera quede acotada en `[0,1]` |
| `ceguera` | `1 − detectadas/reales`. Fracción de divergencias que el agente nunca llegó a notar |
| `latencia_deteccion` | Ticks entre que una divergencia ocurre y el agente la nota. **Es la medida útil del costo de la observabilidad parcial en este entorno** |
| `n_consultas` | Consultas 2 y 3 a la KB o al filtro hechas en eventos de divergencia (§3.4); son las que cobra `ticks_por_ask`. Vale 0 para las políticas que no infieren |
| `lambda_estimado` | $\hat\lambda$ de `BAYESIAN` al final de la corrida, la media posterior de su Beta–Bernoulli; `NaN` para el resto de políticas |

Y la medida de rendimiento compuesta:

```
utilidad_bruta   = valor_entrega · entregas        (valor_entrega = 10)
costo_delib      = κ · pasos_deliberando
utilidad_neta    = utilidad_bruta − costo_delib
```

Separar `κ` (precio por tick de pensar) del costo de oportunidad es deliberado. Con `κ = 0`
el único castigo por deliberar es el tiempo perdido —el caso de un modelo local gratuito—;
con `κ > 0` se modela el costo real en tokens o dinero. La frontera de fase se mueve con `κ`,
y esa dependencia es directamente la decisión de presupuesto de un motor de ejecución
agéntica. Cabe mencionar que todos los barridos se corrieron con `κ = 0`, por lo que en los
resultados la utilidad neta es exactamente diez veces las entregas y el efecto de `κ > 0`
queda sin medir.

## 5. Parámetros del experimento

| Símbolo | Nombre en código | Valores en los barridos | Significado |
|---|---|---|---|
| — | `policy` | las 8 de §3 (las seis originales en los siete barridos originales) | Arquitectura de agente |
| λ | `lambda_dinamismo` | `0, 0.05, 0.1, 0.25, 0.5` | Prob. por tick de que un recurso se mueva |
| `p` | `competencia` | `0.5, 0.7, 0.9, 1.0` | Prob. de que la edición del oráculo sea correcta |
| `c` | `costo_edicion` | `0, 2, 5, 10` | Ticks que consume deliberar |
| `r` | `radio` | `1, 3, None` (`None` = ∞) | Radio de visión (observabilidad parcial) |
| `B` | `presupuesto` | `None` (∞), y `0, 3, 5, 10, 25` en el barrido de gobernanza | Reparaciones proactivas permitidas (solo `GOVERNED`); las forzadas por un fallo no cuentan |
| — | `orden_aleatorio` | `False`, y `True` en el barrido `orden` | Sortear cada tick si el recolector actúa antes o después de la deriva (§2) |
| — | `horizonte_validez` | `"llegada"`, y `"ahora"` en `conocimiento_ahora` | Cuándo debe seguir siendo posible el plan para no repararlo (solo `KNOWLEDGE_BASED` y `BAYESIAN`, §3.4) |
| — | `ticks_por_ask` | `0`, y `1, 2, 5` en `conocimiento_costo` | Ticks quieto que cuesta cada consulta en un evento de divergencia (solo las dos políticas que infieren) |
| `κ` | `kappa` | `0` | Precio por tick de deliberación |
| `N` | `size` | `15` | Lado de la retícula (fijo) |
| `K` | `n_resources` | `8`, y `2, 4, 8, 16` en los barridos de escasez | Recursos simultáneos |
| — | `capacidad` | `3` | Recursos a reunir antes de entregar. Es lo que crea *trabajo en curso*: sin él, un reinicio en frío no pierde nada y la comparación entre frío y caliente se vacía |
| — | `densidad_obstaculos` | `0.15` | Fracción de celdas bloqueadas |
| ε | `epsilon_reflejo` | `0.15` | Movimiento aleatorio de las políticas reactivas, para escapar de mínimos locales (R&N §2.4.2) |
| `T_max` | `max_steps` | `400` | Horizonte |

Los valores fijos son los de `BASE` en `experiments.py`, que difieren de los valores por
defecto del constructor de `OASysWorld` (`size=20`, `max_steps=1000`), de forma que una
corrida suelta del modelo no reproduce las de los barridos a menos que se le pasen
explícitamente.

Réplicas: **30** por combinación, con semillas `0…29` que se pasan por el argumento `rng` de
`batch_run` (nunca dentro de `parameters`, donde se sobrescribirían en silencio).

El barrido completo es grande, así que se ejecuta por etapas, cada una guardada en
`results/<nombre>.csv`, y entre todas suman **16.260 corridas** en trece barridos. Los siete
primeros son los originales y quedaron congelados a las seis políticas originales (las listas
de políticas se fijan a mano en `experiments.py` y no se derivan del enum, para que añadir una
política no cambie en silencio la definición de un barrido ya guardado):

1. **`principal`:** `policy × λ × c`, con `p=0.9` y `r=3`. Es la figura principal (la
   frontera de fase) y son 6 × 5 × 4 × 30 = 3.600 corridas.
2. **`competencia`:** las 4 políticas con plan × λ ∈ {0, 0.1, 0.25, 0.5} × `p`, con `c=5` y
   `r=3` (1.920 corridas). Responde "¿desde qué `p` conviene auto-editarse?".
3. **`observabilidad`:** las 4 políticas con plan × λ ∈ {0, 0.1, 0.25, 0.5} × `r`, con
   `p=0.9` y `c=5` (1.440 corridas). Aísla el efecto de la observabilidad parcial.
4. **`gobernanza`:** `CLOSED_LOOP` y `GOVERNED` × λ ∈ {0.1, 0.25, 0.5} × `B` ∈ {0, 3, 5, 10,
   25}, con `p=0.9`, `c=5` y `r=3` (900 corridas).
5. **`control2`, `control3` y `control4`:** las combinaciones que exigen los controles de
   sanidad 2, 3 y 6 de §9, que ningún otro barrido fija (300, 120 y 360 corridas).

Los seis siguientes salen de las extensiones posteriores al Avance 2
(`docs/roadmap-c4.md`, `roadmap-c4b.md` y `roadmap-c5.md`), todos con `p=0.9` salvo que se diga:

6. **`orden`:** `MODEL_BASED`, `OPEN_LOOP`, `COLD_RESTART` y `CLOSED_LOOP` × λ ∈ {0.1, 0.25,
   0.5} × `c` ∈ {2, 5}, con `r=3` y `orden_aleatorio=True` (720 corridas). Es el subconjunto de
   `principal` con el orden de activación sorteado, y lo que se compara es el signo de las
   diferencias que sostienen las conclusiones.
7. **`conocimiento`:** `MODEL_BASED`, `OPEN_LOOP`, `CLOSED_LOOP`, `KNOWLEDGE_BASED` y
   `BAYESIAN` × λ ∈ {0, 0.1, 0.25, 0.5} × `r` ∈ {1, 3, ∞}, con `c=5` y horizonte `"llegada"`
   (1.800 corridas). `MODEL_BASED` entra porque es la vara más exigente con λ alto.
8. **`conocimiento_ahora`:** las dos políticas que infieren con horizonte `"ahora"` × λ × `r`
   (720 corridas). Es la ablación que aísla la elección de objetivo del criterio de reparación
   y, con `r=∞`, los controles exactos H2 y HB2 de §9.
9. **`conocimiento_costo`:** las dos políticas que infieren × λ ∈ {0.1, 0.25, 0.5} ×
   `ticks_por_ask` ∈ {1, 2, 5}, con `r=3` y `c=5` (540 corridas). Mide desde qué costo de
   preguntar deja de compensar saber más.
10. **`escasez`:** `MODEL_BASED`, `OPEN_LOOP`, `COLD_RESTART`, `CLOSED_LOOP` y
    `KNOWLEDGE_BASED` × `n_resources` ∈ {2, 4, 8, 16} × λ ∈ {0, 0.1, 0.25, 0.5}, con `r=3` y
    `c=5` (2.400 corridas), que es el régimen mixto.
11. **`escasez_inf`:** `OPEN_LOOP`, `COLD_RESTART` y `CLOSED_LOOP` × `n_resources` × λ en el
    régimen del control 2 (`c=0`, `p=1`, `r=∞`; 1.440 corridas), donde replanificar gana.

Aparte de los CSV, `results/dinamica.parquet` guarda la serie temporal decimada cada 5 ticks
de 600 corridas (cinco políticas sin `GOVERNED` × λ ∈ {0, 0.1, 0.25, 0.5} × 30 semillas, con
`c=5` y `r=3`), y `results/abc.parquet` la tabla de referencia de la calibración ABC
(3.000 muestras de (λ, p), de dos semillas cada una, tomadas de un prior uniforme λ ∈ [0, 0.8], `p` ∈ [0.5, 1], simuladas con
`OPEN_LOOP`, `c=5` y `r=3`), que no son barridos de `batch_run` sobre una rejilla sino
simulaciones para inferir los parámetros de un despliegue.

## 6. Estructura del plan

El plan se representa como un programa editable de líneas con su contador de programa
(`book.py`, cuya clase se llama `Book`):

```python
class LineOp(StrEnum):
    GOTO = "GOTO"  # arg: celda destino
    PICK = "PICK"  # arg: id de recurso
    DELIVER = "DELIVER"  # arg: None
    SCAN = "SCAN"  # arg: None — gasta un tick observando


@dataclass(frozen=True, slots=True)
class Line:
    op: LineOp
    arg: Any = None
    locked: bool = False  # fuera del alcance de edición del agente


@dataclass(slots=True)
class Book:
    lines: list[Line]
    pc: int = 0
```

`Book.replace_suffix(from_idx, new_lines)` es la operación de edición del plan, y se acepta o
se rechaza entera (nunca deja el plan a medias), de forma que lanza `EditRejected` en dos
casos: cuando `from_idx` es anterior al contador (reescribir líneas ya ejecutadas no tiene
sentido) y cuando la edición altera las líneas fuera del alcance de edición. Lo que se
compara antes y después es el contenido y el orden de las líneas bloqueadas, no su posición,
por lo que un sufijo puede reescribirse aunque contenga una línea bloqueada siempre que la
reproduzca intacta, que es justo lo que permite reparar la ruta hacia un recurso sin poder
eliminar el `DELIVER` comprometido al final. Es un invariante y las pruebas de
`tests/test_book.py` lo verifican.

## 7. El oráculo

```python
def propose(self, req: RepairRequest) -> Proposal:
    acierta = self.random.random() < self.p
    if req.true_goal is None:  # el agente no ve el objetivo real
        return ruta_optima_hacia(req.believed_goal)  # STALE_TARGET
    if acierta:
        return ruta_optima_hacia(req.true_goal)  # OPTIMAL
    return objetivo_obsoleto_o_desvio(req)  # STALE_TARGET o DETOUR, al 50 %
```

(Pseudocódigo resumido de `oracle.py`, `Oracle.propose`.) El oráculo solo recibe la posición
real del objetivo si el agente puede verla, por lo que bajo observabilidad parcial la
competencia `p` deja de operar en buena parte de las consultas, y la propuesta arrastra
siempre la continuación del plan (objetivos pendientes, regreso y `DELIVER` bloqueado) en vez
de truncar la tarea a un solo objetivo.

El fallo debe producir un plan **plausible**, no ruido. Dos modos de fallo, elegidos
porque son los que un modelo de lenguaje comete de verdad:

- **Objetivo obsoleto:** A\* correcto hacia la última posición conocida del recurso, que ya
  cambió. El plan es internamente coherente y va al lugar equivocado.
- **Ruta con desvío:** llega al objetivo correcto por un camino subóptimo.

Que el fallo sea coherente y no aleatorio es lo que hace válida la analogía: un LLM que se
equivoca no devuelve basura, devuelve algo razonable y falso.

## 8. La deliberación como acción interrumpible

Una deliberación:

- ocupa `c` ticks; con `c = 0` es instantánea y no cuesta nada;
- expone `progress ∈ [0,1]` y `remaining`;
- puede ser **interrumpida** si llega una divergencia nueva antes de terminar — y los
  ticks ya gastados se pierden. Esa pérdida se contabiliza en
  `n_ediciones_desperdiciadas` y es la forma operacional del *thrashing*.

Y la decisión de modelado más importante del módulo:

> **El plan que produce una deliberación se calcula con el mundo tal como estaba cuando la
> deliberación empezó.**

Si el mundo se movió mientras el agente pensaba, el plan llega desactualizado. Ese es el
costo real de pensar en un entorno dinámico, y es lo que impide que "deliberar más" sea
siempre mejor.

**Sobre la implementación.** Ni se usa la clase `Action` de MESA 4.0 ni el simulador de
eventos discretos de 3.5.1 (`mesa.experimental.devs`). Lo primero, porque esa clase es el
objeto de estudio y importarla prehecha escondería el mecanismo que se quiere medir
(ver [`00-rationale.md`](00-rationale.md) §4). Lo segundo, porque `batch_run` —el eje
experimental del proyecto— es un bucle `while model.running: model.step()`
(`mesa/batchrunner.py:206`) que no sabe nada de colas de eventos; y porque una cola rinde
cuando los eventos son escasos, mientras que aquí cada agente actúa en cada tick. La
deliberación es por tanto una acción contada en ticks dentro del `step()` estándar.

## 9. Controles de sanidad

Antes de creer cualquier resultado del barrido:

1. **λ=0** → `CLOSED_LOOP` debe igualar exactamente a `OPEN_LOOP`, con cualquier `p`, `c` y
   `r` (se evalúa sobre el barrido principal, con `p=0.9` y `r=3`). Sin dinamismo,
   replanificar no puede ayudar; si ayuda, hay un error.
2. **c=0, p=1 y r=∞** → `CLOSED_LOOP` debe dominar a `OPEN_LOOP` en todo λ. Si deliberar es
   gratis, el replanificador es perfecto y el agente lo ve todo, más deliberación no
   puede perjudicar.

   Las tres condiciones hacen falta, y omitir alguna convierte el control en un
   resultado. Con `r` finito el oráculo a menudo no observa dónde está realmente el
   objetivo, así que repara sobre una creencia obsoleta; bajo observabilidad parcial
   (`r=3`, `p=0.9`) y con deliberación gratuita, el lazo cerrado no supera al abierto en
   ningún λ del barrido principal (y a λ=0.25 pierde por 25.7 puntos), es decir que
   **replanificar con mala información no es mejor que comprometerse con el plan**, lo cual
   es uno de los hallazgos del trabajo y no un fallo del modelo. Con las tres condiciones,
   en cambio, el control pasa con margen (+14 a +56 puntos según λ).
3. **p=0.5, c=10, λ bajo** → `CLOSED_LOOP` debe ser **peor** que `OPEN_LOOP`. Un replanificador
   mediocre y caro destruye un plan correcto. Si no aparece, el modelo de costo no muerde.
   Cabe mencionar que con la regla de costo actual pasa solo por el signo (85.0 contra 87.5,
   una diferencia dentro del error estándar de 30 réplicas), por lo que lo defendible es que
   el lazo cerrado no mejora, más que que empeore.
4. **Reproducibilidad:** misma semilla ⇒ mismas trayectorias, bit a bit. Ojo con las
   estructuras no ordenadas: devolver un `list(set)` de celdas hace que el orden dependa
   del hash de los objetos —es decir, de direcciones de memoria— y rompe la
   reproducibilidad sin que nada falle visiblemente.
5. **A\* óptimo:** contrastado contra BFS en retículas sin pesos; deben coincidir en longitud
   de ruta.
6. **B=0** → `GOVERNED` debe igualar exactamente a `OPEN_LOOP`, corrida a corrida, con
   cualquier λ y `c`. Sin presupuesto no hay reparación proactiva, y lo único que queda es
   replanificar al fallar al mismo precio que el lazo abierto (§3.2); cualquier diferencia
   delata que la regla de costo o la gobernanza se aplican distinto a las dos políticas.

Con las dos políticas que infieren y los barridos de las extensiones entraron cinco
controles más, todos exactos salvo el de orden:

7. **H2:** con `r=∞` y horizonte `"ahora"`, `KNOWLEDGE_BASED` debe igualar a `CLOSED_LOOP`
   semilla a semilla, incluidas las replanificaciones por fallo, porque la región de cada
   recurso es un punto en cada decisión y la consulta 3 reproduce el monitor; con λ=0 la
   igualdad vale en todo radio.
8. **HB2:** con `r=∞` y `"ahora"`, `BAYESIAN` debe igualar a `CLOSED_LOOP` semilla a semilla.
9. **Solidez y soporte:** en corridas con λ>0 y `r` finito, la celda real de cada recurso
   rastreado está siempre en su región posible (y tiene probabilidad positiva en el filtro), el
   soporte del filtro coincide con la región de `KNOWLEDGE_BASED` en cada tick, y en una
   retícula de 4×4 DPLL responde `falso` exactamente fuera de la región y `desconocido`
   dentro, que es la prueba de que el nivel de implementación por conjuntos equivale al nivel
   de conocimiento. El motor lógico se prueba además por su cuenta (las oraciones R1–R5 de
   R&N, `tt_entails` frente a DPLL en 100 oraciones, CNF equivalente y una cadena de 40
   implicaciones en menos de un segundo).
10. **Regresión de los barridos nuevos:** las filas que repiten una configuración ya corrida
    deben reproducirla exactamente, y lo hacen: `OPEN_LOOP` y `CLOSED_LOOP` de
    `conocimiento` frente a `observabilidad.csv` (0 de 720 distintas), `MODEL_BASED` con `r=3`
    frente a `principal.csv` (0 de 120), y la celda `n_resources=8` de `escasez` y
    `escasez_inf` frente a `principal.csv`, `conocimiento.csv` y `control2.csv`. Re-ejecutar
    corridas originales con el código actual da también lo mismo que `principal.csv`, de forma
    que añadir las dos políticas no cambió a las seis originales.
11. **Robustez al orden de activación** (no exacto, por signo): con el orden sorteado, la
    diferencia entre reparar en caliente y en frío conserva el signo en cinco de seis celdas
    (la excepción es λ=0.5 con `c=5`, donde ambas colapsan) y la ventaja de no planificar con
    λ alto también, mientras que la diferencia entre lazo abierto y cerrado cambia de signo en
    tres de seis, lo cual es consistente con que casi empaten.

Los controles 1 a 3 y el 6 se evalúan sobre los CSV con `uv run python -m project.analysis
--controles` (y en el cuaderno, §3), el 11 con `analysis.robustez_orden()`, mientras que el 4,
el 5 y los del 7 al 10 son propiedades del código o de los CSV guardados y viven como pruebas
en `tests/` (`test_conocimiento.py`, `test_filtro.py`, `test_logica.py` y `test_escasez.py`).
