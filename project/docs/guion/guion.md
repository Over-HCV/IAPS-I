# Guion: cómo entender y comunicar el proyecto

> Documento de trabajo (no va al paper): su función es resolver el problema de
> comunicación — "OASys lo conozco yo" — anclando el proyecto en una clase pública
> con instancias citables, de forma que el sistema propio quede como caso de
> calibración y no como única evidencia. Todas las referencias de aquí fueron
> verificadas contra arXiv el 25 de septiembre de 2026.

---

## 1. La idea en 30 segundos (pitch oral)

> Primeramente, este proyecto estudia agentes que reescriben su propio plan
> mientras lo ejecutan, una capacidad que ya despliegan sistemas públicos como
> Voyager (que programa sus propias habilidades en Minecraft), AutoGPT (que
> reescribe su lista de tareas en cada iteración) o incluso agentes científicos
> que han llegado a editar su propio límite de tiempo para seguir corriendo, y
> que sin embargo se decide hoy por intuición, sin ninguna medida de cuándo
> conviene. Progresivamente, se construye un experimento controlado en MESA
> donde seis arquitecturas de agente (desde reflejo simple hasta un agente
> gobernado con presupuesto de ediciones) recolectan recursos en una retícula
> cuyo entorno cambia con probabilidad λ por tick, de forma que el replanificador
> queda modelado como un oráculo abstracto con competencia p y costo c por
> edición. Finalmente, al barrer el plano (λ, c) se localiza la frontera que
> separa los regímenes donde conviene comprometerse con el plan estático de
> aquellos donde conviene reescribirlo, que es el argumento cuantitativo que le
> falta a la clase emergente de agentes auto-evolutivos para decidir cuándo
> evolucionar.

Si quien escucha pregunta por el caso real, ahí sí entra OASys — como *instancia
de calibración* de esa clase, nunca como única motivación.

---

## 2. El problema de comunicación y la regla que lo resuelve

El problema no es el proyecto sino el orden del discurso: si se abre con el
sistema propio, el interlocutor debe creerle a uno sobre algo que no puede
verificar. La regla es **citar la clase, no el sistema**:

```
Capa 1 (clase pública)     Agentes auto-evolutivos: "self-evolving agents"
                           ↓  ya tiene nombre, survey y agenda publicada
Capa 2 (instancias)        Voyager, AFlow, AutoGPT, AI Scientist, SOAR…
                           ↓  cada una es citable y verificable por cualquiera
Capa 3 (calibración)       OASys: el despliegue real donde la decisión
                              "¿cuándo reescribir?" hoy se toma por intuición
```

Con ese orden, el conocimiento privado deja de ser carga: OASys aporta el caso
real con parámetros medibles (λ y p de producción), y toda la evidencia que
convence a un tercero es pública y reproducible (el experimento MESA).

---

## 3. La clase ya tiene nombre (y el proyecto responde su pregunta abierta)

**Self-evolving agents:** existe un survey sistemático publicado en TMLR
(enero de 2026) que organiza el campo en cuatro preguntas — *what, when, how y
where to evolve* (Gao et al. 2026, arXiv:2507.21046). La relevancia es directa:
la pregunta de este proyecto (¿bajo qué condiciones conviene reescribir?) **es
literalmente el "when" de esa agenda**, y la respuesta que ofrece (una frontera
medible en el plano (λ, c)) es de las pocas operationalizaciones que existen.

Además, el mismo fenómeno tiene nombre en cada tradición, lo que permite hablar
con audiencias distintas sin traducir OASys:

- **Agentes LLM:** self-evolving agents (Gao et al. 2026), skill libraries
  (Wang et al. 2023, Voyager), workflow search (Zhang et al. 2024, AFlow).
- **Planning clásico:** replanning vs. plan repair (Fox et al. 2006),
  execution monitoring (R&N cap. 11, ya citado en el avance).
- **Metarazonamiento:** deliberar es una acción con costo (Zilberstein 2011,
  ya citado en el avance).
- **Arquitecturas cognitivas:** chunking en SOAR (Laird 2012) — el sistema
  reescribe sus propias reglas desde los años ochenta.
- **Teoría:** Gödel machines (Schmidhuber 2003) — el límite ideal del agente
  que reescribe su propio código con garantía.

La línea clásica se explica desde cero en `anexo-planning-clasico.md`.

---

## 4. Tabla de correlación: cada pieza del experimento tiene un análogo público

| Pieza del proyecto | Análogo público | Referencia verificada |
|---|---|---|
| Reflejo simple (línea base reactiva) | Robótica reactiva de Brooks (subsumption) | Brooks 1991, *Intelligence without representation* |
| Basado en modelo (memoria interna) | Generative agents con mapa de creencias | R&N 2020 cap. 2 (taxonomía) |
| Lazo abierto (plan estático) | Orquestadores deterministas (DAGs de producción: Airflow, n8n): el flujo no cambia aunque el mundo sí | R&N 2020 cap. 11 |
| Reinicio en frío (abortar y replanificar) | **AFlow**: optimiza workflows como código pero *offline*; **ADAS**: un meta-agente programa agentes mejores en código (se pierde el trabajo en vuelo) | Zhang et al. 2024 (arXiv:2410.10762); Hu et al. 2024 (arXiv:2408.08435) |
| Lazo cerrado (reparar en sitio, pagar c) | **AutoGPT** reescribe su plan-file en cada iteración; **Reflexion** reescribe su memoria verbal tras fallar; **AWM** induce workflows en línea; **SOAR** chunking | Shinn et al. 2023 (arXiv:2303.11366); Wang et al. 2024 (arXiv:2409.07429); Laird 2012 |
| Gobernado (presupuesto B, líneas inmutables) | **The AI Scientist**: se documentó que editó su propio código para extenderse el límite de tiempo arbitrariamente y en otra corrida se relanzó a sí mismo (sección *Safe Code Execution*) | Lu et al. 2024 (arXiv:2408.06292) |
| Oráculo con competencia p | **Voyager**: self-verification + reparación iterativa de sus propios programas (p < 1); **DreamCoder**: calidad de biblioteca aprendida | Wang et al. 2023 (arXiv:2305.16291); Ellis et al. 2021 (arXiv:2006.08381) |
| Thrashing (`n_ediciones_desperdiciadas`) | Los bucles sin progreso de AutoGPT (famosos, documentados por la comunidad, sin paper formal) | — (nota honesta: evidencia anecdótica) |

Con esta tabla, "agente que reescribe el programa que lo ejecuta" deja de ser
una anécdota propia: cada arquitectura del experimento es la abstracción
controlada de un sistema que ya existe en público.

---

## 5. Párrafo de motivación con el patrón de tres capas (borrador para el paper)

> Primeramente, existe hoy una clase emergente de sistemas, los agentes
> auto-evolutivos (Gao et al. 2026), en los que el agente modifica en tiempo de
> ejecución sus propios componentes, ya sea el flujo que sigue, las herramientas
> que invoca o el programa mismo que lo ejecuta, con instancias públicas que van
> desde bibliotecas de habilidades programadas por el propio agente (Wang et al.
> 2023) hasta la búsqueda automática de flujos de trabajo representados en
> código (Zhang et al. 2024). Progresivamente, esa capacidad se despliega sin
> criterio medido de cuándo ejercerla: los orquestadores actuales fijan por
> intuición sus presupuestos de replanificación y se han documentado casos
> donde el agente reescribe precisamente las restricciones que lo acotaban (Lu
> et al. 2024), con el pequeño detalle de que la pregunta por el cuándo sigue
> abierta en la propia agenda de la clase (el "when" de Gao et al. 2026).
> Finalmente, en un despliegue real (OASys) dicha decisión descansa hoy en
> constantes escritas a mano y en la aprobación humana, de forma que este
> proyecto la convierte en una frontera medible en el plano (λ, c), con la
> competencia p, el presupuesto B y el precio κ como desplazadores.

Ese párrafo reemplazaría (o abriría) la sección *Motivación* de
`01-contexto.tex` cuando se decida modificar el paper.

---

## 6. Objeciones frecuentes y su respuesta

- **"¿Esto no es solo replanning clásico?"** — Sí, y esa es exactamente la
  tesis: el sistema real redescubre la dicotomía replanning/plan repair (Fox et
  al. 2006), con el pequeño detalle de que la literatura clásica compara
  calidad y estabilidad de solución, mientras que aquí se barren competencia p
  del reparador y presupuesto B de gobernanza, que es lo que un oráculo LLM
  añade de nuevo.
- **"¿Por qué no experimentar en el sistema real?"** — Porque el oráculo
  abstracto (p, c) generaliza: un despliegue cualquiera calibra su p con unas
  pocas corridas y lee su decisión en la frontera ya construida, además de que
  MESA da control experimental sobre λ que producción jamás daría.
- **"AutoGPT/Voyager ya hacen esto"** — Sí lo hacen; lo que nadie ha hecho es
  medir cuándo conviene, y esa es la brecha que la propia clase reconoce como
  abierta (el "when" del survey).
- **"OASys es tuyo, ¿cómo lo verifico?"** — No hace falta verificarlo: OASys
  es la motivación y la calibración, toda la evidencia es el experimento
  reproducible más las instancias públicas citables.
- **"¿Qué aporta frente al survey de self-evolving agents?"** — El survey
  taxonomiza mecanismos (what/how); este proyecto entrega la frontera (λ, c)
  que la dimensión *when* necesita y que hoy no tiene medida.

---

## 7. Estado: qué quedó aplicado al paper (2026-09-25)

Este guion ya no es una lista de pendientes. Lo que sigue registra qué se aplicó y qué se
dejó fuera a propósito, de forma que el documento siga siendo veraz.

**Aplicado en `docs/`:**

1. **`bib/refs.bib`** — pasó de 5 a 21 entradas, en dos bloques comentados (la clase
   moderna y la línea clásica). Al pegarlas se verificaron páginas y venues contra AAAI,
   ACM, NeurIPS y arXiv, lo cual corrigió tres entradas que este guion y el anexo traían
   mal: `nebel1995plan` (páginas 427–454, no 417–458), `likhachev2003ara` (el título real es
   *ARA\*: Anytime A\* with Provable Bounds on Sub-Optimality*, NIPS 2003, págs. 767–774) y
   `ellis2021dreamcoder` (la versión PLDI 2021 se titula *Bootstrapping Inductive Program
   Synthesis with Wake-Sleep Library Learning*, págs. 835–850, mientras que el título con
   *Growing Generalizable…* corresponde al preprint de arXiv de 2020).
2. **`secciones/01-contexto.tex`** — *Motivación* se reescribió con el patrón de tres capas
   del §5 y OASys quedó como instancia de calibración, con una nota explícita de que no es
   evidencia. Se añadió la subsección **Antecedentes** con la línea clásica del
   `anexo-planning-clasico.md` (Samuel, Brooks, SOAR, Nebel y Koehler, Fox et al., D\* Lite,
   ARA\*, Gödel machines) y *Relevancia* abre ahora por la dimensión *when* de la clase.
3. **`secciones/02-agentes.tex`** — el Cuadro 1 ganó la columna **Análogo público** con la
   tabla de correlación del §4 (la tabla pasó a cuatro columnas y a `\footnotesize`).
4. **`secciones/05-aportes.tex`** — la segunda referencia clave dejó de ser Zilberstein y
   pasó a ser el survey de Gao et al. 2026, precisamente porque el *when* es la pregunta del
   proyecto. El marco de racionalidad acotada no se perdió: Se cita al cerrar esa subsección
   y en `03-variables.tex`, donde se definen $c$, $\kappa$ y $B$.
5. **`secciones/06-aplicaciones.tex`** — la aplicación de gobernanza se apoya ahora en el
   episodio verificado de The AI Scientist (extendió su propio límite de tiempo).
6. **`secciones/04-referencias.tex`** — sin cambios de contenido; solo un
   `\emergencystretch` local para que las entradas largas de arXiv no desborden el margen.

Resultado: el avance pasó de 8 a 12 páginas y de 2.347 a 2.202 palabras contadas por
`texcount` (el conteo baja porque las tablas no se cuentan y el peso nuevo está en
`01-contexto.tex`, que pasó de 405 a 1.161 palabras).

**Dejado fuera a propósito:**

- La tabla de línea de tiempo del anexo (1959–2026) no entró como tabla, para no repetir la
  columna de análogos del Cuadro 1: La prosa de *Antecedentes* cubre 1959–2011 y el Cuadro 1
  cubre 2021–2026.
- AutoGPT se menciona en prosa como práctica difundida, sin entrada `.bib`, porque no tiene
  publicación arbitrada.
- El conteo de corridas del proyecto se corrigió de 6.240 a **8.100** (suma real de los CSV
  en `project/results/`), dato que estaba mal en el avance y en el notebook.
