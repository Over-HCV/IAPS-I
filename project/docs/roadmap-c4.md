# Roadmap C4 — Lo que la sesión de predador–presa aporta al proyecto

Documento de trabajo derivado de [`content/presentation/IA_C4.ipynb`](../../content/presentation/IA_C4.ipynb)
(predador–presa en Mesa 3.5.1, sesión 4A). No es un plan de entrega sino una lista de mejoras
**opcionales y acumulables**, pensada para avanzar de a poco, de forma que cada paquete es
independiente, deja el repositorio en estado entregable y se marca `[x]` al completarse.

**Cómo usarlo.** Se trabaja un paquete a la vez, siguiendo la ruta conjunta con
[`roadmap-c4b.md`](roadmap-c4b.md) (§Orden), y tras cada paquete `uv run pytest project/tests -q`
debe quedar en verde, así como el cuaderno debe reflejar el cambio si el paquete toca barridos o
figuras.

## Resumen

| # | Paquete | Pregunta que responde | Archivos principales | Costo |
|---|---|---|---|---|
| 1 | Orden de activación aleatorio | ¿Dependen las conclusiones de que el collector siempre mueva primero? | `model.py` | Bajo |
| 2 | Tira de instantáneas (extra) | ¿Cómo se ve la evolución del mecanismo en una sola figura? | `animacion.py` | Bajo |
| 3 | Curvas temporales agregadas | ¿*Cuándo* se separan las políticas, no solo cuánto? | `experiments.py`, `analysis.py` | Medio |
| 4 | Barrido de escasez | ¿Depende el valor de replanificar de la abundancia de recursos? | `experiments.py`, `analysis.py` | Medio |
| 5 | Narrativa de la frontera λ–c | ¿Por qué la frontera tiene la forma que tiene? | `notebook.ipynb` | Bajo |

---

## Paquete 1 — Orden de activación aleatorio

**Origen (C4).** El `CustomScheduler` de la sesión activa los agentes en orden aleatorio y lo
justifica: *«el orden aleatorio evita ventajas sistemáticas por turno»*. Es la lección clásica
de los ABM: quien mueve primero obtiene información (o la pierde) de forma sistemática.

**El gap.** En `OASysWorld.step()` (`model.py:255`) el collector **siempre** actúa antes de que
los recursos deriven. El agente nunca experimenta un mundo que se movió en su propio tick: la
sincronización de las divergencias (y con ella `latencia_deteccion`) depende de ese orden fijado
a mano. Es una amenaza de validez interna del experimento, no un bug.

**Diseño.** Parámetro `orden_aleatorio: bool = False`. Con `True`, cada tick se sortea con
`self.random` (reproducible) si el collector actúa antes o después de la deriva:

```python
collector_primero = self.random.random() < 0.5
if collector_primero:
    self.collector.step()
    recursos.shuffle_do("step")
else:
    recursos.shuffle_do("step")
    self.collector.step()
```

La alternativa «pura» —interleaved completo de `[collector, *recursos]` barajado, con guarda
para agentes ya removidos (patrón `shuffle_do` de C4)— también sirve, pero el sorteo por tick
captura el sesgo sistemático con un cambio mínimo.

**Checklist**

- [x] `orden_aleatorio` en la firma de `OASysWorld.__init__`, guardado como atributo
- [x] `step()` sortea el orden con `self.random` cuando está activo
- [x] Test: con `rng` fijo y `orden_aleatorio=True`, dos corridas idénticas dan métricas idénticas (determinismo)
- [x] Test: con `False` (default), el orden es collector-primero siempre — el resto de la suite actúa como regresión
- [x] Control de robustez (opcional): correr un subconjunto del barrido `principal` con `orden_aleatorio=True` y verificar que el **signo** de `delta_hot_vs_cold` (`analysis.py:110`) no cambia
- [x] Nota de una línea en `info/02-design.md` (clasificación del entorno: el orden es un parámetro, no un supuesto)

**Aceptación.** `uv run pytest project/tests -q` queda en verde y el control de robustez (si se
corre) muestra la misma conclusión cualitativa para la reparación en caliente frente al reinicio
en frío.

---

## Paquete 2 — Tira de instantáneas

**Origen (C4).** La sesión comunica la evolución con una fila de seis instantáneas
(`[0, 60, 120, 180, 240, 299]`): una figura estática que cuenta toda la película. Es su figura
más citada.

**El gap, en parte ya cubierto.** La evolución ya se ve con los reproductores jshtml (play, pausa
y deslizador) del cuaderno final (`anim.mostrar`, `animacion.py:732`, serializado con
`a_jshtml`, `animacion.py:716`) y del Avance 2 (`docs/avance-02/avance-02.ipynb`, que muestra
las tres políticas lado a lado), por lo que este paquete pasa a ser un extra de presentación.
Lo que sigue faltando es una figura **estática** de evolución, dado que `figura_estatica`
(`animacion.py:683`) dibuja solo el último frame con la traza encima, y esa tira sigue siendo
útil como respaldo donde no corre JavaScript (PDF, GitHub) y como material para las diapositivas
(cabe mencionar que la presentación vale el 10 % de la nota).

**Diseño.** `figura_tira(frames, modelo, pasos=None, ncols=6)`: selecciona ticks equidistantes
(incluyendo el 0 y el último), dibuja `_panel_grid` por tick en una fila, y resalta las ediciones
con `_flashes` igual que la película. Extender `Modo` con `"tira"` y despachar desde `mostrar()`.

**Checklist**

- [x] Helper `_ticks(frames, pasos=None)`: default equidistantes, sin duplicados, primero y último siempre incluidos
- [x] `figura_tira(...)` reutilizando `_panel_grid` y `_flashes`
- [x] `Modo = Literal["animacion", "estatico", "tira"]` + rama en `mostrar()`
- [x] Test: `_ticks` devuelve índices válidos, únicos, con extremos
- [x] Test: `figura_tira` devuelve una figura con el número esperado de ejes
- [ ] Celda en el cuaderno: corrida `CLOSED_LOOP` con λ alto y una edición visible en la tira
- [x] Exportar un `.png` a `results/animaciones/` para la presentación

**Aceptación.** La tira renderiza en el cuaderno y se entiende sin narración: dónde estaba el
plan, dónde se rompió, qué sufijo se reescribió.

---

## Paquete 3 — Curvas temporales agregadas

**Origen (C4).** La figura central de la sesión es una **serie de tiempo**: poblaciones contra
paso, con el ciclo Lotka–Volterra a la vista. Lo que enseña no es el valor final sino la
*dinámica* — el retardo con que los predadores siguen a las presas.

**El gap.** Las cinco figuras de barrido de `analysis.py` (`FIGURAS_CLI`, `analysis.py:492`:
`fig_frontera`, `fig_hot_vs_cold`, `fig_competencia`, `fig_observabilidad`, `fig_gobernanza`)
plotean todas **valor final frente a parámetro**, ya que `ejecutar` pide a `batch_run` solo la
última fila de cada corrida (`data_collection_period=-1`, `experiments.py:146`), de modo que la
serie por tick que el `DataCollector` ya recolecta se pierde. No existe ninguna figura de métrica
contra tick promediada sobre réplicas, es decir, el equivalente en el modelo de la serie temporal
de C4, que es la figura que mostraría **cuándo** se separan las políticas (el costo del retardo de
deliberación hecho visible).

**Diseño.**

- **Runner propio:** `correr_dinamica()` en `experiments.py` itera políticas × λ ∈ {0.0, 0.1,
  0.25, 0.5} × `SEMILLAS` (c=5, p=0.9, r=3, `BASE`), corre `OASysWorld` directo y extrae
  `datacollector.get_model_vars_dataframe()` por corrida.
- **Políticas:** Se omite `GOVERNED`, que sin presupuesto es exactamente `CLOSED_LOOP` (§4 del
  cuaderno), por lo que quedan cinco.
- **Salida:** Formato largo, una fila por (corrida, tick) con columnas
  `rng, politica, lambda_dinamismo, tick` más las métricas (`entregas`, `utilidad_neta`,
  `divergencias_reales`, `n_ediciones`, `pasos_deliberando`, `carga_perdida`).
- **Tamaño:** Sin decimar serían 5 políticas × 4 λ × 30 semillas × 401 ticks ≈ 241k filas, del
  orden de 25–30 MB en CSV (estimado, no medido), lo cual es demasiado para el repositorio. Se
  guarda entonces en `results/dinamica.parquet` (`pyarrow` ya está en las dependencias de
  `pyproject.toml`) y se decima a un tick de cada 5, conservando siempre el 0 y el último, lo
  que deja ≈ 49k filas, más que suficientes para una curva con banda de error.
- **Análisis:** `cargar_dinamica()`, `agregar_tiempo(df, metrica)` (media ± SEM sobre semillas,
  en el mismo formato largo que `agregar`) y `fig_dinamica(metrica="entregas")`, que reutiliza
  `lineas` (`analysis.py:337`) con x=tick, serie=politica y faceta=lambda_dinamismo.

**Checklist**

- [x] `correr_dinamica(cada=5)` en `experiments.py` + flag `--dinamica` en el CLI, escribiendo parquet
- [x] `cargar_dinamica()` con el mismo contrato de errores que `cargar()` (`analysis.py:47`), es decir, el comando exacto si falta el archivo
- [x] `agregar_tiempo()` y `fig_dinamica()` en `analysis.py`
- [x] Test smoke: grilla chica, pocos pasos → columnas esperadas, y con `cada=k` los ticks guardados son los múltiplos de `k` más el último
- [x] Test: `agregar_tiempo` calcula media/SEM correctas sobre un DataFrame sintético
- [ ] Sección en el cuaderno: punto de separación entre políticas por λ; lectura frente a `latencia_deteccion` y el thrashing

**Aceptación.** Una figura con banda de error de 30 réplicas donde se distingue el tick en que el
lazo cerrado se despega del abierto (o del frío) y cómo ese punto se mueve con λ (`c` queda fijo
en 5 en este paquete, por lo que su efecto no se lee aquí).

---

## Paquete 4 — Barrido de escasez

**Origen (C4).** En la sesión, la tasa de regeneración del pasto fija la **capacidad de carga**
y con ella toda la dinámica estable. El cuarto pilar: el recurso renovable y distribuido.

**El gap.** `n_resources` y `capacidad` están fijos en `BASE` para los seis barridos
(`experiments.py:41-47`), por lo que la abundancia nunca se mueve y el experimento no sabe si el
valor de replanificar depende de ella.

**Por qué dos regímenes.** Tras la corrección de la regla de costo (2026-10-09), con `r=3` y
`c=5` ninguna política con plan gana en todos los λ: el lazo cerrado queda apenas por encima del
abierto a λ=0.1 y 0.25 (89.0 contra 86.0 y 56.0 contra 47.0) y por debajo a λ=0.5 (10.0 contra
27.0), mientras que desde λ=0.25 las dos quedan por debajo de `MODEL_BASED` (86.0 y 98.3 a
λ=0.25 y 0.5), que nunca paga deliberación (§4 del cuaderno). Es entonces un régimen **mixto**,
lo cual lo vuelve más informativo que antes para la escasez, pero no basta para saber qué
pasa donde replanificar sí gana. Vale la pena anotar que `r=∞` por sí solo tampoco basta,
pues con `c=5` y `p=0.9` el lazo abierto sigue arriba con visión total (129.5 contra 114.5 de
utilidad media, y `CLOSED_LOOP` cae a 0.0 a λ=0.5 por thrashing, frente a 34.0 del lazo
abierto, calculado de `results/observabilidad.csv`), de modo que el único régimen medido donde
`CLOSED_LOOP` domina sigue siendo el del control 2 (`c=0`, `p=1`, `r=∞`,
`experiments.py:77-87`). Por eso el barrido se corre en dos regímenes, el mixto y uno donde
replanificar gana, y la pregunta pasa a ser cómo cambian las distancias entre políticas con la
escasez en cada uno.

**Hipótesis (escribir el veredicto antes de ver la figura, como exige `info/00-rationale.md`).**
Con recursos escasos los viajes entre recogidas son más largos, el objetivo pasa más tiempo
expuesto a la deriva, y las divergencias golpean más ⇒ *la reparación debería valer más con
escasez*. Si el resultado es el contrario, la explicación tendrá que ver con el costo de
oportunidad de deliberar cuando sobran objetivos.

**Diseño.** Dos entradas en `SWEEPS` × `n_resources ∈ {2, 4, 8, 16}` × λ ∈ {0.0, 0.1, 0.25,
0.5} × 30 semillas:

- **`escasez` (régimen mixto):** `{MODEL_BASED, OPEN_LOOP, COLD_RESTART, CLOSED_LOOP}`, `r=3`,
  `c=5`, `p=0.9` → 4 × 4 × 4 × 30 = 1.920 corridas.
- **`escasez_inf` (replanificar gana):** `{OPEN_LOOP, COLD_RESTART, CLOSED_LOOP}`, `r=None`,
  `c=0`, `p=1.0` → 3 × 4 × 4 × 30 = 1.440 corridas.

En total son **3.360 corridas**. Se omite `GOVERNED` (sin presupuesto es `CLOSED_LOOP`) y
`REFLEX`, mientras que `MODEL_BASED` entra solo en el régimen mixto porque es la mejor política
medida con λ alto y `c≥2`, de forma que la pregunta honesta allí ya no es solo si replanificar
vale más con escasez sino si vale más que **no planificar**; en `escasez_inf` no hace falta,
pues ese régimen existe para aislar el caso en que replanificar es gratis y exacto. Si KB-2 de
[`roadmap-c4b.md`](roadmap-c4b.md) ya está hecho y su H1 se sostiene, se añade
`KNOWLEDGE_BASED` a `escasez` (+480 corridas). Cabe mencionar que la celda
`n_resources=8` de cada régimen reproduce, con las mismas semillas y parámetros, filas que ya
existen (`principal.csv` con `c=5` y `control2.csv`, respectivamente, ambos re-corridos con la
regla de costo corregida), lo cual sirve de regresión gratuita.

**Checklist**

- [x] Entradas `escasez` y `escasez_inf` en `SWEEPS` (`experiments.py:49`)
- [x] `fig_escasez()` en `analysis.py` (x=`n_resources`, serie=`politica`, faceta=`lambda_dinamismo`, una fila por régimen)
- [x] Correr: `uv run python -m project.experiments --sweep escasez --procesos 0` y lo mismo con `escasez_inf`
- [x] Test: la celda `n_resources=8` coincide exactamente con las filas correspondientes de `principal.csv` y `control2.csv`
- [x] Actualizar la tabla de barridos en `project/README.md` (8.640 → 12.000 corridas, más las de KB-2 si ya se corrieron) — hecho: 13 barridos y 16.260 corridas, con KB-2 y C5-B incluidos (2026-11-06)
- [x] `uv run python -m project.analysis --controles` sigue en verde tras los CSV nuevos
- [ ] Sección en el cuaderno: hipótesis, figura, veredicto por régimen

**Resultado (2026-11-06).** Se añadió `KNOWLEDGE_BASED` a `escasez` (2.400 corridas; H1 de KB-2
se sostuvo en parte) y `escasez_inf` corrió 1.440; las celdas `n_resources=8` reproducen
`principal`, `conocimiento` y `control2` exactamente. **La hipótesis se refuta en los dos
regímenes:** reparar vale igual o menos con escasez, no más. Con `r=∞` y `c=0`, a λ=0.5,
`CLOSED_LOOP − OPEN_LOOP` crece con la abundancia (+36.7 ± 4.0 con 2 recursos, +62.0 ± 5.0
con 16) y `CLOSED_LOOP − COLD_RESTART` también (+122 a +245). En el régimen mixto el lazo
cerrado no gana de forma consistente, y la ventaja de `MODEL_BASED` sobre el mejor planificador
crece con la abundancia (a λ=0.5, +13.0 ± 3.1 con 2 recursos y +96.0 ± 13.0 con 16). La
lectura es la del costo de oportunidad: cuando sobran objetivos, cada tick deliberando cuesta
más entregas que se dejan de hacer. `KNOWLEDGE_BASED` supera al lazo cerrado a λ=0.5 en todo
`n` (+6 a +21).

**Aceptación.** Los dos barridos corren en minutos (`--procesos 0`), la figura renderiza, la
regresión de `n_resources=8` pasa y los cuatro controles de `--controles` (1, 2, 3 y el 6,
`B=0` ⇒ `GOVERNED` ≡ `OPEN_LOOP`) siguen pasando.

---

## Paquete 5 — Narrativa de la frontera λ–c

**Origen (C4).** La sección *¿Qué hace estable el sistema?* — los «cuatro pilares» — es la pieza
pedagógica más fuerte de la sesión: primero el diagnóstico de por qué moría todo, luego los
mecanismos (recurso renovable, acoplamiento débil, respuesta con retardo, amortiguadores).

**El gap.** El cuaderno interpreta figura por figura, pero no hay una sección que explique la
**frontera** λ–c como un sistema. La estructura de C4 (primero el diagnóstico, luego los
mecanismos) sirve como plantilla de exposición, con la advertencia de que el paralelo con
predador–presa es una **analogía y no un mecanismo**: el modelo no tiene poblaciones acopladas ni
ciclos, de modo que cada pilar se usa para ordenar la explicación y la evidencia tiene que salir de
los barridos del proyecto, no de Lotka–Volterra.

**Diseño.** Markdown en el cuaderno, tras `fig_frontera`, con esta estructura (todas las cifras son
de la versión corregida del 2026-10-09, `p=0.9` y `r=3` salvo que se diga otra cosa):

1. **El diagnóstico: deliberar se come el tiempo.** Con `c=0` el lazo abierto es la mejor política
   (o empata) en todo λ, pero desde `c=2` y λ≥0.25 la mejor pasa a ser `MODEL_BASED`, que actúa sobre sus
   creencias sin plan y nunca paga deliberación (a λ=0.5 y `c=5` rinde 98.3, frente a 27.0 del
   lazo abierto y 10.0 del cerrado, §4), y la razón se lee en el mecanismo: en esa celda
   `CLOSED_LOOP` pasa 282.2 de sus 400 ticks deliberando y `OPEN_LOOP` 153.6, de forma que el
   frente que importa con dinamismo alto ya no es «comprometerse frente a reparar» sino «planificar
   frente a no planificar». Entre las dos políticas con plan la distancia es pequeña y de signo
   variable (89.0 contra 86.0 a favor del cerrado a λ=0.1 con `c=5`, pero 96.0 contra 96.0 con
   `c=0`).
2. **La observabilidad, un desplazador y no el diagnóstico.** El radio mueve sobre todo el nivel
   de utilidad de todas las políticas (promediando λ con `c=5`, `CLOSED_LOOP` pasa de 47.9 con
   `r=1` a 114.5 con `r=∞` y `OPEN_LOOP` de 48.0 a 129.5, §7), mientras que la ventaja media del
   lazo abierto sobre el cerrado es casi nula con `r=1` y `r=3` (48.0 contra 47.9 y 63.3 contra
   62.1) y moderada con visión total. El mecanismo de la creencia obsoleta sigue existiendo,
   pues sin ver el objetivo el oráculo recibe `true_goal=None` y repara hacia la creencia aunque
   su sorteo de competencia salga a favor (`oracle.py:233-235`), solo que ahora afecta también
   al lazo abierto, cuyas replanificaciones tras un fallo pasan por el mismo oráculo, lo cual se
   ve en que subir `p` de 0.5 a 1.0 a λ=0.25 mueve más al lazo abierto (36.7 a 61.0) que al
   cerrado (48.3 a 59.7, §6). Que con `c=0` el lazo abierto siga arriba a λ=0.25 (111.7 contra
   86.0) indica que monitorear sobre creencias viejas cuesta incluso cuando deliberar es gratis,
   y KB-2 de [`roadmap-c4b.md`](roadmap-c4b.md) es el experimento que pone a prueba esa parte,
   ya que cambia la elección de objetivo y el criterio de reparación usando solo lo que el
   agente sabe, sin tocar el oráculo.
3. **Respuesta con retardo (analogía con la reproducción lenta del predador).** Deliberar ocupa
   `c` ticks y el plan se calcula al empezar y se retiene (`agents.py:460-481`), de modo que llega
   desactualizado si el mundo se movió. Esta parte sí es mecanismo del modelo, y el Paquete 3 la
   hace visible en el tiempo.
4. **El thrashing de replanificación.** Cada divergencia nueva interrumpe la deliberación en curso
   y los ticks gastados se pierden (`agents.py:542-551`), lo cual con `r=∞`, `c=5` y λ=0.5 deja a
   `CLOSED_LOOP` en utilidad 0.0, frente a 34.0 del lazo abierto, que también delibera tras cada
   fallo pero no se deja interrumpir (§7). En el Avance 2, con visión total y replanificador
   exacto, bastó `c=1` para invertir la ventaja (79.8 contra −11.3 a λ=0.5).
5. **Amortiguadores (analogía con el tope de energía del predador).** Un presupuesto pequeño de
   ediciones recorta el thrashing, aunque bastante menos de lo que se creía: a λ=0.5, `GOVERNED`
   con `B=3` rinde 23.7 contra 10.0 de `CLOSED_LOOP` y sus ediciones desperdiciadas caen de 181.1
   (con `B=25`) a 50.7, pero con `B=0`, que es exactamente `OPEN_LOOP` (control 6), rinde 27.0 con
   10.1 desperdiciadas (§8), de forma que con dinamismo alto el mejor amortiguador medido es no
   reparar de forma proactiva. A λ=0.1 y 0.25 `B=3` queda apenas por encima de ambos extremos
   (91.0 frente a 89.0 y 86.0; 57.3 frente a 56.0 y 47.0), con diferencias que no conviene leer
   sin banda de error.
6. **Capacidad de carga (analogía con el pasto que se repone).** Cada entrega repone un recurso
   (`agents.py:660-661`, `model.py:195-202`), así que el mundo nunca se queda sin trabajo, y el
   Paquete 4 mide si la abundancia cambia el valor de replanificar (y de no planificar).

Vale la pena dejar escrita en la sección la corrección que cambió esta lectura: antes de la
corrección del 2026-10-09 la replanificación tras un fallo era gratuita y con A\* exacto, mientras que la
reparación proactiva pagaba `c` y pasaba por el oráculo, de modo que el experimento comparaba una
reparación pagada contra una gratuita y buena parte de la dominancia del lazo abierto (así como
del «rescate» por gobernanza) era artefacto de esa asimetría. Hoy `_fallar_tarea` solo deja
pendiente la replanificación (`agents.py:666-689`) y `_paso_planificado` la dispara en el tick
siguiente con `_iniciar_deliberacion(por_fallo=True)` (`agents.py:331-335`), por el mismo oráculo
y al mismo costo que cualquier reparación, sin consumir presupuesto, lo cual hace de `B=0` un
control exacto (`GOVERNED` ≡ `OPEN_LOOP` en 180 pares de corridas, 0 distintos, según
`--controles`).

**Checklist**

- [ ] Sección markdown «¿Por qué la frontera tiene esa forma?» tras `fig_frontera`, con cada pilar rotulado como analogía o como mecanismo
- [ ] Cita cruzada a `fig_dinamica` (Paquete 3) como evidencia del retardo, a `fig_escasez` (Paquete 4) para la capacidad de carga y a `fig_conocimiento` (KB-2) para la parte de la creencia obsoleta, por lo que este paquete va al final
- [ ] La nota sobre la corrección de la regla de costo y el control 6
- [ ] Enlace con R&N §11.5 (monitoreo y reparación de planes) y con Brooks (1991) para el régimen donde gana no planificar

**Aceptación.** La sección se lee sola y cierra con una frase coherente con los datos, que
reemplaza a la de C4: *cuando reparar cuesta, el lazo abierto y el cerrado quedan cerca y, con el
entorno cambiando rápido, gana el agente que no delibera; la observabilidad parcial mueve sobre
todo el nivel de utilidad; el thrashing es real y un presupuesto pequeño lo recorta, aunque con
dinamismo alto no reparar de forma proactiva lo recorta igual o mejor; y reparar en caliente
frente a reiniciar en frío compensa en casi todo el rango con λ>0, salvo a λ=0.5 con `c≥5`, donde
ambas políticas colapsan.*

---

## Orden y dependencias

Este documento y [`roadmap-c4b.md`](roadmap-c4b.md) se recorren como **una sola ruta**, cuyo
detalle y justificación están en la sección
[Orden](roadmap-c4b.md#orden-y-dependencias) de aquel:

```
1 (orden aleatorio) → 3 (curvas temporales) → KB-1 → KB-2 → 4 (escasez) → 5 (narrativa)
extras de presentación: 2 (tira) y KB-3 (capa de región en la animación)
```

El 1 va primero porque es el único que toca el ciclo de `model.py` y conviene aislar su
regresión, y el 5 va al final porque cita `fig_dinamica`, `fig_escasez` y `fig_conocimiento`.

## Referencia

- Sesión: `content/presentation/IA_C4.ipynb` (Mesa 3.5.1, predador–presa, vecindario Moore,
  scheduler aleatorio, ciclos Lotka–Volterra).
- Russell, S. y Norvig, P. (2020), *AIMA* 4.ª ed., §2.4 (taxonomía de agentes) y §11.5
  (ejecución, monitorización y reparación de planes).
