# 01 — Diccionario: concepto ↔ Russell & Norvig ↔ implementación

> Este documento es la columna vertebral del informe académico, pues sostiene la afirmación
> central del trabajo: **un motor de ejecución agéntica en el que un agente puede reescribir
> su propio plan reinventa las piezas de la planeación clásica**, por lo que los resultados
> clásicos sobre esas piezas aplican, incluidos los que advierten sobre sus fallos.
>
> La instancia que motivó el trabajo es un motor de ejecución agéntica propio, OASys, en el
> que un agente puede reescribir el programa que lo ejecuta; aquí no se describe su
> implementación (que sigue cambiando), sino los conceptos que comparte con la literatura y
> la forma en que cada uno se implementa en este modelo.
>
> **Nota sobre la numeración:** las secciones siguen la 4.ª edición de Russell & Norvig
> (Pearson, 2020). Conviene verificar cada número contra el ejemplar físico antes de citarlas
> en el documento final.

---

## 1. La tabla

Cada fila lee de izquierda a derecha: el concepto tal como aparece en un motor de ejecución
agéntica, su nombre en la teoría de planificación y la pieza de código que lo implementa aquí.

| # | Concepto (motor de ejecución agéntica) | Russell & Norvig / teoría de planificación | Implementación en este modelo (MESA / código) |
|---|---|---|---|
| 1 | **Plan:** programa editable de instrucciones que el agente ejecuta | **Plan jerárquico.** Una tarea abstracta se refina en subtareas hasta llegar a acciones primitivas — cap. 11, §11.4 (HTN) | `book.py`: `Book(lines, pc)` y `Line(op, arg, locked)`, con las operaciones primitivas `GOTO`, `PICK`, `DELIVER` y `SCAN` |
| 2 | **Estado de ejecución:** en qué punto del plan va el agente | **Ejecución de un plan.** El estado de ejecución incluye la posición dentro del plan, no solo el estado del mundo — §11.5 | `Book.pc`; el agente ejecuta exactamente una línea por tick (`Collector._ejecutar_linea`) |
| 3 | **Monitorear el plan:** comparar lo que el plan supone contra lo que se observa | **Monitoreo de ejecución,** a nivel de acción, de plan o de objetivo — §11.5.3 | `Collector.observar()` marca una divergencia cuando el objetivo aparece en otra celda o la celda creída se ve vacía; un `PICK` que falla es el monitoreo de acción tardío de `OPEN_LOOP` |
| 4 | **Reescribir el plan** desde el punto de fallo | **Replanificación / reparación del plan,** en vez de replanificar desde cero — §11.5.3 | `Oracle.propose(RepairRequest) -> Proposal` calcula el sufijo nuevo y `Book.replace_suffix(from_idx, lines)` lo instala |
| 5 | **Alcance de edición:** porción del plan que el agente no puede modificar | **Invariantes del plan.** La reparación no puede violar los compromisos ya adquiridos | Todo plan termina con un `DELIVER` con `locked=True`, sea cual sea la política, y `replace_suffix` lanza `EditRejected` si la edición altera lo bloqueado o reescribe líneas ya ejecutadas; las pruebas de `tests/test_book.py` lo ejercitan |
| 6 | **Autorización de la edición:** si reescribir el plan requiere o no aprobación humana (supervisión humana, HiTL) | **Agente con autoridad acotada.** El espacio de acciones no es el mismo para todo agente — §2.4 | No se modela un humano en el bucle; su sustituto automático es el presupuesto de ediciones `B` de `GOVERNED` (ver fila 10) |
| 7 | **Observabilidad parcial:** qué parte del entorno tiene el agente en su contexto | **Estado de creencia.** El agente actúa sobre lo que cree, no sobre el estado real — §2.3.2, y §4.4 (búsqueda con observaciones parciales) | Radio de visión `r` (`None` = total); `Collector.belief` guarda la última posición conocida de cada recurso, y `celda_real_visible` solo entrega al oráculo la posición real si el agente la ve |
| 8 | **Reinicio en frío:** la edición aplica en la ejecución siguiente y el trabajo en curso se pierde | **Planeación de lazo abierto.** Se compila un plan y se ejecuta sin realimentación, lo cual falla en entornos dinámicos o no deterministas — §11.5 | `OPEN_LOOP` (no monitorea: replanifica solo cuando el plan falla, pagando `c` como las demás) y `COLD_RESTART` (`_aplicar_en_frio`: suelta la carga, que se cuenta en `carga_perdida`, y arranca con el plan nuevo) |
| 9 | **Reparación en caliente / en sitio:** la edición aplica sobre la ejecución en curso | **Planeación continua / lazo cerrado.** Monitorear y replanificar durante la ejecución — §11.5.3 | `CLOSED_LOOP` (`_aplicar_en_caliente`: parchea el sufijo y conserva el progreso) |
| 10 | **Cota de deliberación:** cuántas veces puede reescribirse el plan, habitualmente con un tope fijo de iteraciones | **Racionalidad limitada / metarazonamiento.** Cuánto razonar antes de actuar — §2.2 y la discusión de algoritmos *anytime* | `GOVERNED` = reparación en caliente con presupuesto `B` de ediciones; el barrido `gobernanza` **deriva** el efecto de `B` en vez de fijarlo |
| 11 | **Deliberar cuesta tiempo:** mientras el agente piensa, el mundo sigue cambiando | **Costo de la computación** como parte de la decisión (metarazonamiento) | `deliberation.py`: `Deliberation(duration=c)` con progreso e interrupción; el plan se calcula con el mundo del inicio de la deliberación |
| 12 | **Memoria del agente:** estado persistente fuera del contexto inmediato | **Agente basado en modelo:** estado interno del mundo que persiste entre percepciones — §2.4.3 | `Collector.belief`, que sobrevive a los reinicios de plan; `MODEL_BASED` es la política reactiva que decide sobre ella |
| 13 | **Composición de agentes:** un agente completo usado como herramienta opaca de otro | **Descomposición de tareas / subplan opaco.** El plan de nivel superior no ve el interior del subplan — §11.4 | Extensión de fase 2: `mesa.experimental.meta_agents` |
| 14 | **Ramas paralelas** sobre copias aisladas del estado | **Planes con ramas paralelas** sobre estados independientes | Fuera de alcance en esta versión |

### 1.1 Conceptos que entraron después del Avance 2

Las extensiones de [`../docs/roadmap-c4b.md`](../docs/roadmap-c4b.md) y
[`../docs/roadmap-c5.md`](../docs/roadmap-c5.md) llevaron al modelo los conceptos de las
sesiones de agentes basados en conocimiento (C4B) y de inferencia probabilística (C5), de
forma que la tabla gana filas cuya primera columna ya no es un mecanismo de un motor agéntico
sino la pregunta que el agente se hace sobre su propia creencia antes de reparar.

| # | Concepto (pregunta del agente) | Russell & Norvig / teoría | Implementación en este modelo (MESA / código) |
|---|---|---|---|
| 15 | **Base de conocimiento:** lo que el agente sabe, separado de cómo lo calcula | **Agente basado en conocimiento,** nivel de conocimiento frente a nivel de implementación (Newell, 1982) — §7.1 | `conocimiento.py`: `BaseConocimiento`, que usa `KNOWLEDGE_BASED`; `logica.py`: `KnowledgeBase`, contra la que se prueba la primera |
| 16 | **Contar lo visto y preguntar** | **`TELL` / `ASK`** — §7.1 | `BaseConocimiento.percibir` (TELL de lo visto en cada tick) y las tres consultas: `posible`, `clave` y `plan_valido`; `KnowledgeBase.tell`, `ask` y `ask_status` (verdadero, falso o desconocido) |
| 17 | **Hechos con fecha:** dónde estaba un recurso *entonces* | **Fluentes y axiomas de estado sucesor** — §7.7.1 | `Visto(r,c,t)`, `¬En(r,c,t)` y `Recogido(r,t)`, y el axioma de deriva $En(r,c,t) \Rightarrow \bigvee_{c' \in N^+(c)} En(r,c',t+1)$ (docstring de `conocimiento.py`) |
| 18 | **Lo que se observó no se desdice** | **Monotonía** de la implicación lógica — §7.5 | Ninguna observación se retira; lo que caduca es la conclusión «está ahí ahora», que se deriva. Es la respuesta a la Tarea 4 de C4B: con recursos que se mueven la monotonía no se rompe, se indexa por tiempo |
| 19 | **Decidir si algo se sigue de lo que sé** | **Enumeración de modelos, CNF y DPLL** — §7.4–§7.6 | `logica.py`: `tt_entails`, `to_clauses`, `dpll` y `exactly`; la prueba cruzada de `tests/test_conocimiento.py` codifica una retícula de 4×4 y exige `falso` fuera de la región y `desconocido` dentro |
| 20 | **Dónde puede estar un recurso que no veo** | **Estimación de estado lógica / estado de creencia** — §4.4 y §7.7.3 | `RegionPosible` (`conocimiento.py`): se fija al ver, se expande por cada deriva (`expandir`, distancia geodésica) y se poda con lo visto; el agente elige objetivo por el peor caso sobre ella |
| 21 | **Aprender cuánto cambia el mundo** | **Aprendizaje bayesiano de parámetros,** prior conjugado Beta para una tasa de Bernoulli — §20.2 | `BetaBernoulli` (`filtro.py`): cada recurso cuya celda previa sigue a la vista es un ensayo; reporter `lambda_estimado` |
| 22 | **Dónde *probablemente* está un recurso que no veo** | **Filtrado *forward*** (predicción con el modelo de transición, corrección con la observación) — §14.2 | `FiltroRecurso` y `MallaFiltro` (`filtro.py`), cuyo soporte es exactamente la región de la fila 20, lo cual se prueba tick a tick |
| 23 | **Reparar o mantener sin un umbral elegido a mano** | **Principio de utilidad esperada máxima** — §16.1 | `CreenciaBayesiana.plan_valido`: se repara si y solo si $c < (1-q)(c+k)$; el objetivo se elige por costo esperado $d/q$ |
| 24 | **Inferir los parámetros de un despliegue a partir de su telemetría** | **Computación bayesiana aproximada (ABC) por rechazo** (Beaumont et al., 2002; C5 §12), sin contraparte directa en R&N | `calibracion.py`: tabla de referencia en `results/abc.parquet`, `abc_rechazo` y `recomendar`, que lee la política sugerida en la frontera bajo la posterior de (λ, p) |
| 25 | **Qué parámetro vale la pena medir** | **Análisis de sensibilidad** por descomposición de la varianza (η²; C5 §13), sin contraparte directa en R&N | `sensibilidad.py`: η² de un factor y η² parcial sobre los CSV guardados, por política y para la diferencia `OPEN_LOOP − CLOSED_LOOP` |

---

## 2. Las tres asimetrías

La tabla muestra correspondencias, aunque lo interesante son los tres lugares donde **no**
hay correspondencia, dado que ahí cada tradición tiene algo que la otra no.

### 2.1 Lo que los motores agénticos tienen y la IA clásica no

**Espacio de acciones abierto.** La planeación clásica exige enumerar operadores con
precondiciones y efectos declarados, mientras que un agente LLM no necesita esa enumeración y
puede proponer una acción que nadie modeló de antemano. Es una ganancia real de
expresividad, y es la razón por la que un motor de ejecución agéntica puede atacar dominios
que un planificador STRIPS no puede ni formular.

El costo es igualmente real, pues **sin operadores declarados no hay garantías** (no se
puede demostrar completitud, ni optimalidad, ni terminación). El tope fijo de iteraciones
de deliberación es el síntoma, por lo que cuando no se puede acotar la deliberación por
análisis, se la acota por decreto.

### 2.2 Lo que la IA clásica tiene y los motores agénticos no

Tres cosas, en orden de importancia:

1. **Medición:** Un motor que permite auto-editarse no trae de serie ninguna métrica sobre
   si hacerlo mejora el resultado, mientras que MESA aporta `DataCollector` y `batch_run`
   con réplicas y semillas, es decir, barridos de parámetros con curvas en vez de anécdotas,
   lo cual convierte "parece que reparar en caliente sería mejor" en "reparar en caliente
   gana bajo tales condiciones y pierde bajo tales otras".
2. **Caracterización del entorno:** R&N §2.3.2 da el vocabulario (observable, determinista,
   episódico, estático, discreto, multi-agente), de forma que un motor que implementa
   observabilidad parcial o ejecuciones episódicas sin nombrarlas no puede razonar sobre qué
   arquitectura de agente corresponde a cada combinación.
3. **Modelo de costo de la deliberación:** El resultado clásico (beneficio creciente en
   dinamismo contra costo aproximadamente constante, por lo que existe un cruce) predice que
   un agente con capacidad de auto-edición y sin costo asociado entrará en *thrashing*.
   Exigir autorización humana para cada edición lo mitiga, pero es una solución y no un
   modelo.

### 2.3 Lo que ninguna de las dos resuelve

**La calidad del replanificador es un parámetro externo.** En planeación clásica el
replanificador es un algoritmo con propiedades demostradas, mientras que en un agente LLM es
un modelo estadístico cuya tasa de acierto no se conoce a priori y cambia con la versión del
modelo.

Este trabajo no resuelve esa asimetría sino que la **parametriza**, dado que la competencia
`p` del oráculo es una entrada del experimento y no un supuesto oculto. El resultado
buscado no es "los agentes LLM deberían auto-editarse", sino "auto-editarse conviene cuando
la competencia supera `p*` y el costo está por debajo de `c*`, dado un dinamismo λ", que es
un enunciado que sobrevive al cambio de modelo. Vale la pena anotarlo: los datos mostraron
que la competencia `p` pesa más sobre el lazo abierto (que replanifica poco) que sobre el
lazo cerrado, que la observabilidad sube el nivel de todas las políticas sin decidir por sí
sola a favor de reparar en caliente, y que la variable decisiva terminó siendo el costo de
deliberar `c`, que con un entorno rápido hace preferible no planificar en absoluto (ver el
cuaderno, §4, §6 y §7). Cabe mencionar que la calibración ABC (fila 24) vuelve operable el
otro lado de la asimetría, pues estima λ a partir de la telemetría de un despliegue con
precisión moderada, aunque no identifica `p`: con un motor que solo replanifica al fallar,
los errores del replanificador se confunden con el dinamismo, de forma que medir la
competencia exige telemetría que hoy no se registra.

---

## 3. Cómo se usa esta tabla en el informe

- **Marco teórico:** Las filas 1–9 justifican que el objeto de estudio es planeación
  clásica y no una novedad de los LLM.
- **Metodología:** La última columna muestra que cada concepto tiene una contraparte
  ejecutable, de forma que nada queda solo en la prosa.
- **Discusión:** Las secciones 2.1–2.3 son el aporte conceptual, es decir, qué le presta
  cada tradición a la otra.
- **Extensiones:** Las filas 15–25 conectan el modelo con las sesiones de lógica e
  inferencia probabilística, y cada una tiene una prueba o un barrido que la respalda.
- **Trabajo futuro:** Las filas 13–14 son la extensión de meta-agentes y de planes con
  ramas paralelas.
