# 01 — Diccionario: OASys ↔ Russell & Norvig ↔ MESA

> Este documento es la columna vertebral del informe académico. Sostiene la afirmación
> central del trabajo: **un motor de agentes LLM construido desde cero, sin referencia a la
> literatura, reinventó las piezas de la planeación clásica** — y por lo tanto los resultados
> clásicos sobre esas piezas aplican, incluidos los que advierten sobre sus fallos.
>
> Cada fila cita el archivo real de OASys (verificado, no inferido) y la sección de Russell &
> Norvig correspondiente.
>
> **Nota sobre la numeración:** las secciones siguen la 4.ª edición (Pearson, 2020). Conviene
> verificar cada número contra el ejemplar físico antes de citarlas en el documento final.

---

## 1. La tabla

| # | OASys (implementación) | Russell & Norvig (concepto) | MESA (cómo se modela aquí) |
|---|---|---|---|
| 1 | `Device → Books → Pages → Lines → Cells`; una Cell es una expresión del DSL — `backend/src/model/hierarchy.rs` | **Plan jerárquico.** Una tarea abstracta se refina en subtareas hasta llegar a acciones primitivas — cap. 11, §11.4 (*Hierarchical Planning*, HTN) | `book.py`: `Book(lines: list[Line], pc: int)`; `Line(op, arg, locked)` |
| 2 | Contador de programa + pila de llamadas: `PageRunner { line_idx, cell_idx, call_stack: Vec<Frame>, store }` — `backend/src/engine/scheduler/mod.rs` | **Ejecución de un plan.** El estado de ejecución es la posición dentro del plan, no solo el estado del mundo | `Book.pc`; el agente ejecuta `book.lines[pc]` por tick |
| 3 | `readBook` (modo `Allow`) — `backend/src/agent/tools/builtin/oasys_surface.rs:98` | **Monitoreo de ejecución.** Comparar las precondiciones de la siguiente acción contra lo observado — cap. 11, §11.5.3 (*Online Planning*) | `agents.py`: `detect_divergence(line, percept)` antes de ejecutar cada línea |
| 4 | `editBook` (modo `Ask`) — parcha el fuente `old_str`→`new_str` — `oasys_surface.rs:110`, implementación en `backend/src/agent/tools/book.rs` | **Replanificación.** Reparar el plan desde el punto de fallo en vez de replanificar desde cero — cap. 11, §11.5.3 | `oracle.py`: `propose_edit(book, divergence, belief) -> Book`; `book.replace_suffix(...)` |
| 5 | `@lock` + `validate_edit(old, new, caps)`: toda página/línea/celda bloqueada debe renderizar byte a byte idéntica — `backend/src/agent/tools/governance.rs:72` | **Invariantes del plan.** La reparación no puede violar los compromisos ya adquiridos | `Line.locked`; `Book.replace_suffix` rechaza la edición que toque una línea bloqueada |
| 6 | `ToolMode { Allow, Ask, Deny }` por agente y por herramienta — `backend/src/model/workspace.rs` | **Acciones con precondiciones y agente con autoridad limitada.** El espacio de acciones no es el mismo para todo agente — §2.4 | Presupuesto de ediciones `B` en `GovernedAgent`; conjunto de operadores por arquitectura |
| 7 | Set `ignore`: páginas que un agente no ve; `redact_hidden_pages` las borra del fuente que recibe, cabecera incluida — `backend/src/agent/tools/book.rs` | **Observabilidad parcial.** El agente actúa sobre un estado de creencia, no sobre el estado real — §2.3.2, y cap. 4 §4.4 (búsqueda con observaciones parciales) | Radio de visión `r`; `belief` = último estado conocido fuera del radio |
| 8 | **`cold` run (clock-edge):** el scheduler ejecuta `device_snapshot = rt.device.clone()`; `editBook` muta el runtime vivo, así que la edición aplica en la corrida **siguiente** — `backend/src/engine/mod.rs:142` | **Planeación de lazo abierto.** Se compila un plan y se ejecuta sin realimentación; falla en entornos dinámicos o no deterministas — cap. 11, §11.5 | Políticas `OPEN_LOOP` y `COLD_RESTART` en `agents.py` |
| 9 | **`run=hot`:** declarado en el DSL, **no implementado** — `"[Engine] run=hot declared but not implemented; running cold (snapshot)"`, `backend/src/engine/mod.rs:134` | **Planeación continua / lazo cerrado.** Monitorear y replanificar durante la ejecución — cap. 11, §11.5.3 | Política `CLOSED_LOOP` |
| 10 | `const MAX_ITER: usize = 5;` — `backend/src/agent/executor/mod.rs:14`; excederlo es error duro de la celda | **Cota de deliberación.** Cuánto puede razonar un agente antes de tener que actuar — racionalidad limitada; §2.2 y la discusión de algoritmos *anytime* | Costo `c` por edición + presupuesto `B`; el barrido **deriva** el valor en vez de fijarlo |
| 11 | Devices sellados: `import device <alias>` convierte un device entero en una tool invocable; nunca se fusiona con las páginas — `backend/src/agent/tools/compose.rs` | **Descomposición de tarea / subplan opaco.** El plan de nivel superior no ve el interior del subplan — cap. 11, §11.4 | Extensión fase 2: `mesa.experimental.meta_agents` |
| 12 | `CALL` multi-objetivo = fork/join sobre copias aisladas del store, tope de profundidad 16 — `backend/src/engine/scheduler/fork.rs` | **Planes con ramas paralelas** sobre estados independientes | Fuera de alcance en v1 |
| 13 | El estado sobrevive en disco, no en contexto: `#writeFile("agent/state.json")` / `#readFile(...)`; los runs de hook son *stateless* y de un solo disparo — `docs/feats/04-device-researcher.md` | **Agente basado en modelo:** memoria externa del estado del mundo que persiste entre episodios — §2.4.3 | `ModelBasedAgent.belief`, persistente entre reinicios de plan |

---

## 2. Las tres asimetrías

La tabla muestra correspondencias. Lo interesante son los tres lugares donde **no** hay
correspondencia — ahí es donde cada tradición tiene algo que la otra no.

### 2.1 Lo que OASys tiene y la IA clásica no

**Espacio de acciones abierto.** La planeación clásica exige enumerar operadores con
precondiciones y efectos declarados. Un agente LLM no necesita esa enumeración: puede
proponer una acción que nadie modeló de antemano. Es una ganancia real de expresividad, y es
la razón por la que OASys puede atacar dominios que un planificador STRIPS no puede ni
formular.

El costo es igualmente real: **sin operadores declarados no hay garantías**. No se puede
demostrar completitud, ni optimalidad, ni terminación. `MAX_ITER = 5` es el síntoma: cuando
no se puede acotar la deliberación por análisis, se la acota por decreto.

### 2.2 Lo que la IA clásica tiene y OASys no

Tres cosas, en orden de importancia:

1. **Medición.** OASys no tiene *ninguna* métrica sobre si auto-editarse mejora el
   resultado. MESA aporta `DataCollector` + `batch_run` con réplicas y semillas: barridos de
   parámetros con curvas en vez de anécdotas. Esto es lo que convierte "siento que `hot`
   sería mejor" en "`hot` gana por encima de λ\*, y por debajo pierde".
2. **Caracterización del entorno.** R&N §2.3.2 da el vocabulario: observable / determinista
   / episódico / secuencial / estático / dinámico / discreto / multi-agente. OASys implementó
   observabilidad parcial (`ignore`) y ejecución episódica (hooks *stateless*) **sin
   nombrarlas**, y por lo tanto sin poder razonar sobre qué arquitectura de agente
   corresponde a cada combinación.
3. **Modelo de costo de la deliberación.** El resultado clásico —beneficio creciente en
   dinamismo contra costo aproximadamente constante, luego hay cruce— predice que un agente
   con capacidad de auto-edición y sin costo asociado entrará en *thrashing*. OASys mitiga
   eso con `editBook: Ask`, poniendo a un humano en el bucle. Es una solución, pero no es un
   modelo.

### 2.3 Lo que ninguna de las dos resuelve

**La calidad del replanificador es un parámetro externo.** En planeación clásica el
replanificador es un algoritmo con propiedades demostradas. En un agente LLM es un modelo
estadístico cuya tasa de acierto no se conoce a priori y cambia con la versión del modelo.

Este trabajo no resuelve esa asimetría: la **parametriza**. La competencia `p` del oráculo es
una entrada del experimento, no un supuesto oculto. El resultado no es "los agentes LLM
deberían auto-editarse", sino "auto-editarse conviene cuando la competencia supera `p*` y el
costo está por debajo de `c*`, dado un dinamismo λ" — un enunciado que sobrevive al cambio de
modelo.

---

## 3. Cómo se usa esta tabla en el informe

- **Sección de marco teórico:** las filas 1–9 justifican que el objeto de estudio es
  planeación clásica, no una novedad de los LLM.
- **Sección de metodología:** la columna MESA muestra que cada concepto tiene una
  contraparte ejecutable; nada queda en la prosa.
- **Sección de discusión:** §2.1–2.3 son el aporte conceptual — qué le presta cada tradición
  a la otra.
- **Sección de trabajo futuro:** las filas 11–12 son la extensión de meta-agentes.
