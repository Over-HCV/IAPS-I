# Anexo: la línea clásica del planning, explicada desde cero

> Complemento de `guion.md`. La función de este anexo es que la línea clásica
> (Russell y Norvig no son el comienzo) se pueda explicar y defender sin ser
> historiador de la IA: cada ancla se presenta con lo que dijo, por qué importa
> para el proyecto y en qué eje del experimento se refleja. Al final van las
> entradas `.bib` de las anclas clásicas, por si se decide citarlas.

---

## 1. Línea de tiempo en una tabla

| Año | Ancla | Aporte en una frase | Eje del proyecto donde se refleja |
|---|---|---|---|
| 1959 | Samuel (checkers) | Primer sistema que ajusta su propia función de evaluación jugando | Auto-modificación con p baja y c despreciable |
| 1991 | Brooks (robótica reactiva) | Inteligencia sin representación: reaccionar basta si el mundo responde rápido | Reflejo simple (línea base) |
| 1987– | SOAR (Laird) | Arquitectura cognitiva que reescribe sus propias reglas (chunking) en caliente | Lazo cerrado con c pequeño |
| 1995 | Nebel y Koehler | Reusar plan es teóricamente tan duro como generarlo (complejidad) | Justifica que reparar no es gratis |
| 2002 | D* Lite (Koenig y Likhachev) | Replanificación incremental en retículas dinámicas | El mundo MESA con recursos móviles (λ) |
| 2003 | Gödel machines (Schmidhuber) | Límite teórico: reescribirse solo con prueba de mejora | p = 1 con c astronómico |
| 2011 | Zilberstein (metarazonamiento) | Deliberar es una acción con costo que compite con actuar | Todo el marco (κ, c) |
| 2006 | Fox et al. (plan stability) | Reparación vs. replanificación como dicotomía medible | Frío vs. caliente |
| 2021 | DreamCoder | El agente hace crecer su propia biblioteca de programas | Oráculo con competencia p |
| 2023 | Voyager, Reflexion, AutoGPT | Agentes LLM que reescriben habilidades, memoria y planes | Lazo cerrado con p < 1, thrashing |
| 2024 | ADAS, AFlow, AWM, AI Scientist | Búsqueda de flujos en código (frío) e incidentes de auto-edición no autorizada | Reinicio en frío y gobernanza (B) |
| 2026 | Survey self-evolving agents (TMLR) | La clase recibe nombre y agenda: what/when/how/where | El "when" = la pregunta del proyecto |

(Nota honesta: la tabla ordena por tradición más que por fecha estricta, dado
que SOAR nació en los ochenta pero su referencia canónica en libro es Laird
2012.)

---

## 2. Las anclas explicadas

**Samuel (1959), el primer auto-modificador:** el programa de damas de Samuel
aprendía ajustando los pesos de su propia función de evaluación a partir de sus
partidas, de forma que el sistema que evaluaba jugadas era el mismo que se
reescribía tras jugarlas; importa porque desmonta la idea de que "agente que se
modifica a sí mismo" es un fenómeno de 2023, con el pequeño detalle de que allí
la modificación era numérica (pesos) y no simbólica (programas).

**Brooks (1991), la línea base reactiva:** la tesis *intelligence without
representation* sostiene que un agente acoplado al mundo no necesita modelo ni
plan si sus lazos percepción-acción son suficientemente rápidos, lo que en el
experimento corresponde exactamente al reflejo simple (revalúa en cada tick,
nunca sufre plan obsoleto, sacrifica previsión); su valor retórico es que la
línea base del Cuadro 1 tiene un autor y un manifiesto citables.

**SOAR y el chunking (Laird 2012), la edición en caliente histórica:** SOAR es
una arquitectura cognitiva cuyas decisiones son reglas de producción y cuyo
mecanismo de aprendizaje (chunking) compila experiencia en reglas nuevas que se
insertan en el sistema mientras corre, de forma que es el caso clásico de
edición caliente con costo marginal casi nulo; sirve para mostrar que el
espectro c ∈ [0, ∞) del proyecto tiene habitantes verificados en ambos
extremos.

**Nebel y Koehler (1995), la advertencia de complejidad:** su resultado central
es que reusar o reparar un plan, en el caso general, es computacionalmente tan
duro como generarlo de nuevo, con lo cual la intuición "reparar es más barato
que replanificar" no viene gratis sino que hay que medirla; el proyecto
operationaliza justo esa medición (la diferencia de utilidad entre frío y
cerrado es el precio de la reparación).

**Fox et al. (2006), la dicotomía con nombre:** en *Plan Stability:
Replanning versus Plan Repair* se compara regenerar el plan completo contra
modificar el mínimo necesario, introduciendo estabilidad del plan como métrica;
es el pariente directo del proyecto (frío vs. caliente), con la diferencia de
que allí el reparador es exacto y el entorno determinista, mientras que aquí el
reparador es un oráculo estocástico (p) con costo (c) y presupuesto (B), que es
lo que la era LLM añade.

**Monitoreo de ejecución (R&N cap. 11):** la literatura de planning en línea
distingue monitoreo de acción, de plan y de objetivo, y define el evento que
dispara toda la dinámica del experimento (una divergencia entre lo que el plan
asume y lo que el mundo hizo); ya está citado en el avance, solo conviene
recordar que ese vocabulario es el puente natural hacia Fox et al.

**D* Lite y ARA* (2002–2003), el mundo MESA avant la lettre:** D* Lite
replanifica de forma incremental (reutiliza el árbol de búsqueda anterior en
lugar de tirarlo) en retículas donde el mundo cambia mientras el robot se
mueve, que es literalmente el escenario del proyecto (recursos móviles con
probabilidad λ por tick); ARA* añade la dimensión anytime (respuesta buena ya,
mejor si hay tiempo), que es pariente del compromiso costo-beneficio que el
plano (λ, c) mide.

**Zilberstein (2011), el marco que ya se cita:** la tradición de
metarazonamiento trata la deliberación como una acción con costo que compite
con actuar, de modo que el presupuesto B y el precio κ del experimento son una
política de deliberación explícita y el thrashing medido es el modo de fallo
clásico de una política mal calibrada (esto ya está redactado en el avance y no
requiere cambio).

**Gödel machines (Schmidhuber 2003), el límite ideal:** una Gödel machine
reescribe cualquier parte de su propio código únicamente cuando encuentra una
prueba de que la reescritura mejora su utilidad, lo que corresponde al caso p =
1 con un costo c astronómico (buscar la prueba); su función en el discurso es
acotar el espectro por arriba: entre SOAR (c ≈ 0, p modesta) y Gödel (p = 1, c
enorme) viven todos los oráculos reales, incluido el LLM del sistema de
producción.

**La línea moderna (2021–2026), de vuelta al guion:** DreamCoder hace crecer
su propia biblioteca de programas (competencia del oráculo), Voyager, Reflexion
y AutoGPT reescriben en caliente habilidades, memoria y planes, ADAS y AFlow
buscan flujos en código pero offline (frío), y el survey de TMLR le pone nombre
y agenda a la clase; los detalles y referencias están en `guion.md` §3–4.

---

## 3. Cómo se arma el relato con estas piezas

Primeramente se abre con la clase (self-evolving agents, survey TMLR 2026) y su
pregunta abierta (el "when"); progresivamente se muestra que la clase tiene
historia (Samuel, SOAR, Fox, D* Lite, Gödel), de forma que el proyecto queda
como la medición moderna de una pregunta clásica y no como una moda de LLMs; y
finalmente el sistema propio (OASys) entra como la instancia de calibración que hoy
decide esa pregunta por intuición, que es exactamente el vacío que la frontera (λ, c) llena.

---

## 4. Entradas `.bib` de las anclas clásicas (por si se citan)

```bibtex
@article{samuel1959some,
  author  = {Arthur L. Samuel},
  title   = {Some Studies in Machine Learning Using the Game of Checkers},
  year    = {1959},
  journaltitle = {IBM Journal of Research and Development},
  volume  = {3},
  number  = {3},
  pages   = {210--229}
}

@article{brooks1991intelligence,
  author  = {Rodney A. Brooks},
  title   = {Intelligence without Representation},
  year    = {1991},
  journaltitle = {Artificial Intelligence},
  volume  = {47},
  pages   = {139--159}
}

@article{nebel1995plan,
  author  = {Bernhard Nebel and Jana Koehler},
  title   = {Plan Reuse versus Plan Generation in Classical Planning: A Theoretical and Empirical Analysis},
  year    = {1995},
  journaltitle = {Artificial Intelligence},
  volume  = {76},
  number  = {1--2},
  pages   = {427--454}
}

@inproceedings{likhachev2003ara,
  author    = {Maxim Likhachev and Geoff Gordon and Sebastian Thrun},
  title     = {ARA*: Anytime A* with Provable Bounds on Sub-Optimality},
  booktitle = {Advances in Neural Information Processing Systems 16 (NIPS 2003)},
  year      = {2003},
  pages     = {767--774}
}

@misc{schmidhuber2003goedel,
  author = {J{\"u}rgen Schmidhuber},
  title  = {G{\"o}del Machines: Self-Referential Universal Problem Solvers Making Provably Optimal Self-Improvements},
  year   = {2003},
  note   = {arXiv:cs/0309048},
  doi    = {10.48550/arxiv.cs.0309048}
}

@inproceedings{ellis2021dreamcoder,
  author    = {Kevin Ellis and Catherine Wong and Maxwell Nye and others},
  title     = {DreamCoder: Bootstrapping Inductive Program Synthesis with Wake-Sleep Library Learning},
  booktitle = {Proceedings of PLDI 2021},
  year      = {2021},
  pages     = {835--850}
}
```

(Nota de verificación, 2026-09-25: todas estas entradas ya se verificaron contra
IBM/ACM/AAAI/NeurIPS al pegarlas en `bib/refs.bib`, lo cual corrigió tres errores
que este anexo traía de memoria: las páginas de Nebel y Koehler (427–454, no
417–458), el título de ARA* (*Anytime A\* with Provable Bounds on Sub-Optimality*,
no *Anytime Replanning*) y el título de la versión PLDI de DreamCoder
(*Bootstrapping Inductive Program Synthesis with Wake-Sleep Library Learning*; el
título con *Growing Generalizable…* es el del preprint de arXiv de 2020). Samuel
(210–229) y Brooks (139–159) quedaron confirmados sin cambio. La fuente de verdad
es ahora `bib/refs.bib`, no este bloque.)

(Nota de estado, 2026-10-09: el modelo corrigió un sesgo en su regla de costo, pues el lazo
abierto replanificaba gratis y con A\* exacto tras un fallo del plan, mientras que el lazo
cerrado pagaba `c` ticks y pasaba por el oráculo de competencia `p`; hoy toda replanificación
disparada por un fallo o por una divergencia detectada pasa por el mismo oráculo y cuesta `c`,
y las 8.640 corridas se re-ejecutaron. Este anexo no cita cifras de resultados, por lo que
ninguna afirmación suya caducó, aunque dos anclas ganan peso con la corrección: la advertencia
de Nebel y Koehler queda escrita en el propio modelo (ninguna reparación es gratis, tampoco la
del lazo abierto tras un fallo), y la línea reactiva que Brooks defendía deja de ser solo una
línea base, dado que con dinamismo alto y `c≥2` la mejor política medida pasa a ser
`MODEL_BASED`, que actúa sin plan y nunca paga deliberación (con el matiz de que, a diferencia
del reflejo de Brooks, sí guarda creencias, por lo que respalda la mitad "sin plan" de su
tesis y no la mitad "sin representación"). El detalle está en `guion.md` §7.)
