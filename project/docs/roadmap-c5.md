# Roadmap C5 — Inferencia probabilística en el modelo

Documento de trabajo derivado de
[`content/notes/books/ws-05-Inferencia_probabilistica_AMB.ipynb`](../../content/notes/books/ws-05-Inferencia_probabilistica_AMB.ipynb)
(inferencia probabilística para modelos basados en agentes, sesión 5). Funciona igual que
[`roadmap-c4.md`](roadmap-c4.md) y [`roadmap-c4b.md`](roadmap-c4b.md): paquetes acumulables que
se marcan `[x]` al completarse, y tras cada uno `pytest project/tests -q` debe quedar en verde.
La ruta conjunta de los tres documentos está en la sección [Orden](#orden-y-dependencias).

## La tesis

KB-2 de [`roadmap-c4b.md`](roadmap-c4b.md) termina en un **límite honesto**: la lógica dice
dónde **puede** estar un recurso, no dónde **probablemente** está, de modo que el peor caso
trata igual el centro de la región posible que su borde. La sesión 5 trae justo las piezas que
faltan para cruzar ese límite, y lo dice ella misma en su §14 (el Wumpus probabilístico: cuando
la lógica no decide, la probabilidad elige la celda menos riesgosa):

| Concepto C5 | Contraparte en el modelo | Uso |
|---|---|---|
| Beta–Bernoulli (§2.3), convergencia $1/\sqrt{n}$ (§4.2) | Cada recurso visto en dos ticks seguidos es un ensayo de Bernoulli: se movió o no, con probabilidad λ (`Resource.step`, `agents.py`) | El agente **aprende λ** en vez de recibirlo |
| Filtrado *forward* de estado oculto (§11) | La celda de un recurso fuera de vista es un estado oculto que sigue una caminata conocida | Distribución sobre la celda de cada recurso, cuyo soporte es la región $R(r,t)$ de KB-2 |
| Decisión por utilidad esperada (§6) | Reparar cuesta `c`; mantener un plan que luego falla cuesta la caminata perdida más `c` | Regla de reparación sin umbral libre |
| Wumpus probabilístico (§14) | Elegir objetivo cuando varias regiones se solapan | Ordenar objetivos por costo esperado |
| ABC por rechazo (§12) | Estimar (λ, p) de un despliegue a partir de telemetría agregada | Volver operable el criterio de cuándo reescribir |
| Sensibilidad con `batch_run` (§13) | Las 8.640 corridas ya guardadas | Qué parámetro de un despliegue vale la pena medir |

Las piezas de la sesión sin contraparte se descartan: el aprendizaje social (§8) y la selección
evolutiva de creencias (§10) necesitan varios agentes, y el modelo tiene uno; el bandido espacial
(§7) y Q-learning (§15) responden a un problema de exploración que aquí no existe, porque
observar la deriva es **pasivo** (el agente aprende λ mirando, sin pagar por ello), así que la
trampa del pesimista de §5 tampoco aparece.

## Disciplina de alcance

Las mismas reglas que [`roadmap-c4b.md`](roadmap-c4b.md): hipótesis escritas antes de correr,
barridos nuevos en archivos propios (ningún CSV existente se toca), nivel de conocimiento
separado del de implementación, y equidad de costo (`BAYESIAN` hereda la regla de costo
corregida del 2026-10-09 y el parámetro `ticks_por_ask` de KB-2).

---

## C5-B — El agente que sabe *cuánto* sabe (`Policy.BAYESIAN`, `project/filtro.py`)

**Depende de.** KB-2 (reutiliza sus ganchos en `Collector` y su región posible de
`project/conocimiento.py`, contra la que se prueba).

### Qué sabe el agente

- **El mismo conocimiento de fondo que KB-2:** un recurso que se mueve lo hace a una vecina
  transitable elegida al azar. Lo único que KB-2 sabe además es *si* el mundo es estático
  (λ=0 o no); `BAYESIAN` no recibe λ y lo aprende.
- **λ aprendido (Beta–Bernoulli):** Prior Beta(1,1). Cada tick, por cada recurso visto en este
  tick y en el anterior (con al menos una vecina transitable), se suma un éxito si cambió de
  celda y un fracaso si no. Es un ensayo exacto porque el agente observa una sola vez por tick y
  entre dos observaciones el mundo deriva exactamente una vez. $\hat\lambda$ es la media
  posterior.
- **Filtro de rejilla por recurso:** Al verlo, la distribución colapsa a su celda. Cada tick sin
  verlo: predicción con la caminata
  $P'(x) = (1-\hat\lambda)P(x)[\deg x>0] + P(x)[\deg x = 0] + \hat\lambda\sum_{y\sim x} P(y)/\deg y$,
  y corrección poniendo a cero las celdas vistas sin el recurso y renormalizando.

### Las dos decisiones

1. **Objetivo:** Se elige por costo esperado $d / q$, con $d$ la distancia de Manhattan (el
   mismo `_dist` que el resto) a la última celda observada y $q$ la probabilidad de que el
   recurso siga en esa celda al llegar (el filtro propagado $d$ pasos). Solo son candidatos los
   recursos cuya última celda tiene probabilidad positiva ahora, que es exactamente el filtro de
   candidatos de KB-2.
2. **Reparar o mantener:** Ante una divergencia, con `k` líneas `GOTO` antes del `PICK` y $q$ la
   probabilidad de que el recurso esté en la celda del `PICK` al llegar, se repara si y solo si
   $c < (1-q)(c+k)$. Mantener cuesta, en esperanza, la caminata perdida más la replanificación
   forzada posterior; reparar cuesta `c` ya.

Con `horizonte_validez="ahora"` ambas decisiones se evalúan en el tick actual en vez de a la
llegada ($q$ sin propagar), y con visión total eso reduce `BAYESIAN` a `CLOSED_LOOP`.

### Hipótesis (antes de correr)

- **HB1:** Con $r \in \{1,3\}$ y λ>0, `BAYESIAN` (`"llegada"`) supera a `KNOWLEDGE_BASED`
  (`"llegada"`) en `utilidad_neta`, por pares de semilla. La razón esperada es que el peor caso
  descarta por igual objetivos casi seguros y casi perdidos, y el horizonte lógico mantiene
  planes posibles pero improbables.
- **HB2 (control exacto):** Con `r=∞` y `"ahora"`, `BAYESIAN` ≡ `CLOSED_LOOP` semilla a semilla.
- **HB3:** $|\hat\lambda-\lambda|$ al final de la corrida es pequeño y decrece con el número de
  ensayos como $1/\sqrt{n}$ (C5 §4.2), de forma que con `r=1` (pocos ensayos) el agente decide
  con un λ peor estimado.
- **HB4:** A λ=0.5 y `c=5`, `BAYESIAN` sigue por debajo de `MODEL_BASED`, porque el criterio
  evita reparaciones proactivas pero no las forzadas por un fallo. Que falle no invalida el
  paquete: mide cuánto de la brecha con no planificar cierra saber cuánto se sabe.
- **HB5 (calibración):** Con λ conocido, las celdas a las que el filtro asigna probabilidad
  $\approx x$ contienen al recurso con frecuencia $\approx x$ (diagrama de fiabilidad).

**Checklist**

- [x] `project/filtro.py`: `BetaBernoulli`, `FiltroRecurso` (predicción, corrección, avistamiento, propagación sin mutar)
- [x] `Policy.BAYESIAN` (`planifica` y `replanifica`), conectado a los ganchos de KB-2
- [x] Reporter `lambda_estimado` (NaN para el resto); `n_consultas` compartido con KB-2
- [x] `tests/test_filtro.py`: masa 1; soporte == región de KB-2 tick a tick con λ>0; con un solo avistamiento y sin poda, tras `k` ticks el soporte es la bola geodésica; $\hat\lambda$ dentro de 3 desviaciones de λ; HB2 exacta; calibración (`slow`)
- [x] Barridos: `BAYESIAN` en `conocimiento`, `conocimiento_ahora` (que con `r=∞` ya es el control HB2, por lo que no hace falta un `bayes_control` aparte) y `conocimiento_costo`
- [x] `fig_conocimiento` con la serie nueva y `fig_calibracion`
**Resultado (2026-11-06).** HB2 pasa semilla a semilla, el soporte del filtro coincide con
la región de KB-2 en cada tick y el filtro está calibrado (HB5). HB1 **se rechaza**: con `r=3` y
λ=0.5, `BAYESIAN` − `KNOWLEDGE_BASED` = −16 ± 4.3, y la causa es la regla de reparación
$(1-q)(c+k)$, que repara de más (16.3 reparaciones proactivas contra 9.5 de KB a λ=0.5) porque
trata cada reparación como si comprara certeza, cuando el plan reparado nace desactualizado y una
divergencia nueva puede interrumpirlo; con la regla `"ahora"` sube de
84.3 a 93.7 a λ=0.1 en `conocimiento_ahora`, por encima de KB con `"llegada"` (91.3). HB3 se confirma (mediana de $|\hat\lambda-\lambda|$: 0.083
con `r=1`, 0.020 con `r=3`, 0.003 con `r=∞`) y HB4 también (−83 ± 10.3 frente a `MODEL_BASED`
a λ=0.5). Desviación: los ensayos de λ cuentan solo si la celda previa del recurso sigue a la
vista, porque exigir verlo en los dos ticks sesgaba $\hat\lambda$ a la baja (0.38 con λ=0.5 y
`r=1`): un recurso que salió del disco de visión es un movimiento que no se ve.

- [ ] Sección del cuaderno con hipótesis, figuras y veredicto

---

## C5-S — Sensibilidad sobre las corridas guardadas (`project/sensibilidad.py`)

**Objetivo.** Responder sin correr nada qué parámetro mueve más la utilidad de cada política:
para cada barrido y política, la fracción de la varianza de `utilidad_neta` explicada por cada
factor barrido (η² de un factor, $SS_{\text{entre}}/SS_{\text{total}}$), y lo mismo para la
diferencia pareada por semilla `OPEN_LOOP − CLOSED_LOOP`, que es la pregunta del proyecto.

**Hipótesis.** λ domina la varianza de toda política con plan; `c` explica más que `p` en
`OPEN_LOOP` − `CLOSED_LOOP`; `r` mueve el nivel de todas las políticas (η² alto en cada una) pero
poco su diferencia.

**Checklist**

- [x] `sensibilidad(df, factores, metrica, por="politica")` y `sensibilidad_delta(...)` en `project/sensibilidad.py` (módulo propio, para no chocar con `analysis.py`)
- [x] `fig_sensibilidad` (barras horizontales, una faceta por barrido)
- [x] Test con un `DataFrame` sintético de η² conocido
- [ ] Tabla y lectura en el cuaderno

---

## C5-A — Calibración ABC (`project/calibracion.py`)

**Objetivo.** El guion asigna al sistema propio el papel de aportar «λ y p de producción». ABC
por rechazo (C5 §12) lo vuelve un procedimiento: dado lo que registra la telemetría de un
despliegue (entregas, tareas fallidas, replanificaciones forzadas y divergencias por tick), se
estima la posterior de (λ, p) y se lee qué política recomienda la frontera bajo esa posterior.

**Diseño.** Un despliegue simulado con (λ*, p*) ocultos y `OPEN_LOOP` (el modo en frío, sin
monitoreo, que es lo que corre un motor sin reparación en caliente) produce los estadísticos
observados promediando 5 semillas. Prior uniforme λ ∈ [0, 0.8] y p ∈ [0.5, 1] (con [0, 0.5] la posterior se
cargaba hacia abajo cuando λ*=0.5, por el borde); 3.000 simulaciones de 2 semillas; estadísticos estandarizados por su desviación en las simulaciones; se acepta el
5 % más cercano. Salida `results/abc.parquet` y `fig_abc`.

**Hipótesis.** λ se recupera con precisión (las divergencias y los fallos lo delatan casi
linealmente); p sale mucho más ancha, porque con `OPEN_LOOP` el oráculo solo se consulta tras un
fallo y sus errores se confunden con el dinamismo.

**Checklist**

- [x] `estadisticos`, `simular`, `abc_rechazo`, `recomendar` en `calibracion.py`, con CLI
- [x] Test `slow`: en un caso sintético λ* cae dentro del intervalo creíble del 90 %
- [ ] `fig_abc` y sección del cuaderno con la recomendación bajo la posterior

---

## Orden y dependencias

```
C4-1 → C4-3 → KB-1 → KB-2 → C5-B → C4-4 → C5-S → C5-A → C4-5 (narrativa)
extras:  C4-2 (tira)   KB-2/C5-B ──→ KB-3 (región y mapa de probabilidad)
```

C5-B va justo tras KB-2 porque comparte sus ganchos y su prueba de solidez. C5-S y C5-A no
dependen de las políticas nuevas y pueden ir en cualquier momento, pero se dejan tras la escasez
para que la sensibilidad incluya ese barrido.

## Referencias

- Sesión: `content/notes/books/ws-05-Inferencia_probabilistica_AMB.ipynb`.
- Russell, S. y Norvig, P. (2020), *AIMA* 4.ª ed., cap. 12–14 (incertidumbre, redes bayesianas,
  razonamiento temporal y filtrado) y §16.1 (utilidad esperada).
- Beaumont, M. A., Zhang, W. y Balding, D. J. (2002). Approximate Bayesian computation in
  population genetics. *Genetics*, 162(4), 2025–2035.
