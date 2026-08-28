# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: notebook (3.13.9)
#     language: python
#     name: python3
# ---

# %% [markdown] id="qkm5C75mnf0w"
# <table>
#     <tr>
#         <td><img src="assets/header.png" width="300"/></td>
#         <td>&nbsp;</td>
#         <td>
#             <h1 style="font-size:200%;color:blue;text-align:center">    <FONT COLOR="red">Introducción al Aprendizaje Automático de Máquina  </FONT>         </h1></td>
#         <td>
#             <tp><p style="font-size:99%;text-align:center">Sesión 1</p></tp>
#             <tp><p style="font-size:115%;text-align:center">15 de Agosto del 2026</p></tp>
#             <tp><p style="font-size:115%;text-align:center">Prof. Daniel Rambaut</p></tp>
#         </td>
#     </tr>
# </table>

# %% [markdown] id="mGZi_DL7obYK"
# <FONT SIZE=4 COLOR="red"> <strong>Objetivos de la sesión:</strong> </FONT>
#
# ✔  En esta sesión revisaremos algunos conceptos fundamentales de Machine Learning como por ejemplo, aprendizajes supervisado, no supervisado, Tipos de problemas que podemos resolver con ML, tendremos un esquema general del ML para clasificacion, etc.
#
# ✔  Aprenderemos las herramientas necesarias para empezar en el Machine Learning y para hacer análisis Exploratorio de datos, que es un paso fundamental al momento de hacer modelos.
#
# ✔ Por otro lado, estudiaremos en qué consisten los problemas de clasificación y estudiaremos el primer modelo clásico de este tipo: los *k-vecinos más cercanos*.
#

# %% [markdown] id="u16rhg4q8ltY"
# # <FONT SIZE=5 COLOR="Purple"> 0. Herramientas necesarias </FONT>
#

# %% [markdown] id="NyH98dj6-rNZ"
#
# ## <FONT SIZE=5 COLOR="green"> Python </FONT>
#
# Python es un lenguaje de programación de propósito general, usado ampliamente para
#
# *  Desarrollo de aplicaciones
# *  Desarrollo web
# *  Web Scraping
# *  **Ciencia de Datos** ✔
# *  **Visualización** ✔
# *  Aplicaciones a los negocios
# *  **Machine Learning** ✔
# *  **Deep Learning** ✔
#
# Python cuenta con librerías especializadas dependiendo del tipo de tarea. Algunas de ellas son:
#
# <center><img src="assets/librerias.png" alt="Librerias de Python" width="550" height="350"></center> <center><figcaption> <FONT SIZE=1 COLOR="black"> Fuente: https://www.actumlogos.com/python-para-ia.html  </FONT> <figcaption></center>
#
# 1.   **Pandas:** manipulación de datos-estadísticas-data.frames
# 2.   **Matplotlib**: visualización-gráficas
# 3.   **numpy**: operaciones matemáticas
# 4.   **spicy**: realizar cálculo simbólico
# 5.   **scikit-learn**: ejecutar algoritmos de machine learning
# 6.   **NTKL**: Procesamiento de Lenguaje Natural.
# 7.   **seaborn**: creación de gráficos estadísticos
# 8.   **Datetime**: para manipulación de fechas

# %% [markdown] id="L3IE-SDQA0vG"
#
#
# ---
#
#

# %% [markdown] id="0xACY_3koGGf"
# # <FONT SIZE=5 COLOR="Purple"> 1. Conceptos Generales </FONT>
#
# A continuación, presentaremos los conceptos de Inteligencia Artificial (AI), Machine Learning (ML) y Deep Learning (DL).
#
#
# <br>
# <center><FONT SIZE=5 COLOR="green"> AI-ML-DL </FONT></center>
# <br>
#
# - ***Inteligencia Artificial:*** es una combinación de algoritmos y dispositivos, diseñados con el fin de crear máquinas que imiten capacidades del ser humano.
#
# - ***Machine Learning:*** es un campo de la Inteligencia Artificial que a través de algoritmos se trata de identificar patrones en conjuntos de datos masivos y hacer predicciones sobre estos conjuntos.
#
# - ***Deep Learning:*** son algoritmos que usan arquitecturas computacionalmente más complejas, como las redes neuronales, para procesar y hacer predicciones sobre conjuntos de datos.
#
# El siguiente gráfico presenta la relación entre los campos definidos anteriormente.
#
# <br>
#
# <center><img src="assets/ia_ml_dl.png" alt="Relacion entre IA, ML y DL" width="500" height="300"></center><center><figcaption> <FONT SIZE=1 COLOR="black"> Fuente: Elaboración propia  </FONT> <figcaption></center>
# <br>

# %% [markdown] id="nyTDAFSB8KWR"
# ## <FONT SIZE=4 COLOR="green"> 1.1 Machine Learning </FONT>
#
# - El *Machine Learning* o aprendizaje automático de máquina trata de generar conocimiento de los datos. Es decir, extraer información oculta de los datos.
#
# - Es un campo de investigación que intersecta la estadística, inteligencia artificial y ciencias de la computación.
#
# - Las aplicaciones del *Machine Learning* están presenten en muchos contextos de la vida diaria. Desde recomendaciones automáticas de cuáles películas ver, qué comida pedir, cuáles productos comprar, hasta el reconocimiento de amigos en tus fotos.
#
# - Al mirar un sitio web complejo como Facebook, Amazon o Netflix, es muy probable que cada parte del sitio contenga múltiples modelos de machine learning.
#
# Dentro del campo del machine learning se estudian algunos tipos de problemas.

# %% [markdown] id="8-sIR6E78SLW"
#
#
# ## <FONT SIZE=4 COLOR="green"> 1.2 Aprendizaje supervisado </FONT>
#
# En este caso se desea automatizar el proceso de toma de decisiones a partir de ejemplos conocidos. Estos algoritmos de *Machine Learning* aprenden de los pares input/output conocidos, para crear un **output** para un **input** que nunca ha visto antes sin más ayuda.
#
# Vamos a considerar dos conjuntos de datos:
#
# 1. (**Clasificación**) Supongamos que tenemos estos datos
#
# <br>
# <center><img src="assets/supervisado5.png" alt="Datos para clasificacion de diabetes" width="700" height="200"></center>
# <br>
#
# donde,
#
# - ***Pregnancies***: Número de embarazos que ha tenido en su vida
# - ***Glucose***: Nivel de concentración de glucosa en sangre
# - ***BloodPressure***: Presión arterial
# - ***SkinThikness***: Espesor de piel a la altura del triceps
# - ***Insulin***: Respuesta a dosis de insulina en 2 horas
# - ***BMI***: Índice de masa corporal
# - ***DiabetesPedigreeFunction***: Presencia de diabetes en ascendencia directa
# - ***Age***: Edad del paciente
# - ***Outcome***: Variable que queremos predecir:
#    - $1$ : Tiene diabetes
#    - $0$ : No tiene diabetes
#
# ***Problema***: Predecir si una mujer, con ciertos valores en las variables antes mencionadas tiene o no diabetes.
#
# 2. (**Regresión**) Los siguientes datos contienen la información de en pauta publicitaria en diferentes medios (en miles de dólares)
#
# <center><img src="assets/supervisado4.png" alt="Datos para regresion de ventas" width="600" height="200"></center>
#
# ***Problema***: Predecir las ventas en función de las inversiones que se hacen en pauta publicitaria en cada categoria.
#
# Algunos ejemplos de aplicaciones del aprendizaje supervisado
#
# 1. **Clasificación de correos spam**: El modelo de *Machine Learning* utiliza un algoritmo dotado de una gran cantidad de correos electrónicos (los inputs), junto con información sobre si alguno de estos correos electrónicos es spam (objetivo deseado). Dado un nuevo correo electrónico, el algoritmo producirá una predicción sobre si el nuevo correo electrónico es correo no deseado.
#
# 2. **Determinar si un tumor es benigno en base a una imagen médica:** La entrada es la imagen y la salida es si el tumor es benigno. Para crear un conjunto de datos que permita generar un modelo, se necesita una base de datos de imágenes médicas. Así mismo se necesita la opinión y conocimiento de un experto, por lo que un médico debe observar todas las imágenes y decidir qué tumores son benignos y cuáles no. Incluso podría ser necesario hacer un diagnóstico adicional más allá del contenido de la imagen para determinar si el tumor en la imagen es canceroso o no.
#
# 3. **Detección de actividad fraudulenta en transacciones con tarjetas de crédito** La entrada es un registro de la transacción de la tarjeta de crédito y la salida es si es probable que sea fraudulento o no. Suponiendo que usted es la entidad que distribuye las tarjetas de crédito, recopilar un conjunto de datos significa almacenar todas las transacciones y registro si un usuario reporta alguna transacción como fraudulenta.
#
# 4. **Predicción del comsumo de tarjeta de crédito.** Con base a diferentes variables que representan las características de un cliente, se puede predecir su consumo de tarjeta de crédito en un determinado mes o periodo de tiempo.
#
# Por otra parte

# %% [markdown] id="1B7XxQ5cTQEC"
#
#
# ## <FONT SIZE=4 COLOR="green"> 1.3 Aprendizaje No Supervisado </FONT>
#
# Son algoritmos en el que solo se conocen los datos de entrada y no se conoce la salida o etiqueta.
#
# (**Clustering**) En los siguientes datos se muestra información de asesinatos, asaltos, tamaño de la población, violaciones, etc., de estados de EEUU.
#
# <center><img src="assets/no_supervisado1.png" alt="Datos para aprendizaje no supervisado" width="500" height="200"></center>
#
# **Problema**: Identificar grupos de elementos del conjunto que compartan ciertas características.
#
# También se aplica para reducción de dimensionalidad.
#
# Algunos ejemplos de aplicación:
#
# 1. **Segmentación de clientes en grupos con preferencias similares:** Dado un conjunto de registros de clientes, es posible que desee identificar qué clientes son similares, y si hay grupos de clientes con preferencias similares.
#
# 2. **Identificar temas en un conjunto de publicaciones de blog:** Si tiene una gran colección de datos de texto, es posible que desee resumirlos y encontrar temas predominantes en él. Es posible que no sepa de antemano cuáles son estos temas, o cuántos temas puede haber. Por lo tanto, no hay salidas conocidas.
#
# <center><FONT SIZE=5 COLOR="PURPLE"> MACHINE LEARNING </FONT></center>
#
# <br>
# <center><img src="assets/imagen_ml.png" alt="Esquema de machine learning" width="500" height="300"></center><center><figcaption> <FONT SIZE=1 COLOR="black"> Fuente: Elaboración propia  </FONT> <figcaption></center>
# <br>
#
# Observe que para entender y poder determinar si un problema es supervisado o no supervisado debemos tener claro el problema que debemos resolver y qué tipos de variables contiene el conjunto de datos.
#
# Un aspecto importante en el campo del Machine Learning, es que antes de aplicar cualquier modelo, se requiere conocer los datos y alistarlos.
#
# A continuación, revisaremos algunos de estos conceptos.

# %% [markdown] id="DP8ymmF-5lrZ"
# ## <FONT SIZE=4 COLOR="green"> 1.4 Ejercicio de reflexión </FONT>
# **Objetivo**: Diferenciar entre los tipos de aprendizaje (Supervisado vs. No Supervisado).
#
#
# Imagina que la dirección de la empresa te pide usar Inteligencia Artificial para mejorar el departamento. Analiza los siguientes tres casos y determina qué tipo de problema es, es un problema de Aprendizaje Supervisado o uno de aprendizaje No Supervisado? ¿Por qué?
#
# - **Caso A**: Queremos analizar el historial de empleados que han renunciado en los últimos 2 años para que el sistema aprenda a identificar qué empleados actuales tienen un "alto riesgo de fuga".
#
# - **Caso B**: Tenemos 5.000 currículums en una base de datos sin clasificar. Queremos que la IA los agrupe automáticamente por "perfiles similares" (ej. perfiles técnicos, administrativos, creativos) sin que nosotros le digamos previamente qué grupos existen.
#
# - **Caso C**: Queremos predecir cuál debería ser el salario de una nueva posición basándonos en los años de experiencia, nivel educativo y responsabilidades, comparándolo con lo que ya pagamos a otros empleados.

# %% [markdown] id="8fCiGl736flW"
# Espacio para tu respuesta:
#
# - Caso A: ___________________________________
#
# - Caso B: ___________________________________
#
# - Caso C: ___________________________________

# %% [markdown] id="9A4dUqmh_UH3"
# # <FONT SIZE=5 COLOR="Purple"> 2. Análisis exploratorio de datos </FONT>
#
# <center><img src="assets/pandas.webp" alt="Pandas para analisis de datos" width="500" height="250"></center>
#
# + Librería de Python especializada manipulación y análisis de estructuras de datos
# + Permite leer datos en diferentes formatos: csv, excel, bases de datos SQL.
# + Realiza operaciones rápidas y eficientes sobre conjuntos de datos
# + Permite trabajar series de tiempo
# + *import pandas as pd*
# + [Guía Pandas](https://aprendeconalf.es/docencia/python/manual/pandas/)
#
#

# %% [markdown] id="jsBWbocJ_kum"
# ## <FONT SIZE=5 COLOR="purple"> 2.1 ¿Cómo importamos una librería para trabajar?</FONT>

# %% id="yrTNM_Nf_jAQ"
import polars as pl

# %% id="ELTZO-4VJDLd"
import numpy as np

# %% [markdown] id="xpmjfNaOA5vF"
#
#
# ---
#
#

# %% [markdown] id="hTnWXkyrAYDT"
# ## <FONT COLOR="purple"> 2.2 Qué son los dataframes </FONT>

# %% [markdown] id="ZdSTn687_6Cv"
# Los tipos de datos que vamos a trabajar se denominan data.frames
#
# <center><img src="assets/dataframe.png" alt="Estructura de un data frame" width="600" height="300"></center>
#
# Observe que un data.frame puede tener diferentes tipos de variables
#
# <center><img src="assets/tipos_variables.png" alt="Tipos de variables" width="600" height="400"></center>
#
#

# %% [markdown] id="kKIn9fmcA9uN"
#
#
# ---
#
#

# %% [markdown] id="7lG0U_GtAOXB"
# ## <FONT COLOR="PURPLE"> 2.3 Proceso de exploración de datos (EDA) </FONT>
#
# <br>
#
# <center><img src="assets/imagen_eda.png" alt="Proceso de analisis exploratorio de datos" width="550" height="350"></center><center><figcaption> <FONT SIZE=1 COLOR="black"> Fuente: Elaboración propia </FONT> <figcaption></center>
#
# En el gráfico anterior se muestran algunas etapas fundamentales:
#
# 1.	**Preguntas para responder**. Es importante tener claro para qué queremos hacer el procesamiento y análisis de datos. Es decir, qué buscamos responder.
#
# 2.	**Generalidades del conjunto de datos**.  Acá buscamos reconocer la dimensión, datos faltantes, y en general, hacer un resumen del conjunto de datos.
#
# 3.	**Tipos de Variables**. Clasificar las variables en cualitativas y cuantitativas y examinar como se presenta esta información. Por ejemplo, una variable puede estar codificada y verse como numérica, pero ser categórica.
#
# 4.	**Estadística Descriptiva**. Se busca resumir la información. Utilizar medidas de tendencia, de dispersión, de forma, de posición, etc., para entender mejor los datos. Por ejemplo, se identifican datos atípicos usando boxplot.
#
# 5.	**Visualización**.  Es una etapa fundamental en el análisis de datos. Visualizar la información y poder describirla gráficamente. En esta etapa se usan: diagramas de barras, pie, boxplot, histogramas, líneas de densidad, diagramas de dispersión, entre otros.
#
# 6.	**Relación entre variable**. Se explora datos bivariados. Se examinan relaciones entre variables cualitativas (tablas de contingencia) y relaciones entre variables cuantitativas (diagramas de dispersión) se establecen posibles relaciones lineales.
#
# 7.	**Reporte de resultados**. Una vez se haga el proceso de exploración y análisis en Python, R-Studio u otro se deben reportar los resultados y conclusiones de lo que se encontró en el conjunto de datos.

# %% [markdown] id="EQRaWOElfmUN"
# ## <FONT COLOR="purple"> 2.4 Ejemplo </FONT>
# Supongamos que tenemos estos datos
#
# <br>
# <center><img src="assets/supervisado5.png" alt="Datos para clasificacion de diabetes" width="700" height="200"></center>
# <br>
#
# donde,
#
# - ***Pregnancies***: Número de embarazos que ha tenido en su vida
# - ***Glucose***: Nivel de concentración de glucosa en sangre
# - ***BloodPressure***: Presión arterial
# - ***SkinThikness***: Espesor de piel a la altura del triceps
# - ***Insulin***: Respuesta a dosis de insulina en 2 horas
# - ***BMI***: Índice de masa corporal
# - ***DiabetesPedigreeFunction***: Presencia de diabetes en ascendencia directa
# - ***Age***: Edad del paciente
# - ***Outcome***: Variable que queremos predecir:
#    - $1$ : Tiene diabetes
#    - $0$ : No tiene diabetes
#
# ***Problema***: Predecir si una mujer, con ciertos valores en las variables antes mencionadas tiene o no diabetes.

# %% [markdown] id="GgnqjPAU_ESm"
# # <FONT COLOR="green"> 3. Esquema General del Machine Learning para clasificación </FONT>
#
# En está sesión revisaremos algunos conceptos básicos de machine learning en los cuales se profundizará en lo que sigue del notebook
#

# %% [markdown] id="vHiy71gR_Ol4"
#
# ## <FONT COLOR="green"> 3.1 Algoritmos de clasificación: </FONT>
#  son conjuntos de técnicas de aprendizaje supervisado, en el cual el resultado que queremos predecir, es decir, las "etiquetas" (variable $\mathbf{y}$), es discreto.
#
# <br>
# <center><img src="assets/supervisado5.png" alt="Datos para clasificacion de diabetes" width="700" height="200"></center>
# <br>

# %% [markdown] id="0awoq0x9_Vrk"
# ## <FONT COLOR="green"> 3.2 Variable Objetivo: </FONT>
# también denominada **variable de respuesta**. En un algoritmo de aprendizaje de máquina supervisado, es la variable que queremos predecir (por lo general, denotada como $\mathbf{y}$). Esta puede ser discreta o continua. En el primer caso, da lugar a algoritmos de ***clasificación*** y en el segundo caso a algoritmos de ***regresión***.
#
# <br>

# %% [markdown] id="jJAEHo6T_eYf"
#
# ## <FONT COLOR="green"> 3.3 Variables Predictoras: </FONT>
# también denominada ***features***, son las variables que se usarán para predecir la variable objetivo. Estas se denotan como
#
# $$\mathbf{X}=\{X_1,X_2, \dots, X_n \}$$
#
# <br>

# %% [markdown] id="XasroV-z_gvo"
#
#
# ## <FONT COLOR="green"> 3.4 Conjunto de Entrenamiento: </FONT>
#  es el subconjunto de registros que se selecciona para entrenar el modelo. Este conjunto consta de dos partes:
#
# - $X_{train}$ : conjunto de entrenamiento de los predictores o *features*.
#
# - $y_{train}$: conjunto de entrenamiento de la variable objetivo asociada al conjunto $X_{train}$.
#
# El conjunto de entrenamiento se selecciona de manera aleatoria y por lo general se toma el $70\%$ , $75\%$ y $80 \%$.
#
# <br>

# %% [markdown] id="9cbFD8l2_lii"
#
# ## <FONT COLOR="green"> 3.5. Conjunto de Prueba o Validación: </FONT>
#  Es el subconjunto de registros que se selecciona para validar el modelo. Consta de dos partes:
#
# - $X_{test}$ : conjunto de validación de los predictores o *features*.
#
# - $y_{test}$: conjunto de validación de la variable objetivo asociada al conjunto $X_{test}$.
#
# El tamaño de este conjunto es el complemento de los conjuntos de entrenamiento.
#
# <br>

# %% [markdown] id="KMCj9Oh0_uqI"
#

# %% [markdown] id="q0x8AzhXTe_Q"
#
#
# ## <FONT  COLOR="green"> 3.6 Hiperparámetro: </FONT>
#  son variables de configuración externa al modelo original (general) que se pueden ajustar para entrenar el modelo. (cada modelo tiene diferentes hiperparámetros)

# %% [markdown] id="E8kS2FKh_xcv"
#
# ## <FONT COLOR="green"> 3.7 Matriz de Confusión:</FONT>
#  Herramienta usada para evaluar el rendimiento del modelo. (se ampliará más adelante en la siguiente sesión, junto a otros conceptos como las métricas).
#
# <br>
#

# %% [markdown] id="heRB4ulrUB_E"
# ## <FONT COLOR="green"> 3. 8 Resumen </FONT>
# <br>
# <center><img src="assets/esquema_clasificacion.png" alt="Esquema de clasificacion" width="700" height="400"></center> <center><figcaption> <FONT SIZE=1 COLOR="black"> Fuente: Elaboración propia  </FONT> <figcaption></center>
# <br>
#

# %% [markdown] id="QwPl7UrD70Pz"
# ## <FONT SIZE=4 COLOR="green"> 3.9 Ejercicio crítico: Diseño del modelo de selección </FONT>
#
# **Objetivo**: identificar las partes para un modelo de clasificación.
#
# Observa la siguiente tabla teórica sobre candidatos a un puesto de trabajo:
#
# <br>
#
# | Edad | Años Exp. | Nivel Inglés | Test Psicotécnico | ¿Contratado? | Desempeño (1-10) |
# |------|------------|--------------|-------------------|--------------|------------------|
# | 25   | 2          | B2           | 85                | Sí           | 7.5              |
# | 40   | 15         | C1           | 90                | Sí           | 9.0              |
# | 30   | 5          | B1           | 60                | No           | NaN              |
#
# <br>
#
# Responde lo siguiente:
#
# **a)** Si nuestro objetivo es predecir si un nuevo candidato será contratado o no:
#
#   - ¿Cuál es la Variable Objetivo $\mathbf{y}$?
#
#   - ¿Es un problema de Clasificación o de Regresión?
#
# <br>
#
# **b)** Si nuestro objetivo es predecir el puntaje de Desempeño (1-10) que tendrá el candidato una vez entre:
#
#   - ¿Es un problema de Clasificación o de Regresión?
#
#   - ¿Qué pasaría con la fila del candidato que "No" fue contratado para entrenar este modelo específico?
#
# <br>
#
# **c)** ¿Crees que la variable "Edad" debería ser una Variable Predictora $\mathbf{X}$? ¿Qué riesgos éticos o de sesgo encuentras al incluirla?

# %% [markdown] id="s1oCh6nXUQ0g"
# # <FONT SIZE=5 COLOR="red"> 4. Algoritmo de clasificación KNN : K-vecinos más cercanos </FONT>
#
# Revisaremos el algoritmo de clasificación ***KNN: k-nearest neigbors*** : K-vecinos más cercanos.

# %% [markdown] id="FzTKyySDUHH0"
# ## <FONT SIZE=4 COLOR="red"> 4.1 ¿En qué consiste? </FONT>
#
# Este algoritmo consiste en consiste en clasificar los valores de una variable categórica de acuerdo con los vecinos más cercanos. A continuación explicaremos el funcionamiento

# %% [markdown] id="Jf97bF18Ul6J"
# 1. Supongamos que queremos clasificar el cuadrado amarillo en las dos posibles clases.
#
# <br>
# <center><img src="assets/knn1.png" alt="Clasificacion KNN, ejemplo 1" width="600" height="450"></center> <center><figcaption> <FONT SIZE=1 COLOR="black"> Fuente: Libro Guía  </FONT> <figcaption></center>
#
#
#

# %% [markdown] id="EU7Y3anyUpRo"
# 2. Por ejemplo, si tenemos otro valor de $k$ la clasificación puede cambiar.
#
# <br>
# <center><img src="assets/knn2.png" alt="Clasificacion KNN, ejemplo 2" width="600" height="450"></center> <center><figcaption> <FONT SIZE=1 COLOR="black"> Fuente: Libro Guía  </FONT> <figcaption></center>
#
#

# %% [markdown] id="5_SmSgqrUsxT"
# ## <FONT SIZE=4 COLOR="red"> .42 Descripción del algoritmo: pseudocódigo </FONT>
#
# - Determinar el valor de $k$.
#
# - Calcular la distancia del punto a clasificar a todos los otros puntos.
#
# - Ordenar de manera ascendente las distancias.
#
# - Tomar los puntos más cercanos al punto a clasificar de acuerdo con el valor que le asignemos a $k$.
#
# - Contar cuántos puntos de cada clase están en la vecindad y definimos por mayoría.
#
# - Por ejemplo: Si k es 3 y tenemos
#
#    + Distancia 1 : 2.5 : clase a
#
#    + Distancia 2 : 2.51 : clase b
#
#    + Distancia 3 : 2.53 : clase a
#
#   Conclusión: El punto se clasifica en la clase a.
#
# En caso de que haya empate se pueden definir algunos criterios de desempate. Por ejemplo:
#
#   - la clase que contenga al vecino más cercano.
#   - la clase con la distancia media más pequeña.

# %% [markdown] id="e3r_NUA3U3-w"
# ## <FONT SIZE=4 COLOR="red"> 4.3 Sobre el algoritmo </FONT>
#
# A continuación, algunos puntos importantes que se deben tener en cuenta sobre el algoritmo ***knn***
#
# 1. Observe que no se genera un modelo que sea consecuencia de un entrenamiento previo, sino que el aprendizaje se da en el mismo momento en el que se prueban los datos de validación. A este tipo de algoritmos se les denomina ***lazy learning methods***.
#
# 2. Como utiliza todo el set de entrenamiento para calcular las distancias, se tiene un costo computacional alto.
#
# 3. Es un algoritmo que da buenos resultados, pero es recomendable para conjuntos de datos no tan grandes.
#
# 4. Es muy sensible al valor de $k$ y a la distancia seleccionada.
#
# 5. Es importante escalar los datos.

# %% [markdown] id="TRdOW3KeVENL"
# ## <FONT SIZE=4 COLOR="red"> 4.4 Sobre las distancias </FONT>
#
# El algoritmo $knn$ está fundamentado en la distancia entre dos puntos. Si bien, una de las distancias más conocida es la distancia euclideana, existen otras distancias que se pueden usar para el algoritmo.
#
# ## <FONT SIZE=3 COLOR="red"> Distancia Euclideana </FONT>
#
# $$ \left (\sum \limits_{i=1}^m (x_i-y_i)^2 \right)^{1/2}$$
#
# Esta métrica se puede usar para variables con valores discretos o continuos en general.
#
# ## <FONT SIZE=3 COLOR="red"> Distancia de Manhattan</FONT>
#
# $$ \sum \limits_{i=1}^{m} |x_i-y_i|$$
#
# Observe que es más sencilla que la euclideana (tiene menos cálculos)
#
# <br>
# <center><img src="assets/knn3.png" alt="Distancias usadas por KNN" width="600" height="450"></center> <center><figcaption> <FONT SIZE=1 COLOR="black"> Fuente: Elaboración propia  </FONT> <figcaption></center>
#
# La métrica euclideana y de Manhattan tienen una generalización que se denomina.
#
# ## <FONT SIZE=3 COLOR="red"> Distancia de Minkowski</FONT>
#
# $$ \left (\sum \limits_{i=1}^m (x_i-y_i)^p \right)^{1/p}$$
#
# ## <FONT SIZE=3 COLOR="red"> Distancia de Hamming</FONT>
#
# $$Distancia \,\, Hamming : \begin{cases} 0 & \text{si $x=y$} \\ 1 & \text{si $x \neq y$}   \end{cases}$$
#
# Esta distancia es equivalente a la de Manhattan para variables binarias, es decir, que solo tienen ceros y unos
#
# $$ a = \begin{pmatrix} 1 \\ 0 \\ 1 \\ 1 \end{pmatrix}  \qquad b = \begin{pmatrix} 0 \\ 1 \\ 1 \\ 1 \end{pmatrix}$$
#
# ## <FONT SIZE=3 COLOR="red"> Distancia Euclideana con pesos </FONT>
#
# $$ \left (\sum \limits_{i=1}^m w_i(x_i-y_i)^2 \right)^{1/2}$$
#
# donde los pesos resultan, por ejemplo, del escalamiento de los datos.
#
#

# %% [markdown] id="_2ifL4chVK2e"
# ## <FONT SIZE=4 COLOR="red"> 3.6 Sobre el escalamiento </FONT>
#
# El algoritmo *knn* está fundamentado en seleccionar mínimas distancias, en ese orden de ideas, observe lo siguiente.
#
# - Si se tiene una variable $X_1$ que varía en $[1,2]$ y otra variable $X_2$ que varía en $[1000, 2000]$. Al calcular distancias con los valores de estas variables $X_2$ dominará a $X_1$ que tiene valores más pequeños y como la algoritmo utiliza la distancia para clasificar entonces queda sesgado el resultado.
#
# Por lo anterior, se deben escalar las variables predictoras y en general se usan las siguientes dos funciones.
#
# ## <FONT SIZE=3 COLOR="red"> StandardScaler </FONT>
#
# $$\dfrac{X-\mu}{\sigma}$$
#
#
# ## <FONT SIZE=3 COLOR="red"> MaxminScaler </FONT>
#
# $$\dfrac{X-X_{min}}{X_{max}-X_{min}}$$
#
#
#
#

# %% [markdown] id="UwEPzK5xVoh-"
#

# %% [markdown] id="jU2O_Ocdk-MD"
# # <FONT SIZE=5 COLOR="purple"> 5. Ejemplo Práctico </FONT>
#
# - Haremos un ejemplo práctico.
#
# - Iniciaremos indicando las librerías que debemos usar.

# %% [markdown] id="LQk9kTV1lZw0"
# ## <FONT SIZE=4 COLOR="red"> 5.1 Librerías de trabajo </FONT>

# %% id="fmJaik-Alf_S"
# Manipulación de data.frames
import polars as pl
import numpy as np

# Librerías para Gráficos
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
# %matplotlib inline
plt.style.use("ggplot")
plt.rcParams["figure.figsize"] = (15,6)

# Librerías para datos de entrenamiento y prueba
from sklearn.model_selection    import train_test_split

# Para preprocesamiento
from sklearn.preprocessing      import StandardScaler, MinMaxScaler

# Para aplicar k-nearest neiborg
from sklearn.neighbors          import KNeighborsClassifier

# Métricas de evaluación
from sklearn.metrics            import confusion_matrix, ConfusionMatrixDisplay, classification_report
from sklearn.metrics            import accuracy_score, precision_score, recall_score, f1_score

# Optimización de hiperparámetros
from sklearn.model_selection    import GridSearchCV, RandomizedSearchCV

# Para ignorar los warnings
import warnings
warnings.filterwarnings("ignore")

# %% [markdown] id="HkINXW4WmU5O"
# ## <FONT SIZE=4 COLOR="red"> 5.2 Contexto del problema </FONT>
#
#  En este caso intentaremos predecir a qué categoría corresponde un conjunto de datos.
#
# En términos generales, seremos mucho más precisos si tenemos que modelar el comportamiento de una categoría que de una variable continua, por lo que veremos que muchas veces, incluso los problemas de predecir variables numéricas se pueden discretizar y convertir en problemas de clasificación.
#
# En este caso, veremos un caso típico de un problema de clasificación. Queremos predecir si una integrante de una muestra que representa a una población, tiene diabetes. Queremos hacer esto a partir de múltiples variables que tenemos de cada uno de los pacientes para eso usaremos la base de datos vista en la sesión 2:
#
# - ***Pregnancies***: Número de embarazos que ha tenido en su vida
# - ***Glucose***: Nivel de concentración de glucosa en sangre
# - ***BloodPressure***: Presión arterial
# - ***SkinThikness***: Espesor de piel a la altura del triceps
# - ***Insulin***: Respuesta a dosis de insulina en 2 horas
# - ***BMI***: Índice de masa corporal
# - ***DiabetesPedigreeFunction***: Presencia de diabetes en ascendencia directa
# - ***Age***: Edad del paciente
# - ***Outcome***: Variable que queremos predecir:
#    - $1$ : Tiene diabetes
#    - $0$ : No tiene diabetes
#
#

# %% [markdown] id="gvKTG0D5pHv9"
# ## <FONT SIZE=4 COLOR="red"> 5.3 Importar los datos </FONT>
#
# Vamos a traer los datos del GitHub de la siguiente manera.

# %% [markdown] id="59MSJIyYolvs"
# Lo primero que haremos es importar los datos que están en el siguiente link o pueden ser descargados de la página de Kaggle.

# %% id="gPKIEFqGqDJn"
url = "https://raw.githubusercontent.com/Fabian830348/Bases_Datos/master/diabetes.csv"

# %% id="TCkook-pqDG3"
diabetes = pl.read_csv(url)

# %% [markdown] id="wlgRkB50rYvW"
# ## <FONT SIZE=4 COLOR="red"> 5.4 Exploración de los datos </FONT>
#
# Es importante revisar la base de datos antes de empezar cualquier otro análisis. Idealmente nos familiarizamos con las variables, los tipos de variables, el número de filas, de qué trata cada variable, y en general, comprendemos qué historia nos cuenta esta base de datos

# %% id="04IgiY6vgxgD"
# primeros registros
diabetes.head()

# %% id="STcYQTSag1Kn"
# últimos registros
diabetes.tail(4)

# %% id="8abpttSyg2jj"
# tamaño de los datos
diabetes.shape

# %% id="gQ7h76ruamNK"
# nombre de las columnas
diabetes.columns

# %% id="E3GzMnUpg43x"
# información de los datos
diabetes.glimpse()

# %% id="DQoZwNikg9Jr"
# resumen estadístico variables cuantitativas
diabetes.describe()

# %% id="uoFRd8uMqTNB"
# contar las categorias de la variable outcome
diabetes['Outcome'].value_counts().sort('Outcome')

# %% [markdown] id="hS0mIidmxVYL"
# Hacemos la gráfica de barras de las frecuencias

# %% colab={"base_uri": "https://localhost:8080/", "height": 542} id="Emu5coqS8VXC" outputId="2b8b0f33-5e34-4f70-b24e-d936786dfad8"
conteo = diabetes['Outcome'].value_counts().sort('Outcome')
px.bar(conteo, x='Outcome', y='count')

# %% [markdown] id="rDxGEnEswVeV"
# **Cuidado 🍳**: En esta parte hay que tener especial atención,  particularmente en otros algoritmos. Cuando los datos están desbalanceados pueden afectar los resultados. Para esto se puede usar algunas técnicas de balanceo de datos: *subsampling*, *oversampling* y *smote*.
#
# - Para continuar con el ejercicio, trabajaremos con las clases como están.

# %% [markdown] id="iod7SswDw-a3"
# ## <FONT SIZE=4 COLOR="red"> 5.6 Conjunto de Entrenamiento y Prueba </FONT>
#
# - **data training:** Datos que usamos para entrenar el modelo.
#
# - **testing data:** Datos que reservamos para comprobar si el modelo generado a partir de los datos funciona
#
# Normalmente, usamos $70\%-30\%$ / $80\%-20\%$

# %% id="3IzpP8VDKv5x"
# variables predictoras
X = diabetes.drop("Outcome")
# variable objetivo
y = diabetes["Outcome"]

# %% id="RsCcPQYaLRca"
# seleccionar conjunto de train y test (entrenamiento y prueba)
X_train, X_test, y_train, y_test = train_test_split(X,                        # variables predictoras
                                                    y,                        # variable de respuesta
                                                    random_state = 0,         # semilla para que al ejecutar siempre de igual
                                                    test_size = 0.2)          # tamaño del conjunto de prueba

# %% colab={"base_uri": "https://localhost:8080/", "height": 206} id="-BHq7Cw4NBFd" outputId="1183dcaf-20d6-46f0-a953-901724de82ea"
X_train.head(5)

# %% colab={"base_uri": "https://localhost:8080/"} id="6oYBnVRHOQgk" outputId="d9423ae7-af8f-4035-fb0e-314de6eda486"
y_train.head(5)

# %% [markdown] id="q1LiaIp50Y2L"
# Veamos los tamaños de estos conjuntos

# %% colab={"base_uri": "https://localhost:8080/"} id="pJRMrfwi0e_g" outputId="8946688a-6c8d-4c87-d225-5a096aecd9a3"
X_train.shape
y_train.shape
X_test.shape
y_test.shape

# %% [markdown] id="_IvjR_fr0mBP"
# ## <FONT SIZE=4 COLOR="red"> 5.7 Escalar las variables predictoras </FONT>
#
# - En los algoritmos donde se vea involucrada una distancia es importante hacer el escalamiento.
#
# - Una recomendación es hacer el escalamiento después de dividir en entrenamiento y prueba. Ya que la idea es que no se sobreentrene el modelo.
#

# %% id="NXOutoIs1CcK"
escalar = StandardScaler()
X_train = escalar.fit_transform(X_train)
X_test = escalar.transform(X_test)

# %% id="Bi3nj5NmDTgv"
X_train

# %% [markdown] id="aJncrGo-1F_R"
# **Observación importante de lo anterior**.
#
# a. Para $X_{train}$ usamos ***fit.transform*** esto significa que los datos se este conjunto se escalarán con base a su $\mu$ media y $\sigma$ desviación estándar. (que no son lo mismo que calcularla sobre todo el conjunto)
#
# b. Para $X_{test}$ usamos ***.transform*** esto significa que para escalar los datos del conjunto de prueba se usan los parámetros $\mu$ y $\sigma$ obtenidos en la parte a. con el conjunto de entrenamiento $X_{train.}$
#
# <br>
# <center><img src="assets/knn4.png" alt="Escalamiento de datos de entrenamiento y prueba" width="600" height="400"></center> <center><figcaption> <FONT SIZE=1 COLOR="black"> Fuente: Elaboración propia  </FONT> <figcaption></center>
#
#

# %% [markdown] id="ImKRyOLx2vVs"
# ## <FONT SIZE=4 COLOR="red"> 5.8 Selección de $k$  </FONT>
#
# - Inicialmente seleccionamos un valor un $k$, ejecutamos el modelo y luego revisamos otros valores de $k$ para ver si tenemos mejores resultados.

# %% [markdown] id="j904Yynv3D7C"
# ## <FONT SIZE=4 COLOR="red"> 5.9 Generar el Modelo  </FONT>
#
# En esta parte usaremos la librería *sciki-learn* y la función *KNeighborsClassifier*

# %% colab={"base_uri": "https://localhost:8080/", "height": 74} id="EVHP8iWx3GKI" outputId="54a1eb8f-b048-4241-f6c0-cd03f62a7f62"
KNN = KNeighborsClassifier(n_neighbors = 15,              # número de vecinos k=15 variar.
                           metric = 'euclidean')          # métrica euclideana
KNN.fit(X_train,y_train)

# %% [markdown] id="PsoZTQB33j66"
# ## <FONT SIZE=4 COLOR="red"> 5.10 Evaluar en el conjunto de Prueba  </FONT>
#
# Luego de tener el modelo entrenado con **X_{train}** y **y_{train}** pasamos a calcularlo en el conjunto **X_{test}**, con lo cual obtendremos valores de predicción del modelo.

# %% colab={"base_uri": "https://localhost:8080/"} id="Y3LZQ9s63n1U" outputId="36799e58-9457-491f-a7bb-2791a73a8528"
y_pred = KNN.predict(X_test)
y_pred

# %% colab={"base_uri": "https://localhost:8080/"} id="U__P1T43EgT_" outputId="117ae965-8ba3-4e40-c00b-540a4c4ac112"
np.array(y_test)

# %% [markdown] id="3Gzcmncd7CRx"
# La pregunta que nos hacemos ahora es:
#
# ***¿Qué tanta coincidencia hay en el modelo con los datos de prueba?***
#
# La respuesta a esta pregunta la tendremos justamente comparando **$y_{pred}$** con **$y_{test}$**. Esto lo haremos con una herramienta muy importante en Machine Learning y modelos de clasificación denominada ***matriz de confusión*** que veremos en la próxima sesión!.
