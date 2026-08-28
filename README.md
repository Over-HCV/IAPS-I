# IAPS-I — Inteligencia Artificial: Representación y Solución de Problemas

Repositorio de la asignatura **Inteligencia Artificial** (código **32310004**) de la **Universidad del Rosario**.

| | |
|---|---|
| **Profesor** | Nicolás Avilán Vargas ([nicolasg.avilan@urosario.edu.co](mailto:nicolasg.avilan@urosario.edu.co)) |
| **Créditos** | 2 (Tipo A) — 24 h acompañamiento + 48 h trabajo independiente |
| **Horario** | Viernes, 1:00 p.m. – 4:00 p.m. |
| **Modalidad** | Presencial y remota |
| **Prerrequisitos** | Ninguno |

## Descripción

Visión general del campo de la inteligencia artificial: qué es la inteligencia, cómo crear agentes que actúen de forma inteligente, y los temas centrales de la IA. Se estudian las características de un agente inteligente, la representación de problemas, la búsqueda de soluciones óptimas, el razonamiento, los sistemas de inferencia y la inferencia probabilística, junto con ejemplos de aplicación en diferentes campos.

## Conceptos fundamentales

1. Introducción a la Inteligencia Artificial
2. Entornos y agentes
3. Búsqueda en un espacio de estados
4. Representación del conocimiento
5. Razonamiento
6. Planeación
7. Inferencia probabilística

## Resultados de aprendizaje (RAE)

1. Explicar las principales características de un agente inteligente y las de los entornos.
2. Reconocer y comparar técnicas básicas de IA: representación de problemas, búsqueda de caminos óptimos con uso limitado de memoria, representación de conocimiento mediante lógica y probabilidad.
3. Conocer ventajas, desventajas y contexto de uso de cada técnica.

## Evaluación

| Actividad | Porcentaje |
|-----------|------------|
| Quices | 30% |
| Notebooks | 30% |
| Proyecto — Documento | 15% |
| Proyecto — Notebook | 15% |
| Proyecto — Presentación | 10% |

## Programación de sesiones

| Sesión | Tema | Recursos (Russell & Norvig) |
|---------|------|------------------------------|
| 1 | Introducción: ¿qué es la IA? Panorama histórico. Tipos de agente. | secs. 1.1, 1.3, 2.1, 2.2, 2.4 |
| 2 | Entornos. Ambientes de tarea y su implementación en Python. | secs. 2.1, 2.3 |
| 3 | Búsqueda a ciegas. Arquitectura de nodos. | secs. 3.1–3.4 |
| 4 | Búsqueda informada. Heurísticas, búsqueda avara, A*, beam search. | secs. 3.5, 3.6 |
| 5 | Lógica y razonamiento automático. | secs. 7.1, 7.3–7.5 |
| 6 | Agentes basados en conocimiento. El mundo del Wumpus. | secs. 7.2, 7.7 |
| 7 | Comprensión de texto y gramáticas independientes del contexto. | Bird et al., secs. 8.2, 8.3, 9.1, 9.2 |
| 8 | Redes bayesianas y redes de decisión. | secs. 13.2, 13.3, 16.3, 16.5 |

Cada sesión incluye lectura de referencias y ejercicios del notebook correspondiente.

## Estructura del repositorio

```
notes/        # Guía de asignatura y notas de clase (W1S1.md)
content/
├── project/
│   ├── presentation/   # Material de sesiones ML (ML_Session1)
│   └── notebook/       # Cuadernos de trabajo (ws-01, ws-02)
learn/        # Material de estudio autónomo (app, reportes, datasets)
```

## Configuración del entorno

El proyecto usa [uv](https://docs.astral.sh/uv/) con Python 3.13.

```bash
# Sincronizar el entorno (crea .venv e instala dependencias)
uv sync

# Ejecutar un script
uv run python content/project/presentation/ML_Session1.py
```

Dependencias principales (`pyproject.toml`): `polars`, `numpy`, `matplotlib`, `seaborn`, `plotly`, `scikit-learn`, `ipykernel`.

> Los cuadernos usan **polars** en lugar de pandas para manipulación de datos.

### Ejecutar los `.py` por celdas en VS Code

Los materiales de sesión están en formato *percent* (`.py` con marcadores `# %%`), además del `.ipynb` original:

- Abre el `.py` en VS Code y usa **Jupyter: Run Cell** (requiere la extensión *Jupyter* y `ipykernel`, ya incluido).
- También puedes ejecutarlo completo como script de Python: `uv run python <archivo>.py`.

## Bibliografía

- [1] Russell, S. y Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4.ª ed.). Pearson.
- [2] Bird, S., Klein, E. y Loper, E. (2009). *Natural Language Processing with Python* (NLTK). O'Reilly.

Complementaria: Nilsson (2001); Rich y Knight (1994); Copeland (2004); Gouveia (2020); Duda, Hart y Stork (2000).

## Acuerdos del curso

Calificaciones solo se modifican por reclamos oportunos según el Reglamento Académico; los supletorios siguen el procedimiento regular. El fraude en evaluaciones se reporta a la Secretaría Académica (reglamento formativo-preventivo y disciplinario). Cualquier situación de acoso o discriminación puede denunciarse en la Coordinación de Psicología y Calidad de Vida (Tel/WhatsApp 322 2485756). Estudiantes con discapacidad o sin recursos tecnológicos deben informarlo a tiempo para recibir apoyos razonables.

---

Guía completa: [`notes/course-guide.md`](notes/course-guide.md)
