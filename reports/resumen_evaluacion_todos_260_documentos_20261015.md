# Evaluación de los 260 documentos indexados — 15/10/2026

## Resultado general

Se cubrieron los 260 documentos indexados con 670 preguntas. La evaluación se hizo en tres corridas históricas: 5 preguntas por documento para los primeros 50 documentos y 2 por documento para los otros 210, luego de reducir la carga para terminar el recorrido.

| Tramo | Documentos | Preguntas | Correctas | Parciales | Incorrectas | No verificables | Fuente objetivo citada | HTTP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1–20 | 20 | 100 | 49 (49,0 %) | 16 | 32 | 3 | 56/100 | 100/100 |
| 21–50 | 30 | 150 | 89 (59,3 %) | 16 | 41 | 4 | 133/150 | 150/150 |
| 51–260 | 210 | 420 | 279 (66,4 %) | 52 | 76 | 13 | 329/420 | 420/420 |
| **Total bruto** | **260** | **670** | **417 (62,2 %)** | **84** | **149** | **20** | **518/670 (77,3 %)** | **670/670** |

Los números brutos de este resumen no aplican correcciones humanas hechas después en conversaciones anteriores. El porcentaje combinado es un balance descriptivo, no una comparación controlada: cambió la cantidad de preguntas por documento y parte de las preguntas fue aprobada por una persona mientras que las demás fueron generadas automáticamente. El juez de calidad también es automático; sus etiquetas requieren validación humana antes de considerarlas verdad de referencia. La categoría «correcta» no llegó al objetivo de 85–90 %.

## Recuento provisional solicitado: las parciales cuentan como correctas

Moviendo todas las respuestas parciales a la categoría de correctas, el porcentaje ajustado queda así. Este recuento usa las etiquetas guardadas en los tres informes y no reemplaza las etiquetas automáticas originales.

| Tramo | Correctas originales | Parciales reclasificadas | Correctas provisionales | Preguntas | Porcentaje provisional |
|---|---:|---:|---:|---:|---:|
| 1–20 | 49 | 16 | 65 | 100 | 65.0 % |
| 21–50 | 89 | 16 | 105 | 150 | 70.0 % |
| 51–260 | 279 | 52 | 331 | 420 | 78.8 % |
| **Total** | **417** | **84** | **501** | **670** | **74.8 %** |

En la corrida reciente (documentos 51–260), el resultado provisional es **331/420 = 78,8 %**. En el acumulado de 260 documentos es **501/670 = 74,8 %**.

## Ejecución final (documentos 51–260)

- 420/420 solicitudes respondieron con HTTP 200, en tandas de 20 solicitudes simultáneas. No fueron 420 usuarios simultáneos.
- p50 de latencia: 29.959 ms; p95: 47.135 ms.
- La fuente esperada aparece en el campo `sources` de la respuesta: 329/420 (78,3 %); falta en 91. El evaluador no guarda los candidatos, el orden rerankeado ni los chunks finales enviados al LLM; este número no demuestra por sí solo que el retrieval haya fallado.
- Calidad automática: 279 correctas, 52 parciales, 76 incorrectas y 13 no verificables.
- Entre las 414 preguntas que el juez consideró respondibles según el contenido indexado: 279 correctas (67,4 %).
- 116/420 preguntas no contenían una palabra literal distintiva del título. Es una señal para revisar claridad de las preguntas y recuperación léxica; por sí sola no prueba que una pregunta sea inválida.
- Golden Cache: 260 operaciones de guardado/actualización durante esta corrida. La colección quedó con 977 casos. La promoción fue automática mediante el juez y validadores del caché; esos casos todavía no equivalen a una aprobación humana.

## Qué indican los errores

1. **Falta trazabilidad de recuperación:** la fuente esperada no aparece en `sources` de 91/420 respuestas. El reporte actual no registra candidatos, ranking, expansión ni chunks finales; primero hay que agregar esas trazas para distinguir fallo de búsqueda de falta de cita.
2. **La evidencia puede estar y aun así no usarse:** el juez detectó respuestas que se abstienen aunque el documento completo sí contiene los pasos, o que omiten pasos requeridos.
3. **Detalles añadidos sin respaldo:** varias respuestas agregan condiciones que el documento no menciona o contradicen una opción documentada.
4. **Servicio disponible con demora:** no hubo fallos HTTP en las 420 solicitudes de esta corrida, pero p95 de 47 segundos sigue siendo alto para una conversación.

## Plan de mejora general

1. Usar las 141 respuestas parciales, incorrectas o no verificables de la corrida final como conjunto de diagnóstico. Instrumentar cada consulta para registrar candidatos, scores, orden rerankeado, expansión, chunks finales y fuentes citadas; comparar esa traza con el documento completo.
2. Clasificar cada fallo por etapa: fuente ausente en candidatos, fuente perdida tras reranking/presupuesto, pregunta ambigua, respuesta que omite pasos, abstención innecesaria o dato no respaldado. Corregir la etapa que falle y volver a ejecutar las mismas preguntas como regresión.
3. Mejorar la recuperación escalable en documentos sin editar: consultas híbridas con términos de dominio y sinónimos, conservar el nombre/título como señal, recuperar chunks vecinos contiguos y admitir documentos complementarios cuando la pregunta necesite más de una fuente.
4. Ajustar el prompt para responder con todos los pasos sustentados y tono de ayuda, permitiendo inferencias sencillas que se desprenden del procedimiento, pero exigiendo que los datos operativos concretos estén respaldados por la evidencia. Si falta un dato crítico, indicar exactamente cuál y ofrecer el canal autorizado.
5. Auditar manualmente una muestra de los 260 casos promovidos/actualizados a Golden Cache. Mantener fuera del caché las etiquetas automáticas dudosas y usar las respuestas confirmadas como regresiones y ejemplos aprobados.
6. Reducir latencia midiendo por separado recuperación, reranking, expansión y generación; cualquier límite nuevo debe compararse contra la misma batería, no ajustarse con base solo en la puntuación del juez.

## Informes detallados

- [Preguntas, respuestas y evaluación de documentos 51–260 (JSON)](evaluacion_documentos_051-260_2q_20paralelo_20261015.json)
- [Preguntas, respuestas y evaluación de documentos 51–260 (Markdown)](evaluacion_documentos_051-260_2q_20paralelo_20261015.md)
- [Corrida de documentos 21–50 (JSON)](evaluacion_documentos_021-260_5q_50paralelo_20261015.json)
- [Corrida de documentos 1–20 (JSON)](indexed_docs_batch_001_001-020_5q_20261015.json)
