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
| **E** — Entorno | Retícula `N×N` de von Neumann con obstáculos fijos; `K` recursos que se desplazan; una base de entrega en posición fija |
| **A** — Actuadores | `GOTO(celda)` un paso por tick; `PICK(recurso)`; `DELIVER()`; `DELIBERAR()` — que consume `c` ticks y produce un plan nuevo |
| **S** — Sensores | Contenido de las celdas dentro del radio `r` de la posición actual. Fuera de `r`, el agente solo tiene su creencia |

**Sobre `DELIBERAR` como actuador:** es la decisión de diseño central. Deliberar no es un
acto instantáneo entre ticks, sino **una acción del mismo tipo que moverse**, que ocupa
tiempo del reloj durante el cual el mundo sigue cambiando. Sin esto no hay costo que medir y
la pregunta del trabajo se vuelve trivial.

## 2. Clasificación del entorno (R&N §2.3.2)

| Propiedad | Valor | Cómo se controla |
|---|---|---|
| Observable | **Parcialmente** (totalmente si `r = ∞`) | Parámetro `r` — modela el set `ignore` de OASys |
| Determinista | **Estocástico** | El movimiento de recursos (λ) y la competencia del oráculo (`p`) |
| Episódico | **Secuencial** | Las decisiones tempranas condicionan todo el resto — es el régimen de horizonte largo |
| Estático | **Dinámico** | Los recursos se mueven **mientras el agente delibera**. Esta es la propiedad que hace costosa la deliberación |
| Discreto | **Discreto** | Retícula y ticks enteros |
| Agentes | **Un agente** (multi-agente en extensión) | — |
| Conocido | **Conocido** | Las reglas del entorno se conocen; lo que no se conoce es el *estado* |

El caso λ=0, r=∞ colapsa a un entorno estático y totalmente observable: ahí la planeación de
lazo abierto es óptima por construcción, y sirve como control de sanidad del experimento.

## 3. Arquitecturas de agente

Las cinco primeras corresponden una a una con la taxonomía de R&N §2.4, que es el RAE #1 de
la asignatura. Las dos últimas columnas indican qué modo de OASys representa cada una.

| # | Clase | Descripción | R&N | OASys |
|---|---|---|---|---|
| 1 | `ReflexAgent` | Se mueve con avidez hacia el recurso visible más cercano. Sin plan ni memoria | §2.4.2 reflejo simple | — (línea base) |
| 2 | `ModelBasedAgent` | Mantiene un mapa de creencias del mundo; sigue siendo reactivo, sin plan explícito | §2.4.3 reflejo basado en modelo | Estado en disco (`state.json`) |
| 3 | `OpenLoopAgent` | Calcula un plan A\* una vez y lo ejecuta sin realimentación. Ignora las divergencias | §2.4.4 basado en objetivos, lazo abierto | `cold` **sin** `editBook` |
| 4 | `ColdRestartAgent` | Al divergir, **aborta la corrida** y replanifica desde cero en la siguiente | lazo abierto con reinicio | `cold` **con** `editBook` — el clock-edge real |
| 5 | `ClosedLoopAgent` | Monitorea, y al divergir replanifica en sitio pagando `c` ticks | §11.5.3 planeación en línea | `run=hot` (no implementado) |
| 6 | `GovernedAgent` | Como (5), pero con presupuesto de `B` ediciones y líneas `@lock` inmutables | lazo cerrado con recursos acotados | `run=hot` + gobernanza + cuota |

**Por qué (4) merece ser una política y no una nota al pie.** `ColdRestartAgent` modela
literalmente lo que OASys hace hoy: el motor ejecuta un *snapshot*, la edición del agente
aplica en la corrida siguiente, y el progreso de la corrida actual se pierde. Su diferencia
de rendimiento contra (5) **es** el costo cuantificado de no haber implementado `run=hot`.
Ese número es el entregable que vuelve al sistema real.

### 3.1 Niveles de monitoreo (R&N §11.5.3)

R&N distingue tres niveles a los que un agente puede detectar que su plan ya no sirve. Se
implementan los dos primeros; el tercero queda como parámetro opcional.

| Nivel | Detecta | Implementación |
|---|---|---|
| **De acción** | La precondición de la línea actual no se cumple | `PICK(A)` pero `A` no está en la celda |
| **De plan** | El resto del plan ya no puede tener éxito, aunque la línea actual sí | El recurso objetivo se movió fuera de la ruta restante |
| **De objetivo** *(opcional)* | Apareció una meta mejor | Un recurso más cercano entró en el radio `r` |

El nivel de monitoreo es en sí mismo una variable interesante: monitorear más profundo
detecta antes, pero dispara más ediciones. Se deja como extensión.

**Sobre por qué la ceguera casi no aparece.** El diseño inicial esperaba que un radio
pequeño hiciera al agente *perderse* divergencias. Casi no ocurre, y por una razón
estructural: el plan lleva al agente precisamente a la celda donde creía que estaba el
recurso, así que tarde o temprano descubre que no está. Lo que cambia con el radio no es
*si* se entera sino **cuándo**, y mientras tanto camina hacia el sitio equivocado. De ahí
que la métrica que importa sea la latencia y no la fracción de perdidas.

### 3.2 Compromiso contra oportunismo

Un resultado que el diseño no anticipaba y que conviene dejar escrito, porque matiza el
primer resultado de aprendizaje de la asignatura: **el orden de la taxonomía de R&N
depende del entorno de tarea.**

Con recursos escasos y terreno obstruido, planificar bate al reflejo por un factor de tres
a seis: hace falta previsión para rodear obstáculos y encadenar objetivos lejanos. Pero
con recursos abundantes que reaparecen por todo el mapa, el agente reflejo **iguala o
supera** al planificador. La razón es que el planificador se compromete a una cadena de
objetivos y la ejecuta sin aprovechar lo que se le cruza por el camino, mientras que el
reflejo reevalúa en cada tick.

Planificar compra previsión y vende oportunismo. Cuál de las dos vale más es una propiedad
del entorno, no del agente — que es exactamente la tesis del capítulo 2 de R&N.

## 4. Métricas

Definiciones operacionales. Todas se recogen con `DataCollector` como *model reporters*.

| Métrica | Definición |
|---|---|
| `entregas` | Recursos depositados en la base |
| `pasos_utiles` | Ticks ejecutando `GOTO` / `PICK` / `DELIVER` |
| `pasos_deliberando` | Ticks dentro de una acción `DELIBERAR` (completada **o** interrumpida) |
| `n_ediciones` | Llamadas a `replace_suffix` aceptadas |
| `n_ediciones_desperdiciadas` | Ediciones seguidas de otra divergencia antes de ejecutar `k` líneas (por defecto `k=2`), más toda deliberación interrumpida antes de terminar. **Es la medida operacional del *thrashing*** |
| `carga_perdida` | Recursos soltados por un reinicio en frío. Es el trabajo en vuelo que `cold` tira y `hot` conserva |
| `divergencias_reales` | Veces que el plan dejó de ser válido en el mundo, contadas como transiciones a estado divergente |
| `divergencias_detectadas` | Subconjunto que el agente percibió. Se emparejan con las reales —una detección solo cuenta si hay una divergencia real pendiente— para que la cifra no pueda superar a la de reales y la ceguera quede acotada en `[0,1]` |
| `ceguera` | `1 − detectadas/reales`. Fracción de divergencias que el agente nunca llegó a notar |
| `latencia_deteccion` | Ticks entre que una divergencia ocurre y el agente la nota. **Es la medida útil del costo de la observabilidad parcial en este entorno** |

Y la medida de rendimiento compuesta:

```
utilidad_bruta   = w · entregas
costo_delib      = κ · pasos_deliberando
utilidad_neta    = utilidad_bruta − costo_delib
```

Separar `κ` (precio por tick de pensar) del costo de oportunidad es deliberado. Con `κ = 0`
el único castigo por deliberar es el tiempo perdido —el caso de un modelo local gratuito—;
con `κ > 0` se modela el costo real en tokens o dinero. La frontera de fase se mueve con `κ`,
y esa dependencia es directamente la decisión de presupuesto en OASys.

## 5. Parámetros del experimento

| Símbolo | Nombre en código | Valores del barrido | Significado |
|---|---|---|---|
| — | `politica` | las 6 de §3 | Arquitectura de agente |
| λ | `lambda_dinamismo` | `0, 0.05, 0.1, 0.25, 0.5` | Prob. por tick de que un recurso se mueva |
| `p` | `competencia` | `0.5, 0.7, 0.9, 1.0` | Prob. de que la edición del oráculo sea correcta |
| `c` | `costo_edicion` | `0, 2, 5, 10` | Ticks que consume deliberar |
| `r` | `radio` | `1, 3, ∞` | Radio de visión (observabilidad parcial) |
| `B` | `presupuesto` | `∞`, `10` | Ediciones permitidas (solo `GovernedAgent`) |
| `κ` | `kappa` | `0, 0.5` | Precio por tick de deliberación |
| `N` | `size` | `20` | Lado de la retícula (fijo) |
| `K` | `n_recursos` | `8` | Recursos simultáneos (fijo) |
| — | `capacidad` | `3` | Recursos a reunir antes de entregar. Es lo que crea *trabajo en vuelo*: sin él, un reinicio en frío no pierde nada y la comparación `cold` contra `hot` se vacía |
| ε | `epsilon_reflejo` | `0.15` | Movimiento aleatorio de las políticas reactivas, para escapar de mínimos locales (R&N §2.4.2) |
| `T_max` | `max_steps` | `1000` | Horizonte |

Réplicas: **30** por combinación, con semillas derivadas de forma determinista.

El barrido completo es grande, así que se ejecuta por etapas:

1. **Barrido principal:** `politica × λ × c`, con `p=0.9`, `r=3`, `κ=0`. Es la figura
   principal —la frontera de fase— y son 6 × 5 × 4 × 30 = 3.600 corridas.
2. **Sensibilidad a la competencia:** `politica × λ × p`, con `c=5`. Responde "¿desde qué `p`
   conviene auto-editarse?".
3. **Sensibilidad a la observabilidad:** `politica × λ × r`. Aísla el efecto de `ignore`.
4. **Gobernanza:** `ClosedLoop` vs `Governed` con `B` finito, en régimen de λ alto.

## 6. Estructura del plan (el "Book")

Réplica mínima del contador de programa de OASys
(`backend/src/engine/scheduler/mod.rs::PageRunner`):

```python
class LineOp(StrEnum):
    GOTO = "GOTO"  # arg: celda destino
    PICK = "PICK"  # arg: id de recurso
    DELIVER = "DELIVER"  # arg: None
    SCAN = "SCAN"  # arg: None — gasta un tick observando


@dataclass
class Line:
    op: LineOp
    arg: Any = None
    locked: bool = False  # @lock: el oráculo no puede tocarla


@dataclass
class Book:
    lines: list[Line]
    pc: int = 0
```

`Book.replace_suffix(from_idx, new_lines)` es el análogo de `editBook`. **Debe rechazar la
edición si alguna línea en `lines[from_idx:]` está bloqueada** — el equivalente de
`validate_edit` en `backend/src/agent/tools/governance.rs:72`, donde toda construcción
bloqueada debe renderizar idéntica. Es un invariante y los tests lo verifican.

## 7. El oráculo

```python
def propose_edit(self, book, divergence, belief) -> Book | None:
    if self.random.random() < self.p:
        return astar_repair(book, divergence, belief)  # sufijo óptimo
    return degraded_repair(book, divergence, belief)  # plausible pero equivocado
```

`degraded_repair` debe producir un plan **plausible**, no ruido. Dos modos de fallo, elegidos
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

1. **λ=0, p=1, r=∞** → `ClosedLoop` debe igualar exactamente a `OpenLoop`. Sin dinamismo,
   replanificar no puede ayudar; si ayuda, hay un error.
2. **c=0, p=1 y r=∞** → `ClosedLoop` debe dominar a `OpenLoop` en todo λ. Si deliberar es
   gratis, el replanificador es perfecto y el agente lo ve todo, más deliberación no
   puede perjudicar.

   Las tres condiciones hacen falta, y omitir alguna convierte el control en un
   resultado. Con `r` finito el oráculo casi nunca observa dónde está realmente el
   objetivo, así que repara sobre una creencia obsoleta y cambia de objetivo cada vez;
   bajo observabilidad parcial, **replanificar con mala información es peor que
   comprometerse con el plan**, incluso con deliberación gratuita. Ese es uno de los
   hallazgos del trabajo, no un fallo del modelo.
3. **p=0.5, c=10, λ bajo** → `ClosedLoop` debe ser **peor** que `OpenLoop`. Un replanificador
   mediocre y caro destruye un plan correcto. Si no aparece, el modelo de costo no muerde.
4. **Reproducibilidad:** misma semilla ⇒ mismas trayectorias, bit a bit. Ojo con las
   estructuras no ordenadas: devolver un `list(set)` de celdas hace que el orden dependa
   del hash de los objetos —es decir, de direcciones de memoria— y rompe la
   reproducibilidad sin que nada falle visiblemente.
5. **A\* óptimo:** contrastado contra BFS en retículas sin pesos; deben coincidir en longitud
   de ruta.
