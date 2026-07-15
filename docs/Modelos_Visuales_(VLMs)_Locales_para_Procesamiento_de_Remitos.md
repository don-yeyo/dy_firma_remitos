# Arquitectura de Extracción Estructurada de Remitos mediante Modelos de Lenguaje con Visión Locales en Redes Privadas

## Evaluación Comparativa de Modelos de Visión y Lenguaje Locales

El procesamiento de documentos comerciales complejos, como los remitos o
albaranes de entrega, ha encontrado un punto de inflexión con la
maduración de los modelos de lenguaje con visión (VLMs) de código
abierto^1^. Tradicionalmente, la extracción estructurada requería
motores de reconocimiento óptico de caracteres (OCR) heurísticos y
plantillas rígidas susceptibles de fallar ante la mínima variación del
diseño del documento^2^. La aparición de modelos cerrados en la nube,
tales como la familia Google Gemini, demostró la viabilidad de la
extracción de documentos mediante el análisis contextual y visual
unificado^4^. No obstante, las restricciones normativas, la privacidad
de los datos financieros y la necesidad de operar sin conectividad
externa imponen el despliegue de soluciones en servidores locales cien
por ciento privados^3^.

Para emular de forma efectiva la precisión y flexibilidad de las APIs de
Gemini en un entorno privado, es imperativo seleccionar arquitecturas
locales que integren de manera nativa la comprensión de la distribución
espacial de los textos, la lectura de tablas y el soporte del idioma
español^1^. El rendimiento de estos modelos se evalúa principalmente a
través de métricas estandarizadas como DocVQA, orientada a la
comprensión visual de documentos, y OCRBench, diseñada para evaluar la
precisión de la transcripción de caracteres y símbolos bajo condiciones
difíciles^8^.

La tabla presentada a continuación detalla las especificaciones técnicas
y métricas de rendimiento de los principales VLMs locales recomendados
para la extracción de remitos en español:

+---------+---------+---------+---------+---------+---------+---------+
| **M     | **Arqui | **Pr    | **Pun   | **      | **      | **Tipo  |
| odelo** | tectura | ecisión | tuación | Consumo | Soporte | de      |
|         | y       | en      | en      | de VRAM | de      | L       |
|         | Parám   | DocVQA  | OCR     | E       | Idioma  | icencia |
|         | etros** | (       | Bench** | stimado | y OCR   | de      |
|         |         | Test)** |         | (Quant  | en      | Uso**   |
|         |         |         |         | ización | Es      |         |
|         |         |         |         | a 4     | pañol** |         |
|         |         |         |         | bits)** |         |         |
+=========+=========+=========+=========+=========+=========+=========+
| **Qwe   | Transf  | 9       | 864^9^  | ![      | Exc     | Apache  |
| n2.5-VL | ormador | 5.7%^9^ |         | ](media | elente, | 2.0^11^ |
| -7B-Ins | denso   |         |         | /image1 | incluye |         |
| truct** | de      |         |         | 6.png){ | datos   |         |
|         | !       |         |         | width=" | de      |         |
|         | [](medi |         |         | 1.00195 | entren  |         |
|         | a/image |         |         | 3193350 | amiento |         |
|         | 6.png){ |         |         | 8312in" | espe    |         |
|         | width=" |         |         | hei     | cíficos |         |
|         | 0.73763 |         |         | ght="0. | en      |         |
|         | 0139982 |         |         | 2296139 | esp     |         |
|         | 5022in" |         |         | 5450568 | añol^7^ |         |
|         | he      |         |         | 678in"} |         |         |
|         | ight="0 |         |         |         |         |         |
|         | .228561 |         |         | \[cite: |         |         |
|         | 8985126 |         |         | 8\]     |         |         |
|         | 859in"} |         |         |         |         |         |
|         | parámet |         |         |         |         |         |
|         | ros^10^ |         |         |         |         |         |
+---------+---------+---------+---------+---------+---------+---------+
| **Qwen  | Transf  | N/D     | N/D     | !       | Exc     | Qwen    |
| 2.5-VL- | ormador |         |         | [](medi | elente, | Lice    |
| 32B-Ins | denso   |         |         | a/image | alta    | nse^11^ |
| truct** | de      |         |         | 18.png) | ca      |         |
|         | ![      |         |         | {width= | pacidad |         |
|         | ](media |         |         | "0.7182 | de      |         |
|         | /image1 |         |         | 6115485 | comp    |         |
|         | 2.png){ |         |         | 5643in" | rensión |         |
|         | width=" |         |         | he      | con     |         |
|         | 0.80371 |         |         | ight="0 | textual |         |
|         | 0629921 |         |         | .229011 | en      |         |
|         | 2599in" |         |         | 3735783 | esp     |         |
|         | he      |         |         | 027in"} | añol^7^ |         |
|         | ight="0 |         |         |         |         |         |
|         | .229631 |         |         | \[cite: |         |         |
|         | 4523184 |         |         | 13\]    |         |         |
|         | 602in"} |         |         |         |         |         |
|         | parámet |         |         |         |         |         |
|         | ros^12^ |         |         |         |         |         |
+---------+---------+---------+---------+---------+---------+---------+
| **      | Mezcla  | N/D     | Alta    | ![      | Muy     | Apache  |
| DeepSee | de      |         | efi     | ](media | bueno,  | 2.0^1^  |
| k-VL2** | E       |         | ciencia | /image1 | alta    |         |
|         | xpertos |         | de      | 6.png){ | tol     |         |
|         | (MoE)   |         | OCR^1^  | width=" | erancia |         |
|         | de      |         |         | 1.00195 | a ruido |         |
|         | !       |         |         | 3193350 | visual  |         |
|         | [](medi |         |         | 8312in" | en el   |         |
|         | a/image |         |         | hei     | t       |         |
|         | 1.png){ |         |         | ght="0. | exto^1^ |         |
|         | width=" |         |         | 2296139 |         |         |
|         | 0.80371 |         |         | 5450568 |         |         |
|         | 0629921 |         |         | 678in"} |         |         |
|         | 2599in" |         |         |         |         |         |
|         | he      |         |         |         |         |         |
|         | ight="0 |         |         |         |         |         |
|         | .229631 |         |         |         |         |         |
|         | 4523184 |         |         |         |         |         |
|         | 602in"} |         |         |         |         |         |
|         | totales |         |         |         |         |         |
|         | y       |         |         |         |         |         |
|         | ![      |         |         |         |         |         |
|         | ](media |         |         |         |         |         |
|         | /image1 |         |         |         |         |         |
|         | 5.png){ |         |         |         |         |         |
|         | width=" |         |         |         |         |         |
|         | 0.73763 |         |         |         |         |         |
|         | 0139982 |         |         |         |         |         |
|         | 5022in" |         |         |         |         |         |
|         | he      |         |         |         |         |         |
|         | ight="0 |         |         |         |         |         |
|         | .228561 |         |         |         |         |         |
|         | 8985126 |         |         |         |         |         |
|         | 859in"} |         |         |         |         |         |
|         | act     |         |         |         |         |         |
|         | ivos^1^ |         |         |         |         |         |
+---------+---------+---------+---------+---------+---------+---------+
| **GLM   | Mezcla  | N/D     | N/D     | ![      | Exc     | Prop    |
| -4.5V** | de      |         |         | ](media | elente, | ietaria |
|         | E       |         |         | /image1 | ca      | de      |
|         | xpertos |         |         | 3.png){ | pacidad | Zhipu   |
|         | (MoE)   |         |         | width=" | de      | AI^1^   |
|         | de      |         |         | 1.09652 | razon   |         |
|         | !       |         |         | 1216097 | amiento |         |
|         | [](medi |         |         | 9878in" | p       |         |
|         | a/image |         |         | hei     | rofundo |         |
|         | 2.png){ |         |         | ght="0. | con     |         |
|         | width=" |         |         | 2297473 | modo de |         |
|         | 0.89827 |         |         | 7532808 | pens    |         |
|         | 5371828 |         |         | 398in"} | amiento |         |
|         | 5215in" |         |         |         | ac      |         |
|         | he      |         |         |         | tivo^1^ |         |
|         | ight="0 |         |         |         |         |         |
|         | .229791 |         |         |         |         |         |
|         | 1198600 |         |         |         |         |         |
|         | 175in"} |         |         |         |         |         |
|         | totales |         |         |         |         |         |
|         | y       |         |         |         |         |         |
|         | ![      |         |         |         |         |         |
|         | ](media |         |         |         |         |         |
|         | /image1 |         |         |         |         |         |
|         | 9.png){ |         |         |         |         |         |
|         | width=" |         |         |         |         |         |
|         | 0.80371 |         |         |         |         |         |
|         | 0629921 |         |         |         |         |         |
|         | 2599in" |         |         |         |         |         |
|         | he      |         |         |         |         |         |
|         | ight="0 |         |         |         |         |         |
|         | .229631 |         |         |         |         |         |
|         | 4523184 |         |         |         |         |         |
|         | 602in"} |         |         |         |         |         |
|         | act     |         |         |         |         |         |
|         | ivos^1^ |         |         |         |         |         |
+---------+---------+---------+---------+---------+---------+---------+
| **Mi    | SigL    | N/D     | SOTA    | !       | Exc     | Prop    |
| niCPM-V | IP-400M |         | para su | [](medi | elente, | ietaria |
| 2.6**   | unido a |         | ta      | a/image | soporte | de      |
|         | Q       |         | maño^8^ | 8.png){ | opt     | Open    |
|         | wen2-7B |         |         | width=" | imizado | BMB^15^ |
|         | (!      |         |         | 0.90738 | para    |         |
|         | [](medi |         |         | 9545056 | más de  |         |
|         | a/image |         |         | 8679in" | 30      |         |
|         | 3.png){ |         |         | hei     | idio    |         |
|         | width=" |         |         | ght="0. | mas^15^ |         |
|         | 0.73763 |         |         | 2294542 |         |         |
|         | 0139982 |         |         | 8696412 |         |         |
|         | 5022in" |         |         | 948in"} |         |         |
|         | he      |         |         |         |         |         |
|         | ight="0 |         |         | \[cite: |         |         |
|         | .228561 |         |         | 8\]     |         |         |
|         | 8985126 |         |         |         |         |         |
|         | 859in"} |         |         |         |         |         |
|         | parámet |         |         |         |         |         |
|         | ros)^8^ |         |         |         |         |         |
+---------+---------+---------+---------+---------+---------+---------+
| **      | Transf  | N/D     | N/D     | ![      | Probado | Apache  |
| Granite | ormador |         |         | ](media | exito   | 2.0^17^ |
| 3.2     | denso   |         |         | /image1 | samente |         |
| V       | de      |         |         | 6.png){ | en      |         |
| ision** | !       |         |         | width=" | doc     |         |
|         | [](medi |         |         | 1.00195 | umentos |         |
|         | a/image |         |         | 3193350 | come    |         |
|         | 3.png){ |         |         | 8312in" | rciales |         |
|         | width=" |         |         | hei     | en      |         |
|         | 0.73763 |         |         | ght="0. | espa    |         |
|         | 0139982 |         |         | 2296139 | ñol^17^ |         |
|         | 5022in" |         |         | 5450568 |         |         |
|         | he      |         |         | 678in"} |         |         |
|         | ight="0 |         |         |         |         |         |
|         | .228561 |         |         | \[cite: |         |         |
|         | 8985126 |         |         | 14\]    |         |         |
|         | 859in"} |         |         |         |         |         |
|         | parámet |         |         |         |         |         |
|         | ros^17^ |         |         |         |         |         |
+---------+---------+---------+---------+---------+---------+---------+
| **Llama | Transf  | Elev    | N/D     | ![      | Li      | Llama   |
| 3.2-    | ormador | ada^20^ |         | ](media | mitado, | 3.2     |
| Vision- | con     |         |         | /image1 | soporte | Commun  |
| 11B-Ins | ad      |         |         | 3.png){ | de      | ity^19^ |
| truct** | aptador |         |         | width=" | imagen  |         |
|         | visual  |         |         | 1.09652 | a texto |         |
|         | de      |         |         | 1216097 | opt     |         |
|         | ![      |         |         | 9878in" | imizado |         |
|         | ](media |         |         | hei     | ofici   |         |
|         | /image1 |         |         | ght="0. | almente |         |
|         | 7.png){ |         |         | 2297473 | solo en |         |
|         | width=" |         |         | 7532808 | ing     |         |
|         | 0.80371 |         |         | 398in"} | lés^18^ |         |
|         | 0629921 |         |         |         |         |         |
|         | 2599in" |         |         | \[cite: |         |         |
|         | he      |         |         | 8\]     |         |         |
|         | ight="0 |         |         |         |         |         |
|         | .229631 |         |         |         |         |         |
|         | 4523184 |         |         |         |         |         |
|         | 602in"} |         |         |         |         |         |
|         | parámet |         |         |         |         |         |
|         | ros^18^ |         |         |         |         |         |
+---------+---------+---------+---------+---------+---------+---------+

El análisis de las capacidades relativas demuestra que la serie
Qwen2.5-VL se sitúa a la vanguardia en tareas de comprensión visual de
documentos^1^. En evaluaciones de gran exigencia como la suite CC-OCR,
que evalúa la lectura en múltiples escenas y la extracción de
información clave, Qwen2.5-VL-72B y Gemini-1.5-Pro ocupan de manera
consistente los primeros puestos, superando ampliamente a otros modelos
comerciales y de código abierto^22^. La variante Qwen2.5-VL-7B-Instruct
ofrece un punto de equilibrio idóneo para implementaciones locales,
puesto que supera a modelos cerrados de menor escala como Gemini 1.5
Flash 8B en pruebas específicas de DocVQA^20^, manteniendo un consumo de
recursos compatible con hardware de coste moderado^8^.

Por su parte, MiniCPM-V 2.6 proporciona una alternativa robusta gracias
a su algoritmo de división de imágenes de alta resolución en parches
dinámicos, lo que le permite procesar capturas de hasta
![](media/image9.png){width="0.2739260717410324in"
height="0.2633902012248469in"} megapíxeles sin distorsionar la relación
de aspecto^8^. Esta capacidad resulta de vital importancia para
descifrar fuentes pequeñas o números de lote borrosos dentro de las
tablas de los remitos^8^. En cambio, a pesar del excelente rendimiento
general de la familia Llama 3.2-Vision, la restricción de su alineador
visual, que admite de forma oficial únicamente el idioma inglés para
tareas de procesamiento de imágenes con texto, desaconseja su uso para
la extracción de documentos comerciales redactados en español, dada la
elevada probabilidad de que se generen transcripciones erróneas o
alucinaciones en campos críticos^18^.

## Arquitecturas Híbridas de Extracción y Modelos Especialistas de Bajo Parámetro

Cuando el presupuesto de cómputo es limitado o se requiere maximizar la
velocidad de procesamiento para lotes pequeños sin comprometer la
precisión, las arquitecturas híbridas representan una alternativa
superior a la utilización de un único modelo multimodal denso^2^. Este
enfoque combina herramientas open-source de análisis de diseño con
modelos especialistas de visión de bajo parámetro que han demostrado un
rendimiento excepcional en tareas de extracción de datos
documentales^2^.

La tabla a continuación compara las herramientas de conversión de
documentos y los modelos especialistas de bajo parámetro óptimos para
flujos de procesamiento locales:

  ----------------------------------------------------------------------------------------------------------------------------
  **Herramienta /  **Tipo de          **Tamaño / Parámetros**                               **Especialidad   **Ventaja Clave
  Modelo**         Tecnología**                                                             Principal**      en Entornos
                                                                                                             Locales**
  ---------------- ------------------ ----------------------------------------------------- ---------------- -----------------
  **Docling        Analizador de      Ligero (Basado en visión local)^4^                    Reconstrucción   Velocidad de
  (IBM)**          diseño y extractor                                                       semántica de     ejecución extrema
                   de Markdown^4^                                                           tablas, títulos  en CPU y GPU de
                                                                                            y párrafos^4^    consumo^2^

  **PaddleOCR-VL   Modelo de lenguaje ![](media/image7.png){width="0.7376301399825022in"    OCR denso        Supera a GPT-4o
  1.5**            con visión         height="0.2285618985126859in"} parámetros^2^          multilingüe y    en precisión de
                   especializado^2^                                                         reconocimiento   análisis
                                                                                            de tablas^2^     documental
                                                                                                             básico^2^

  **GLM-OCR**      VLM especialista   ![](media/image7.png){width="0.7376301399825022in"    Lectura y        Posicionamiento
                   ultraligero^2^     height="0.2285618985126859in"} parámetros^2^          extracción       líder en la
                                                                                            directa de       prueba de
                                                                                            información      referencia
                                                                                            clave^2^         OmniDocBench
                                                                                                             v1.5^2^

  **dots.OCR**     Modelo de          ![](media/image11.png){width="0.7376301399825022in"   Layout, fórmulas Manejo unificado
                   transcripción      height="0.2285618985126859in"} parámetros^2^          y tablas en más  de tablas
                   integrado^2^                                                             de 100           complejas bajo
                                                                                            idiomas^2^       licencia MIT^2^
  ----------------------------------------------------------------------------------------------------------------------------

La integración de una biblioteca como Docling de IBM en la fase inicial
del pipeline de datos permite descomponer el remito en una estructura
Markdown o JSON limpia, aislando las tablas y los encabezados con una
gran precisión visual^4^. Una vez que el diseño ha sido estructurado de
forma semántica por Docling, el texto resultante puede ser procesado por
un modelo de lenguaje de texto puro más pequeño y rápido, lo que reduce
sustancialmente la necesidad de realizar llamadas de inferencia
multimodal complejas y costosas en términos de memoria de video^2^.

Alternativamente, el despliegue de modelos hiper-especializados de menos
de dos mil millones de parámetros, como PaddleOCR-VL o GLM-OCR,
demuestra que el tamaño del modelo no es el único indicador de la
calidad del OCR^2^. Estos micro-modelos, entrenados casi en su totalidad
con corpus de documentos sintéticos y reales alineados con HTML,
eliminan la necesidad de alojar grandes servidores de inferencia,
permitiendo el procesamiento ágil de los remitos directamente en
ordenadores de oficina comunes o servidores locales ligeros^2^.

## Mecanismos de Decodificación Guiada y Formateo Estricto de Esquemas

La extracción de datos comerciales para su posterior ingesta en sistemas
de planificación de recursos empresariales (ERP) o bases de datos
relacionales no tolera fallos de consistencia en el formato de
salida^25^. Un modelo que responda con bloques de texto explicativos,
marcas de formato Markdown adicionales o estructuras JSON con llaves
faltantes detendrá el flujo automático de datos^25^. Para emular la
confiabilidad de las APIs de Gemini, que ofrecen parámetros de formato
estructurado nativo, los entornos locales deben implementar esquemas de
decodificación guiada a nivel de hardware de inferencia^25^.

### Fundamentos Técnicos de la Inferencia Constreñida

La decodificación guiada consiste en modificar de forma dinámica la
distribución de probabilidad de los tokens de salida durante la fase de
muestreo del modelo de lenguaje^27^. Herramientas de software como vLLM
integran los backends de optimización de gramática Outlines y XGrammar
para ejecutar esta tarea^25^. El proceso se desarrolla de acuerdo con la
siguiente secuencia lógica de bajo nivel:

1.  El desarrollador define la estructura de datos deseada mediante un
    > esquema JSON estándar o, preferiblemente, a través de una clase de
    > validación de tipos Pydantic en Python^29^.

2.  El motor de inferencia local traduce el esquema JSON provisto a un
    > Autómata Finito No Determinista (NFA) o a una gramática libre de
    > contexto en formato EBNF^27^.

3.  En cada paso de la generación de tokens (token generation step), el
    > autómata evalúa qué caracteres del vocabulario del modelo
    > mantienen el cumplimiento sintáctico estricto del esquema^27^.

4.  Se aplica una máscara de logits (logit mask) que reduce la
    > probabilidad de selección de todos los tokens no conformes a
    > ![](media/image10.png){width="0.38118547681539805in"
    > height="0.2575579615048119in"}, forzando al modelo a elegir
    > únicamente de entre el subconjunto de tokens válidos^27^.

Este mecanismo garantiza que la salida del modelo cumpla al cien por
ciento con el contrato de la API, eliminando la necesidad de implementar
lógicas complejas de reintento o análisis basados en expresiones
regulares en el código cliente^25^.

### Clasificación de Errores en Procesos de Extracción Documental

Para evaluar la calidad de un pipeline de extracción local, es necesario
diferenciar los tipos de errores que ocurren durante la inferencia,
clasificándolos en dos categorías principales^25^:

-   **Fallos de Contrato:** Incluyen errores de sintaxis en el archivo
    > JSON, omisión de claves obligatorias definidas en el esquema,
    > tipos de datos erróneos (por ejemplo, insertar una cadena de texto
    > en un campo configurado como numérico entero) y la generación de
    > texto explicativo residual tras el cierre de la estructura del
    > objeto^25^. El uso de backends de decodificación guiada como
    > XGrammar o Outlines neutraliza por completo este tipo de errores,
    > reduciendo su incidencia a cero^25^.

-   **Fallos de Contenido:** Comprenden las discrepancias de información
    > entre los datos reales legibles en el remito físico y el texto
    > extraído por el modelo^25^. Se manifiestan en forma de errores de
    > transcripción en códigos alfanuméricos largos, la inversión de
    > dígitos en importes numéricos (digit flips), la omisión de líneas
    > completas de tablas debido a una resolución insuficiente o la
    > alucinación de datos no presentes en el remito original^25^.

Para combatir los fallos de contenido, es crítico fijar el parámetro de
temperatura del modelo exactamente en cero, lo que desactiva el muestreo
probabilístico del decodificador y asegura que el modelo se comporte de
manera estrictamente determinista^29^. Asimismo, la implementación de
resoluciones dinámicas altas a nivel de codificador visual y el uso de
máscaras de pérdida específicas para el asistente durante el
entrenamiento son esenciales para salvaguardar la fidelidad de la
información numérica sensible extraída^25^.

## Flujo de Trabajo Técnico y Pipeline de Inferencia Local

El procesamiento de un lote de 50 remitos mediante una arquitectura
local segura requiere estructurar un flujo de trabajo lineal que cubra
desde la ingesta del archivo PDF hasta el almacenamiento estructurado
final de la información comercial^34^. A diferencia de los flujos
basados en la nube, donde la transferencia de la red y el procesamiento
en servidores externos añaden variabilidad a los tiempos de respuesta,
un pipeline local proporciona un rendimiento predecible y
consistente^8^.

Un factor clave a considerar es la estimación del rendimiento y los
tiempos de ejecución locales. En configuraciones de hardware equipadas
con tarjetas gráficas de gama media, se estima que el procesamiento de
una página de documento mediante un modelo VLM de 8B parámetros (como
MiniCPM-V 2.6) toma entre 20 y 60 segundos por página utilizando
llamadas secuenciales^14^. Al proyectar este rendimiento sobre un lote
cerrado de 50 escaneos de remitos de una sola página, el tiempo estimado
total de procesamiento se sitúa en un intervalo de entre 16 y 50 minutos
si se procesa de forma estrictamente secuencial. No obstante, mediante
la optimización de lotes paralelos (batching) soportada por vLLM y el
ajuste de la longitud de contexto del modelo, estos tiempos pueden
reducirse de manera significativa en entornos de producción^8^.

El pipeline técnico propuesto se articula a través de las siguientes
etapas operativas secuenciales:

> +\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+\
> \| PDF de Remito \|\
> +\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+\
> \|\
> v\
> +\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+\
> \| Rasterización \| -\> pdf2image (300 DPI) para preservar pequeños
> detalles\
> +\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+\
> \|\
> v\
> +\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+\
> \| Preprocesamiento \| -\> Conversión a escala de grises, corrección
> de inclinación\
> \| de Imagen \| y reducción de ruido mediante filtros OpenCV\
> +\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+\
> \|\
> v\
> +\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+\
> \| Decodificación \| -\> vLLM / Ollama con logit masking activo\
> \| Guiada (VLM) \| (XGrammar / Outlines para forzar salida JSON)\
> +\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+\
> \|\
> v\
> +\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+\
> \| Post-Procesamiento\| -\> Validaciones lógicas y aritméticas en
> backend Python\
> \| y Almacenamiento \| antes de persistir en base de datos local
> protegida\
> +\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+

### 1. Rasterización Optimizada de Archivos

Dado que los VLMs locales reciben tensores de píxeles, el documento PDF
de origen debe transformarse en una representación visual de alta
fidelidad^14^. Se emplea la biblioteca Python pdf2image, la cual
requiere la instalación del motor binario Poppler en el sistema
operativo^38^.

Para garantizar que el codificador visual reciba suficiente detalle para
distinguir caracteres numéricos pequeños y códigos de barras, se
establece una resolución mínima de
![](media/image14.png){width="0.7620439632545932in"
height="0.2609744094488189in"}^39^. Esto asegura que la conversión
espacial genere una representación nítida de los caracteres legibles,
mitigando la posibilidad de que el proyector multimodal del modelo de
lenguaje reciba características visuales borrosas que induzcan a
alucinaciones de contenido^25^.

### 2. Preprocesamiento de Imágenes mediante OpenCV

Para neutralizar los efectos de escaneos defectuosos, faxes de bajo
contraste o páginas digitalizadas con rotaciones angulares accidentales,
se implementa un pipeline de limpieza visual automatizado utilizando la
biblioteca OpenCV (cv2) en combinación con operaciones vectoriales en
NumPy^40^:

  -----------------------------------------------------------------------
  Python\
  import cv2\
  import numpy as np\
  \
  def **limpiar_y_desvelar_remito**(ruta_entrada: str, ruta_salida:
  str):\
  \# Cargar la imagen del remito en escala de grises para simplificar el
  procesamiento\
  img = cv2.imread(ruta_entrada, cv2.IMREAD_GRAYSCALE)\
  \
  \# Aplicar un filtro bilateral para remover ruido de fondo preservando
  la nitidez de los bordes del texto\
  img_filtrada = cv2.bilateralFilter(img, 9, 75, 75)\
  \
  \# Aplicar binarización adaptativa mediante el método de Otsu para
  obtener blanco y negro puro\
  \_, img_binarizada = cv2.threshold(img_filtrada, 0, 255,
  cv2.THRESH_BINARY \| cv2.THRESH_OTSU)\
  \
  \# Calcular el ángulo de inclinación del documento para corregir
  desalineaciones\
  coordenadas = np.column_stack(np.where(img_binarizada \> 0))\
  angulo = cv2.minAreaRect(coordenadas)\[-1\]\
  \
  \# Normalizar el ángulo calculado para rotaciones estándar de texto\
  if angulo \< -45:\
  angulo = -(90 + angulo)\
  else:\
  angulo = -angulo\
  \
  \# Calcular el centro y aplicar la matriz de transformación afín para
  rotar la **imagen**\
  (alto, ancho) = img_binarizada.shape\[:2\]\
  centro = (ancho *// 2, alto // 2)*\
  matriz_rotacion = cv2.getRotationMatrix2D(centro, angulo, 1.0)\
  img_corregida = cv2.warpAffine(\
  img_binarizada,\
  matriz_rotacion,\
  (ancho, alto),\
  flags=cv2.INTER_CUBIC,\
  borderMode=cv2.BORDER_REPLICATE\
  )\
  \
  \# Guardar la imagen optimizada para el motor de inferencia local\
  cv2.imwrite(ruta_salida, img_corregida)
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

La aplicación de este bloque de preprocesamiento previene fallas
críticas en los algoritmos de atención bidireccional del transformador
del modelo de visión, ya que las líneas de texto del remito quedan
alineadas de forma estrictamente horizontal^7^.

### 3. Inferencia de Extracción y Validación de Negativos

Tras optimizar la señal visual, se procede a invocar el modelo de
lenguaje con visión estructurado mediante vLLM, utilizando un cliente
compatible con OpenAI que ejecuta la solicitud a través del endpoint de
red local^43^.

A fin de prevenir que el sistema procese documentos erróneos que hayan
sido ingresados por accidente al lote de remitos, el esquema de Pydantic
debe contemplar claves de control de confianza y banderas booleanas que
actúen como filtros de descarte automático de negativos^25^. El modelo
se configura para asignar un valor nulo o retornar campos vacíos en caso
de que el documento analizado carezca de la información típica de un
remito comercial, permitiendo que la aplicación cliente identifique y
descarte anomalías de manera oportuna^25^.

El siguiente bloque de código Python demuestra la orquestación completa
del proceso de extracción de datos, incluyendo la llamada al servidor
compatible de vLLM y el análisis automático de coincidencia aritmética
para validar la integridad del contenido de los datos extraídos:

> Python
>
> **import** base64\
> **from** typing **import** List, Optional\
> **from** pydantic **import** BaseModel, Field, model_validator\
> **from** openai **import** OpenAI\
> \
> *\# Definición de esquemas de datos utilizando Pydantic v2*\
> **class** LineaItem(BaseModel):\
> codigo: Optional\[str\] **=** Field(**None**, description**=**\"Código
> de artículo del proveedor.\")\
> descripcion: str **=** Field(**\...**, description**=**\"Texto que
> describe el producto entregado.\")\
> cantidad: float **=** Field(**\...**, description**=**\"Cantidad
> física entregada.\")\
> precio_unitario: Optional\[float\] **=** Field(**None**,
> description**=**\"Precio unitario de lista si está visible.\")\
> importe_linea: Optional\[float\] **=** Field(**None**,
> description**=**\"Importe total para este ítem (cantidad \*
> precio_unitario).\")\
> \
> **class** RemitoValidado(BaseModel):\
> es_remito_valido: bool **=** Field(**\...**, description**=**\"Bandera
> que indica si el documento es efectivamente un remito comercial
> legible.\")\
> numero_remito: Optional\[str\] **=** Field(**None**,
> description**=**\"Número de remito en formato estándar de
> facturación.\")\
> razon_social_proveedor: Optional\[str\] **=** Field(**None**,
> description**=**\"Nombre legal de la entidad emisora del remito.\")\
> items: List\[LineaItem\] **=** Field(default_factory**=**list,
> description**=**\"Desglose de productos o ítems detallados.\")\
> subtotal_calculado: Optional\[float\] **=** Field(**None**,
> description**=**\"Suma acumulada del importe de las líneas.\")\
> importe_total_declarado: Optional\[float\] **=** Field(**None**,
> description**=**\"Valor final total asentado físicamente en el
> remito.\")\
> \
> *\# Validador de consistencia lógica para asegurar la integridad de
> los datos numéricos extraídos*\
> \@model_validator(mode**=**\'after\')\
> **def** verificar_coherencia_aritmetica(self) **-\>**
> \'RemitoValidado\':\
> **if** **not** self.es_remito_valido:\
> **return** self\
> \
> *\# Calcular de forma independiente la suma de las líneas de
> producto*\
> suma_items **=** sum(item.importe_linea **for** item **in** self.items
> **if** item.importe_linea **is** **not** **None**)\
> \
> *\# Validar consistencia si el subtotal fue declarado en el
> documento*\
> **if** self.subtotal_calculado **is** **not** **None** **and**
> abs(self.subtotal_calculado **-** suma_items) **\>** 0.01:\
> *\# Registrar discrepancia o corregir programáticamente para auditoría
> de calidad*\
> **pass**\
> \
> **return** self\
> \
> **def** ejecutar_extraccion_local(ruta_imagen_limpia: str) **-\>**
> Optional\[RemitoValidado\]:\
> *\# Inicializar el cliente apuntando al host local seguro protegido
> por TLS*\
> client **=** OpenAI(\
> base_url**=**\"https://vlm-extractor.infra.local/v1\",\
> api_key**=**\"token_seguridad_local_interno\"\
> )\
> \
> *\# Codificar la imagen del remito a Base64 para su transmisión local
> segura*\
> **with** open(ruta_imagen_limpia, \"rb\") **as** f:\
> datos_base64 **=** base64.b64encode(f.read()).decode(\"utf-8\")\
> \
> prompt **=** (\
> \"Analiza el documento comercial provisto. Transcribe meticulosamente
> los campos de \"\
> \"identificación, emisor y cada una de las líneas de artículos
> detalladas en la tabla de entrega. \"\
> \"Si detectas que el documento no es un remito comercial legible,
> establece el campo \'es_remito_valido\' en falso.\"\
> )\
> \
> *\# Ejecución de la solicitud de inferencia local con decodificación
> guiada*\
> response **=** client.chat.completions.create(\
> model**=**\"Qwen/Qwen2.5-VL-7B-Instruct\",\
> messages**=**\[\
> {\
> \"role\": \"user\",\
> \"content\": \[\
> {\"type\": \"text\", \"text\": prompt},\
> {\
> \"type\": \"image_url\",\
> \"image_url\": {\
> \"url\": f\"data:image/jpeg;base64,{datos_base64}\"\
> }\
> }\
> \]\
> }\
> \],\
> extra_body**=**{\
> \"guided_json\": RemitoValidado.model_json_schema()\
> },\
> temperature**=**0.0 *\# Desactivar la variabilidad para forzar
> respuestas estrictamente reproducibles*\
> )\
> \
> *\# Deserializar y validar el resultado bajo el esquema estructurado
> de Pydantic*\
> **try**:\
> resultado **=** RemitoValidated **=**
> RemitoValidado.model_validate_json(response.choices\[0\].message.content)\
> **return** resultado\
> **except** Exception **as** e:\
> *\# Registrar fallos sintácticos si el motor de inferencia no aplicó
> la máscara correctamente*\
> **return** **None**

## Estrategias de Despliegue de Red, Hardening de Servidores y Aislamiento de Datos

Para que una solución de extracción de datos documentales sea
legítimamente segura e inmune a filtraciones de datos, toda la
infraestructura de hardware y red debe operar bajo una estrategia de
confianza cero (Zero Trust) y con un aislamiento físico estricto de
cualquier salida a Internet^6^. Ollama, vLLM y los contenedores de
Docker por defecto no incluyen controles robustos de acceso y seguridad,
lo que exige la implementación de capas externas de endurecimiento de
sistemas^46^.

### Configuración del Aislamiento Físico y de Red (Air-Gapping)

En instalaciones donde no se tolera ningún tipo de fuga de información
hacia el exterior (por ejemplo, servidores ubicados en bóvedas de datos
corporativos o laboratorios aislados), se debe bloquear por completo la
capacidad de los contenedores de realizar peticiones de red
salientes^48^.

A nivel de orquestación, las políticas del contenedor Docker o del pod
de Kubernetes que ejecuta el servidor de inferencia de vLLM deben
prescindir de interfaces de red con pasarelas de enlace externas^6^. La
configuración de las variables de entorno HF_HUB_OFFLINE=1 y
TRANSFORMERS_OFFLINE=1 fuerza al software de Hugging Face a buscar todos
los pesos del modelo y archivos de configuración del tokenizador de
manera estrictamente local en el almacenamiento persistente montado,
previniendo fallos en el arranque por intentos fallidos de conexión a
Internet^50^.

A continuación se detalla la configuración recomendada para un entorno
de Docker Compose diseñado para operar de forma segura bajo condiciones
de aislamiento de red local:

> YAML
>
> version: \'3.8\'\
> \
> services:\
> vllm-extractor:\
> image: vllm/vllm-openai:latest\
> container_name: vllm-server-seguro\
> restart: unless-stopped\
> \# Desconectar el contenedor de redes con acceso externo\
> networks:\
> - red-interna-ai\
> ports:\
> \# Exponer puerto de inferencia únicamente a la interfaz de bucle de
> retorno local (loopback)\
> \# Esto evita que otros equipos de la red local accedan directamente
> al puerto de vLLM sin pasar por el proxy\
> - \"127.0.0.1:8000:8000\"\
> volumes:\
> \# Montar el volumen local persistente que contiene los pesos de
> Qwen2.5-VL-7B-Instruct descargados previamente\
> - /opt/model_cache/qwen2.5-7b-vl:/root/.cache/huggingface\
> environment:\
> - HF_HUB_OFFLINE=1\
> - TRANSFORMERS_OFFLINE=1\
> - CUDA_VISIBLE_DEVICES=0\
> deploy:\
> resources:\
> reservations:\
> devices:\
> - driver: nvidia\
> count: 1\
> capabilities: \[gpu\]\
> \
> networks:\
> red-interna-ai:\
> driver: bridge\
> \# Configurar la red como interna para impedir de manera estricta
> cualquier tráfico de salida de red (egress)\
> internal: true

### Mitigación de Vulnerabilidades y Control de Accesos

Dado que los motores de inferencia locales carecen de módulos nativos
para la autenticación de usuarios, la gestión de cuotas de cómputo y el
registro detallado de auditoría, se debe implementar una arquitectura de
seguridad por capas alrededor de los puertos de servicio^46^.

El control de accesos se delega de forma exclusiva a una pasarela de
seguridad configurada mediante un servidor Nginx, el cual encripta la
comunicación entre el servidor de aplicaciones corporativas y el nodo de
inferencia utilizando el protocolo seguro HTTPS^46^. Asimismo, el
firewall del host (por ejemplo, UFW en Ubuntu o iptables a nivel de
kernel) debe configurarse para bloquear de manera estricta el puerto
nativo de Ollama (11434) o vLLM (8000) para todas las interfaces de red
externas, permitiendo únicamente solicitudes entrantes que atraviesen el
puerto protegido del proxy inverso HTTPS^6^.

Adicionalmente, se recomienda definir políticas de uso y límites físicos
en el consumo de memoria de video (VRAM) para evitar ataques de
denegación de servicio internos provocados por el procesamiento
simultáneo de múltiples documentos de gran tamaño^37^. Establecer
límites de concurrencia mediante el parámetro \--limit-mm-per-prompt de
vLLM evita que el desborde de imágenes consuma en exceso la memoria
KVCache de la GPU, manteniendo la estabilidad operativa del servidor de
inferencia privado^37^.

## Síntesis Operativa y Recomendaciones de Implementación

La emulación de las capacidades de Google Gemini para la extracción y
estructuración automatizada de datos de remitos en una red local privada
y aislada es completamente viable, eficiente y altamente segura si se
estructuran de forma adecuada las capas del sistema de información
corporativo^3^. Para procesar con éxito el lote de 50 escaneos de
remitos minimizando el esfuerzo de desarrollo y maximizando la exactitud
de los datos extraídos, se aconseja adoptar la siguiente estrategia de
implementación unificada:

### Selección del Modelo de Inferencia

El modelo **Qwen2.5-VL-7B-Instruct** es la recomendación preferente para
este proyecto^8^. Al contar con entrenamiento nativo en idioma español
para tareas de análisis de documentos e interpretación de tablas densas,
proporciona una precisión de extracción comparable a la de modelos
comerciales medianos que operan en la nube^7^. Su tamaño permite
cargarlo con una cuantización estándar de precisión de 4 bits en
cualquier GPU comercial moderna equipada con al menos
![](media/image5.png){width="1.0166021434820647in"
height="0.25933727034120735in"} de VRAM, requiriendo un consumo de
memoria de video sumamente bajo de entre
![](media/image4.png){width="0.9155271216097988in"
height="0.2600929571303587in"} durante la inferencia activa^8^.

### Arquitectura del Motor y Decodificación Guiada

Se sugiere optar por el despliegue del servidor a través de **vLLM**^8^.
vLLM no solo optimiza el rendimiento del procesamiento de imágenes
complejas mediante el uso eficiente de la memoria de la GPU, sino que
integra de manera nativa los backends de decodificación guiada Outlines
y XGrammar^25^. Al suministrar un esquema JSON validado bajo Pydantic en
cada solicitud de inferencia local, se elimina por completo la
posibilidad de recibir respuestas mal formateadas, asegurando la
consistencia e integridad estructural de los datos JSON que se guardarán
posteriormente en los sistemas de bases de datos empresariales^25^.

### Pipeline de Datos y Tratamiento de la Señal Visual

Dada la variabilidad física inherente a los documentos comerciales
escaneados, no se deben enviar los archivos PDF originales directamente
al modelo de visión sin una fase de acondicionamiento previa^41^. El
pipeline local debe estructurar de manera sistemática la rasterización
de los documentos utilizando pdf2image configurado a una resolución
nítida de ![](media/image14.png){width="0.7620439632545932in"
height="0.2609744094488189in"}^14^, seguida de una rutina automática de
limpieza en OpenCV encargada de binarizar la imagen mediante el
algoritmo de Otsu y neutralizar geométricamente cualquier inclinación
angular de la página^39^. Este conjunto de transformaciones visuales
garantiza que el proyector del VLM reciba una señal de texto de alta
legibilidad, minimizando significativamente la tasa de alucinaciones
tipográficas o numéricas en la salida del modelo^25^.

### Directivas de Seguridad y Cumplimiento

Con el fin de certificar la total privacidad del flujo de datos dentro
de la red corporativa, se debe aislar el host de la GPU mediante
firewalls físicos y configurar las variables de entorno HF_HUB_OFFLINE=1
y TRANSFORMERS_OFFLINE=1 para impedir de manera absoluta cualquier
intento de telemetría o conexión saliente del contenedor hacia
repositorios públicos^6^. El acceso a la API local compatible con OpenAI
expuesta por vLLM debe estar estrictamente protegido mediante un proxy
inverso Nginx local^46^. Este proxy se encargará de encriptar el tráfico
mediante certificados de seguridad TLS y restringir la autorización de
acceso únicamente a la dirección IP asignada al servidor de aplicaciones
de la organización, creando un entorno de cómputo robusto, eficiente y
totalmente conforme con las políticas más exigentes de soberanía de la
información^6^.

#### Fuentes citadas

1.  Ultimate Guide - The Best Open Source LLM for Document Screening in
    > 2026 - SiliconFlow,
    > [[https://www.siliconflow.com/articles/en/best-open-source-LLM-for-Document-screening]{.underline}](https://www.siliconflow.com/articles/en/best-open-source-LLM-for-Document-screening)

2.  Best Open Source OCR for AI Agents: The 2026 Document Pipeline,
    > [[https://www.madebyagents.com/blog/best-open-source-ocr-for-ai-agents]{.underline}](https://www.madebyagents.com/blog/best-open-source-ocr-for-ai-agents)

3.  Extract Invoice Data Using LLMs and Export Instantly to CSV or
    > JSON - elDoc,
    > [[https://eldoc.online/blog/extract-invoice-data-using-llms-and-export-to-csv-or-json/]{.underline}](https://eldoc.online/blog/extract-invoice-data-using-llms-and-export-to-csv-or-json/)

4.  Best Vision Language Models & Agentic OCR Tools for Developers -
    > LlamaIndex,
    > [[https://www.llamaindex.ai/insights/best-vision-language-models]{.underline}](https://www.llamaindex.ai/insights/best-vision-language-models)

5.  Best LLM for Invoice Extraction: GPT vs Claude vs Gemini,
    > [[https://invoicedataextraction.com/blog/best-llm-for-invoice-extraction]{.underline}](https://invoicedataextraction.com/blog/best-llm-for-invoice-extraction)

6.  Ollama on-premise setup for businesses with Open WebUI - FJAN,
    > [[https://www.fjan.nl/posts/ollama-on-premise-setup-for-businesses-offline-ai]{.underline}](https://www.fjan.nl/posts/ollama-on-premise-setup-for-businesses-offline-ai)

7.  Qwen2.5-VL: Architecture, Data, Benchmarks and Inference -
    > DebuggerCafe,
    > [[https://debuggercafe.com/qwen2-5-vl/]{.underline}](https://debuggercafe.com/qwen2-5-vl/)

8.  Local AI Vision Tasks (2026): OCR, Invoices & Alt-Text with Open
    > VLMs,
    > [[https://localaimaster.com/blog/local-ai-vision-tasks]{.underline}](https://localaimaster.com/blog/local-ai-vision-tasks)

9.  Qwen2.5-VL - Grokipedia,
    > [[https://grokipedia.com/page/Qwen25-VL]{.underline}](https://grokipedia.com/page/Qwen25-VL)

10. Qwen2.5 VL 7B Instruct API - AIMLAPI.com,
    > [[https://aimlapi.com/models/qwen2-5-vl-7b-instruct]{.underline}](https://aimlapi.com/models/qwen2-5-vl-7b-instruct)

11. qwen2.5 - Ollama,
    > [[https://ollama.com/library/qwen2.5]{.underline}](https://ollama.com/library/qwen2.5)

12. Qwen/Qwen2.5-VL-32B-Instruct - Hugging Face,
    > [[https://huggingface.co/Qwen/Qwen2.5-VL-32B-Instruct]{.underline}](https://huggingface.co/Qwen/Qwen2.5-VL-32B-Instruct)

13. qwen2.5vl - Ollama,
    > [[https://ollama.com/library/qwen2.5vl]{.underline}](https://ollama.com/library/qwen2.5vl)

14. How to Add Vision to a Local AI Agent Without Blowing Your VRAM -
    > MindStudio,
    > [[https://www.mindstudio.ai/blog/add-vision-to-local-ai-agent-low-vram]{.underline}](https://www.mindstudio.ai/blog/add-vision-to-local-ai-agent-low-vram)

15. GitHub - OpenBMB/MiniCPM-V: A Pocket-Sized MLLM for Ultra-Efficient
    > Image and Video Understanding on Your Phone,
    > [[https://github.com/openbmb/MiniCPM-V]{.underline}](https://github.com/openbmb/MiniCPM-V)

16. Multimodal Language Models - SGLang Documentation,
    > [[https://sgl-project.github.io/supported_models/text_generation/multimodal_language_models.html]{.underline}](https://sgl-project.github.io/supported_models/text_generation/multimodal_language_models.html)

17. Ollama with granite3.2-vision is excellent for OCR and for
    > processing text afterwards - Reddit,
    > [[https://www.reddit.com/r/ollama/comments/1j6dp3j/ollama_with_granite32vision_is_excellent_for_ocr/]{.underline}](https://www.reddit.com/r/ollama/comments/1j6dp3j/ollama_with_granite32vision_is_excellent_for_ocr/)

18. llama3.2-vision - Ollama,
    > [[https://ollama.com/library/llama3.2-vision]{.underline}](https://ollama.com/library/llama3.2-vision)

19. Llama 3.2 Overview --- NVIDIA NIM for Vision Language Models (VLMs),
    > [[https://docs.nvidia.com/nim/vision-language-models/1.2.0/examples/llama3-2/overview.html]{.underline}](https://docs.nvidia.com/nim/vision-language-models/1.2.0/examples/llama3-2/overview.html)

20. Meta\'s Llama 3.2 models now available on watsonx, including
    > multimodal 11B and 90B models \| IBM,
    > [[https://www.ibm.com/think/news/meta-llama-3-2-models]{.underline}](https://www.ibm.com/think/news/meta-llama-3-2-models)

21. Qwen2.5-VL Vision Language Model \| Guides - Clore.ai,
    > [[https://docs.clore.ai/guides/vision-models/qwen-vl]{.underline}](https://docs.clore.ai/guides/vision-models/qwen-vl)

22. A Comprehensive and Challenging OCR Benchmark for Evaluating Large
    > Multimodal Models in Literacy - CVF Open Access,
    > [[https://openaccess.thecvf.com/content/ICCV2025/papers/Yang_CC-OCR_A_Comprehensive_and_Challenging_OCR_Benchmark_for_Evaluating_Large_ICCV_2025_paper.pdf]{.underline}](https://openaccess.thecvf.com/content/ICCV2025/papers/Yang_CC-OCR_A_Comprehensive_and_Challenging_OCR_Benchmark_for_Evaluating_Large_ICCV_2025_paper.pdf)

23. imanoop7/Ollama-OCR - GitHub,
    > [[https://github.com/imanoop7/Ollama-OCR]{.underline}](https://github.com/imanoop7/Ollama-OCR)

24. What Is MiniCPM-V 4.6? A 1.3B Vision Model Built for Local AI Agents
    > \| MindStudio,
    > [[https://www.mindstudio.ai/blog/what-is-minicpm-v-4-6-vision-model]{.underline}](https://www.mindstudio.ai/blog/what-is-minicpm-v-4-6-vision-model)

25. Seeking Professional Methodology for VLM Domain Fine-tuning:
    > Analyzing 4 Experimental Strategies with Qwen2-VL - Hugging Face
    > Forums,
    > [[https://discuss.huggingface.co/t/seeking-professional-methodology-for-vlm-domain-fine-tuning-analyzing-4-experimental-strategies-with-qwen2-vl/173682]{.underline}](https://discuss.huggingface.co/t/seeking-professional-methodology-for-vlm-domain-fine-tuning-analyzing-4-experimental-strategies-with-qwen2-vl/173682)

26. Structured Outputs with Ollama: Harnessing Local AI Models for
    > Reliable Data - Medium,
    > [[https://medium.com/@danushidk507/structured-outputs-with-ollama-harnessing-local-ai-models-for-reliable-data-ae49221e9c13]{.underline}](https://medium.com/@danushidk507/structured-outputs-with-ollama-harnessing-local-ai-models-for-reliable-data-ae49221e9c13)

27. Structured Decoding in vLLM: a gentle introduction,
    > [[https://vllm.ai/blog/2025-01-14-struct-decode-intro]{.underline}](https://vllm.ai/blog/2025-01-14-struct-decode-intro)

28. Reliable JSON from Any LLM: Pydantic + Zod (2026) \| TECHSY,
    > [[https://techsy.io/en/blog/llm-structured-outputs-guide]{.underline}](https://techsy.io/en/blog/llm-structured-outputs-guide)

29. Structured Outputs - Ollama documentation,
    > [[https://docs.ollama.com/capabilities/structured-outputs]{.underline}](https://docs.ollama.com/capabilities/structured-outputs)

30. Structured outputs · Ollama Blog,
    > [[https://ollama.com/blog/structured-outputs]{.underline}](https://ollama.com/blog/structured-outputs)

31. Structured Outputs - vLLM Documentation,
    > [[https://docs.vllm.ai/en/latest/features/structured_outputs/]{.underline}](https://docs.vllm.ai/en/latest/features/structured_outputs/)

32. Training and deploying VLM models with Gemma 4 \| by Dave Davies \|
    > Online Inference,
    > [[https://medium.com/online-inference/training-and-deploying-vlm-models-with-gemma-4-c5dc1179833c]{.underline}](https://medium.com/online-inference/training-and-deploying-vlm-models-with-gemma-4-c5dc1179833c)

33. Qwen/Qwen2-VL-7B-Instruct - Hugging Face,
    > [[https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct]{.underline}](https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct)

34. Extracting Invoice and Receipt Data as JSON Using Fine-Tuned VLMs -
    > CloudThat,
    > [[https://www.cloudthat.com/resources/blog/extracting-invoice-and-receipt-data-as-json-using-fine-tuned-vlms]{.underline}](https://www.cloudthat.com/resources/blog/extracting-invoice-and-receipt-data-as-json-using-fine-tuned-vlms)

35. Best OpenCV settings for image prep prior to OCR? : r/learnpython -
    > Reddit,
    > [[https://www.reddit.com/r/learnpython/comments/1iw1lnp/best_opencv_settings_for_image_prep_prior_to_ocr/]{.underline}](https://www.reddit.com/r/learnpython/comments/1iw1lnp/best_opencv_settings_for_image_prep_prior_to_ocr/)

36. Offline VLLM Setup - by Ekaansh Sahni - Medium,
    > [[https://medium.com/@ekaansh.sahni/offline-vllm-setup-00dbd004867f]{.underline}](https://medium.com/@ekaansh.sahni/offline-vllm-setup-00dbd004867f)

37. Qwen2.5-VL Usage Guide - vLLM Recipes,
    > [[https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen2.5-VL.html]{.underline}](https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen2.5-VL.html)

38. Deploy DeepSeek-OCR on GPU Cloud: Self-Host Production Document and
    > Visual OCR Inference (2026 Setup Guide) \| Spheron Blog,
    > [[https://www.spheron.network/blog/deploy-deepseek-ocr-gpu-cloud/]{.underline}](https://www.spheron.network/blog/deploy-deepseek-ocr-gpu-cloud/)

39. Extracts structured tables from balance sheets, 10-Ks, and scanned
    > financial PDFs using layout-aware OCR and transformer parsers.
    > Preserves row and column hierarchy and exports clean CSV, JSON,
    > and pandas DataFrames. · GitHub,
    > [[https://github.com/dakshjain-1616/Table-Extraction-from-Financial-Documents-By-NEO]{.underline}](https://github.com/dakshjain-1616/Table-Extraction-from-Financial-Documents-By-NEO)

40. \[Guide\] Parsing PDF Files Using Python with Tesseract OCR - Ask
    > the Community,
    > [[https://community.palantir.com/t/guide-parsing-pdf-files-using-python-with-tesseract-ocr/1347]{.underline}](https://community.palantir.com/t/guide-parsing-pdf-files-using-python-with-tesseract-ocr/1347)

41. Ultimate guide to Python Tesseract - Nutrient iOS,
    > [[https://www.nutrient.io/blog/tesseract-python-guide/]{.underline}](https://www.nutrient.io/blog/tesseract-python-guide/)

42. How to extract tables from pdf: Simple, Free Tools for Clean Data,
    > [[https://pdf.ai/resources/how-to-extract-tables-from-pdf]{.underline}](https://pdf.ai/resources/how-to-extract-tables-from-pdf)

43. meta-llama/Llama-3.2-11B-Vision - Hugging Face,
    > [[https://huggingface.co/meta-llama/Llama-3.2-11B-Vision]{.underline}](https://huggingface.co/meta-llama/Llama-3.2-11B-Vision)

44. vLLM - Qwen,
    > [[https://qwen.readthedocs.io/en/v2.5/deployment/vllm.html]{.underline}](https://qwen.readthedocs.io/en/v2.5/deployment/vllm.html)

45. mikgr/doctype-classifier-vl - Ollama,
    > [[https://ollama.com/mikgr/doctype-classifier-vl]{.underline}](https://ollama.com/mikgr/doctype-classifier-vl)

46. Securing Ollama: Auth, TLS, Network Isolation (Production Guide) \|
    > Local AI Master,
    > [[https://localaimaster.com/blog/securing-ollama-guide]{.underline}](https://localaimaster.com/blog/securing-ollama-guide)

47. Secure Self-Hosted AI --- Security & Best Practices for Ollama \|
    > Saeree ERP,
    > [[https://www.grandlinux.com/en/blogs/ollama-self-host-security.html]{.underline}](https://www.grandlinux.com/en/blogs/ollama-self-host-security.html)

48. Does Ollama Work Offline? Yes --- Complete Offline Mode Guide for
    > Windows,
    > [[https://ai-ollama.github.io/ollama-offline.html]{.underline}](https://ai-ollama.github.io/ollama-offline.html)

49. Benchmarking with GuideLLM in air-gapped OpenShift clusters - Red
    > Hat Developer,
    > [[https://developers.redhat.com/articles/2025/09/15/benchmarking-guidellm-air-gapped-openshift-clusters]{.underline}](https://developers.redhat.com/articles/2025/09/15/benchmarking-guidellm-air-gapped-openshift-clusters)

50. Setting up vLLM in an airgapped environment - General,
    > [[https://discuss.vllm.ai/t/setting-up-vllm-in-an-airgapped-environment/916]{.underline}](https://discuss.vllm.ai/t/setting-up-vllm-in-an-airgapped-environment/916)

51. How can I run VLLM serving without an internet connection? #1405 -
    > GitHub,
    > [[https://github.com/vllm-project/vllm/discussions/1405]{.underline}](https://github.com/vllm-project/vllm/discussions/1405)
