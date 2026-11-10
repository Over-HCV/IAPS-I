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
| **A** — Actuadores | `GOTO(celda)` un paso por tick; `PICK(recurso)`; `DELIVER()`; `DELIBERAR()` — que consume `c` ticks y produce un plan nuevo |
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
| Conocido | **Conocido** | Las reglas del entorno se conocen; lo que no se conoce es el *estado* |

El caso λ=0, r=∞ colapsa a un entorno estático y totalmente observable: ahí la planeación de
lazo abierto es óptima por construcción, y sirve como control de sanidad del experimento.

## 3. Arquitecturas de agente

Todas las políticas comparten un mismo cuerpo de agente (`Collector` en `agents.py`), y lo
único que cambia entre ellas es la enumeración `Policy`, es decir, cómo reacciona cada una a
una divergencia entre el plan y el mundo. Entre las cuatro que planifican, además, la
diferencia es solo **cuándo** invocan al replanificador, no cuánto les cuesta, pues todas lo
pagan al mismo precio (§3.2). Las tres primeras siguen la taxonomía de R&N §2.4,
que es el RAE #1 de la asignatura, mientras que las tres últimas extienden al agente basado
en objetivos con las variantes de replanificación de §11.5.

| # | Política | Descripción | R&N | Cuándo aplica la edición |
|---|---|---|---|---|
| 1 | `REFLEX` | Se mueve con avidez hacia el recurso visible más cercano, con un paso aleatorio de probabilidad ε para escapar de mínimos locales. Sin plan ni memoria | §2.4.2 reflejo simple | — (línea base, no planifica) |
| 2 | `MODEL_BASED` | Mantiene creencias sobre dónde están los recursos y persigue el más cercano según ellas; sigue siendo reactivo, sin plan explícito | §2.4.3 reflejo basado en modelo | — (no planifica) |
| 3 | `OPEN_LOOP` | Calcula un plan A\* y lo ejecuta sin realimentación, ignorando las divergencias hasta que el plan falla (un `PICK` sin recurso); solo entonces replanifica, pagando `c` ticks con el mismo replanificador que las demás | §2.4.4 basado en objetivos, lazo abierto | Al fallar, en caliente: conserva la carga |
| 4 | `COLD_RESTART` | Al detectar una divergencia (o al fallar el plan) delibera `c` ticks, y luego **suelta la carga** y arranca con el plan nuevo desde cero | lazo abierto con reinicio | En frío: en la ejecución siguiente, y el trabajo en curso se pierde |
| 5 | `CLOSED_LOOP` | Monitorea, y al divergir repara el sufijo del plan en sitio pagando `c` ticks; si aun así el plan falla, replanifica igual que (3) | §11.5.3 planeación en línea | En caliente: sobre la ejecución en curso |
| 6 | `GOVERNED` | Como (5), pero con un presupuesto de `B` reparaciones proactivas; agotado el presupuesto deja de reparar al divergir y se comporta exactamente como (3) | lazo cerrado con recursos acotados | En caliente, con presupuesto `B` |

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
así ocurre); `COLD_RESTART` en los mismos momentos, pero reiniciando en frío.

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
| — | `policy` | las 6 de §3 | Arquitectura de agente |
| λ | `lambda_dinamismo` | `0, 0.05, 0.1, 0.25, 0.5` | Prob. por tick de que un recurso se mueva |
| `p` | `competencia` | `0.5, 0.7, 0.9, 1.0` | Prob. de que la edición del oráculo sea correcta |
| `c` | `costo_edicion` | `0, 2, 5, 10` | Ticks que consume deliberar |
| `r` | `radio` | `1, 3, None` (`None` = ∞) | Radio de visión (observabilidad parcial) |
| `B` | `presupuesto` | `None` (∞), y `0, 3, 5, 10, 25` en el barrido de gobernanza | Reparaciones proactivas permitidas (solo `GOVERNED`); las forzadas por un fallo no cuentan |
| `κ` | `kappa` | `0` | Precio por tick de deliberación |
| `N` | `size` | `15` | Lado de la retícula (fijo) |
| `K` | `n_resources` | `8` | Recursos simultáneos (fijo) |
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
`results/<nombre>.csv`, y entre todas suman **8.640 corridas**:

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

Los controles 1 a 3 y el 6 se evalúan sobre los CSV con `uv run python -m project.analysis
--controles` (y en el cuaderno, §3), mientras que el 4 y el 5 son propiedades del código y
viven como pruebas en `tests/`.
