---
name: ohcv-writting
description: Captura el estilo, tono y forma de redactar propios del usuario.
---

# Estilo de redacción personal

Este skill describe cómo escribe el usuario para que un Agente pueda generar o completar texto que suene genuinamente escrito por él (registro académico-técnico en español, con oraciones largas encadenadas por comas, voz impersonal con "se", marcadores secuenciales tipo "Primeramente/Progresivamente/Finalmente", aclaraciones entre paréntesis y listas con término-en-negrita-seguido-de-explicación). Úsala SIEMPRE que el usuario pida redactar, completar, revisar o reescribir cualquier texto para él —informes, talleres, respuestas de examen, documentos LaTeX, correos formales, resúmenes técnicos, etc.— y no solo en temas de ciberseguridad. Actívala también cuando pida "que suene como yo", "en mi estilo" o simplemente continúe un documento que ya tiene ese tono. No aplica a chistes, poesía o textos explícitamente casuales/informales que el usuario pida en un registro distinto.


## Rasgos centrales de la voz

1. **Oraciones largas, compuestas con conectores lógicos (no con comas).** El
   usuario prefiere una oración extensa con varias cláusulas antes que varias
   oraciones cortas, pero las compone con conectores ("de forma que", "por lo
   que", "lo cual", "puesto que", "así como", "con el objetivo de") y no
   encadenando comas, porque las comas en serie cortan la narrativa. Nunca se
   pone coma antes de "y" (la conjunción ya es separador). Si una oración
   acumula más de tres comas, se reescribe con conectores o se parte en dos.
   - Ejemplo real: *"Progresivamente y en silencio se iban recopilando los
     datos, esto apoyados de un proxy que permitía aparentar una dirección
     IP que ubicaron en Toronto (Canadá) para tener un acceso prolongado."*
   - Al redactar en su nombre, resistir el impulso de "limpiar" esto en
     oraciones cortas tipo libro de texto; el largo es parte de la voz.
2. **Voz impersonal con "se".** Casi nunca usa primera persona ni voz activa
   con sujeto explícito para narrar hechos; prefiere "se filtraron", "se
   hizo uso de", "se procede con", "se pueden diseñar algoritmos que...".
3. **Marcadores secuenciales explícitos.** Para narrar procesos o cadenas de
   eventos usa marcadores como "Primeramente", "Progresivamente",
   "Finalmente", "Al momento que...", en vez de listas numeradas cuando el
   contenido es narrativo (las listas numeradas/bullet sí se usan para
   contenido enumerativo, ver punto 5).
4. **Aclaraciones técnicas entre paréntesis.** Introduce siglas o detalles
   de contexto entre paréntesis inmediatamente después del término: "la red
   corporativa (ALM)", "(sin cifrado asociado)", "(1 o más respuestas
   válidas)". Esto sustituye a notas al pie para aclaraciones breves.
5. **Listas con término-en-negrita + explicación en una oración.** Cuando sí
   usa listas (`\item`), cada punto es un concepto corto seguido de dos
   puntos y luego una oración explicativa completa, no un fragmento:
   - *"Principios Zero Trust: Al momento que se compromete una cuenta, esta
     no debería acceder progresivamente a enormes cantidades de
     información, el privilegio debe ser mínimo y sólo autorizado cuando
     sea necesario."*
6. **Registro académico-técnico con toques coloquiales.** El vocabulario es
   técnico y preciso (exfiltración, escalamiento de privilegio, Zero
   Trust, SOC, VPN), pero se permite alguna expresión coloquial de
   transición: "cabe mencionar", "con el pequeño detalle que", "hay que
   brindar". No es un registro 100% formal/burocrático; es el de alguien
   explicando con rigor pero sin acartonarse.
7. **Auto-anotaciones honestas `01` ┌ Reconocimiento
`02` └ Escaneo nmap
`03` ┌ Escaneo vulns
`04` └ Exploit distcc
`05` ┌ Exploit vsftpd
`06` └ Conclusionesobre incertidumbre.** Cuando la fuente
   original es dudosa (ej. un PDF con OCR, una diapositiva no confirmada),
   el usuario dedica una nota aparte explicando el problema y qué falta
   verificar, en vez de fingir certeza. Al redactar por él, replicar este
   hábito: si algo no está confirmado con una fuente, decirlo explícitamente
   en vez de inventar con seguridad.
8. **Mayúscula después de dos puntos y punto y coma.** Regla fija del
   usuario, sin excepción: la palabra que sigue a `:` o `;` empieza en
   mayúscula, tanto en prosa como en títulos, pies de figura, nodos de
   diagramas y listas de palabras clave.
   - *"esto tiene una explicación directa: En la escala original la segunda
     variable dominaba..."*
   - *"Pregunta 1: Unidades estadísticas"*, *"Palabras clave: Estadística
     descriptiva; Diagrama de caja; Covarianza"*
   - No aplica dentro de código, matemáticas, horas (`12:00`) ni rangos
     numéricos.
9. **Respuesta directa primero, pregunta en negrita.** En talleres y
   ejercicios cada inciso abre con la pregunta o el concepto en negrita
   terminado en punto o signo de interrogación, seguido de la respuesta
   directa ("Sí,", "No, pues", "El Modelo B,") y después la justificación
   encadenada en una sola oración larga.
   - *"**¿Cambió el desempeño tras estandarizar?** Sí, de forma sustancial en
     su capacidad de detectar la clase positiva: El Accuracy apenas se
     mueve..."*
   - *"**Por qué k impar evita empates.** Un empate ocurre cuando..."*
   - Los incisos enumerativos van con letras (a., b., c.) y el patrón
     "**Término.** Oración completa".
10. **Conectores y matices preferidos.** "pues", "de forma que", "de modo
    que", "es decir", "mientras que", "ya que", "dicho esto", "esto sucede
    porque", "resulta claro que", "quedando así demostrado". Para matizar sin
    perder firmeza: "vale la pena matizar", "vale la pena anotarlo con
    honestidad", "no es del todo una confirmación independiente". Se evita
    abusar de "Primeramente/Progresivamente" en textos técnicos cortos; "Primero
    se calcula... Luego..." es suficiente.
11. **Formato numérico.** Decimales con punto (0.9326) y miles con punto
    (150.000, 4.543), igual que en sus trabajos corregidos; los resultados de
    software se citan con el mismo número que imprime la salida.
12. **Pies de figura explicativos.** Un pie de figura describe qué se ve y,
    tras dos puntos, qué se debe concluir: *"Trayecto directo frente al
    trayecto en escalera entre A y B: La escalera nunca puede ser más corta
    que la línea recta."*
## Checklist antes de entregar un texto "en su estilo"
 
- [ ] ¿Las oraciones largas están compuestas con conectores lógicos (y no con
      cadenas de comas), sin coma antes de "y"?
- [ ] ¿Se usó voz impersonal con "se" en vez de "yo hice" / "nosotros
      hicimos"?
- [ ] ¿Los procesos narrativos usan marcadores secuenciales en prosa en vez
      de listas numeradas?
- [ ] ¿Las siglas o detalles de contexto van entre paréntesis pegados al
      término?
- [ ] ¿Las listas (si las hay) tienen el patrón "Término: oración
      explicativa completa"?
- [ ] ¿El vocabulario es técnico del dominio correspondiente, sin perder
      algún conector coloquial ocasional?
- [ ] Si hay algo no verificable con la fuente disponible, ¿se dejó una nota
      explícita de incertidumbre en vez de inventar?
- [ ] ¿Toda palabra después de `:` o `;` empieza en mayúscula (también en
      títulos, pies de figura, diagramas y palabras clave)?
- [ ] ¿Cada inciso abre con la pregunta/concepto en negrita y la respuesta
      directa (Sí/No/valor) antes de la justificación?
- [ ] ¿Decimales con punto y miles con punto?
## Cómo adaptar a otros dominios (no solo ciberseguridad)

La arquitectura de la voz (oraciones largas con "se", marcadores
secuenciales, paréntesis aclaratorios, listas término+explicación,
auto-anotación de incertidumbre) es independiente del tema. Al redactar en
otro dominio (legal, historia, ingeniería, negocios, etc.):

1. Sustituir el vocabulario técnico por el propio del nuevo dominio.
2. Mantener intacta la arquitectura de oración y los conectores descritos
   arriba.
3. Si el nuevo documento tiene un formato distinto (Word, Markdown, correo),
   conservar igualmente el patrón de listas y el uso de paréntesis
   aclaratorios; no son exclusivos de LaTeX.
4. Si el usuario pide explícitamente un registro más informal, más corto o
   más formal-burocrático, priorizar esa instrucción explícita sobre este
   skill — este skill es el modo por defecto, no una camisa de fuerza.
## Notas

Este es un skill de estilo, no de contenido: no dicta qué decir, sino cómo
decirlo. Para tareas de contenido técnico específico (ej. LaTeX de un
taller, hechos de un caso de estudio), seguir investigando/verificando la
información normalmente y aplicar este estilo al redactar la respuesta
final.
