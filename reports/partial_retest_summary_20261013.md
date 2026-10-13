# Reporte de evaluación RAG y remediación — 13/10/2026

## Alcance real de la campaña por documentos

La campaña recorrió los **242 documentos indexados (7.307 chunks)** en orden y generó **2 preguntas por documento: 484 en total**. Se agruparon como pediste: **10 preguntas por cada grupo de 5 documentos**, para un total de 49 grupos; el último grupo contiene 2 documentos y 4 preguntas. Para las llamadas al chatbot, el ejecutor reunió hasta cinco grupos por tanda: 10 tandas en total, nueve de 50 preguntas y la última de 34. El detalle de preguntas y respuestas originales está en `indexed_documents_eval_20261006.md`.

## Línea base y segunda revisión

| Medición | Resultado |
|---|---:|
| Respuestas HTTP exitosas en la campaña inicial | 483/484; 1 error HTTP 500 |
| Fuente esperada entre fuentes finales | 381/484 (78,7 %) |
| Evaluación inicial del juez | 168 correctas, 185 parciales, 124 incorrectas, 7 no verificables (34,7 % correctas) |
| Latencia inicial | p50 54,7 s; p95 61,4 s |
| Revisión multi-evidencia de las 185 parciales | 127 correctas, 57 parciales, 0 incorrectas, 1 no verificable |
| Calidad combinada tras esa revisión | 295/484 correctas (61,0 %); incluye respuestas ya correctas más las 127 revaloradas |

La revisión multi-evidencia encontró que muchas respuestas parciales sí estaban respaldadas al leer juntos los chunks y páginas. Esa etapa fue una reevaluación automática con el juez `gpt-6-luna`, no una nueva consulta del usuario ni una ejecución completa del endpoint.

## Cambios aplicados y resultado medido

| Cambio general | Evidencia y efecto medido |
|---|---|
| Se corrigió la expansión del contexto del instructivo de Estudiantes Nuevos: el selector enviaba un `float` donde la expansión esperaba texto. | El caso que terminaba en HTTP 500 volvió a responder HTTP 200; la respuesta fue revisada con páginas complementarias y quedó correcta. |
| Se amplió la instrucción de respuesta para preservar la ruta completa, enumerar pasos/campos/filtros, respetar la acción y objeto exactos, separar trámites parecidos y no completar vacíos con instrucciones de otro sistema. | En la reejecución del grupo residual se evaluaron respuestas con todos los chunks finales, no solo con una cita; 51/58 casos del grupo residual están correctos tras los ajustes y la adjudicación descritos más abajo. |
| Se amplió la detección de procedimientos para reconocer verbos como modificar, exportar, llegar e incluir, y preguntas que piden conjuntos completos de datos/campos/filtros. | Prueba dirigida de 9 consultas: 5 correctas, 3 parciales y 1 incorrecta; las 9 incluyeron la fuente esperada. |
| Se quitó el falso positivo del filtro de cuenta que trataba cualquier consulta de «credenciales» como acceso a cuenta institucional. | Caso de credenciales de evaluación de selección: pasó a correcto; la fuente llegó al contexto. |
| Se cambió la detección de `pc` de subcadena a palabra completa. | «opción de pagos» ya no activa exclusión de hardware; caso de pagos pasó a correcto con su fuente. |
| Se robusteció la lectura JSON del juez y se separaron las políticas configuradas por la aplicación de las evidencias documentales. | La evaluación tolera texto sobrante del proveedor y no atribuye una política de la aplicación a un documento. |
| Se corrigió el flujo de retest para limpiar el veredicto previo heredado de cada respuesta base. | Un resultado anterior marcado parcial estaba impidiendo que el juez evaluara una respuesta nueva. Con el juicio actualizado, `doc0006-q1` pasó a correcto usando la respuesta y los chunks generados en el último retest. |
| Se endureció la promoción a Golden Cache. | Solo se guarda cuando el veredicto es correcto, la confianza es ≥0,98, no hay afirmaciones materiales sin respaldo, la fuente esperada está en el contexto y la evidencia original es válida. |
| Se corrigió la expansión contigua: ahora conserva los chunks de cada página adyacente con IDs y orden verificables, en lugar de dejar que un solo chunk de OCR desplace los demás. | En pruebas dirigidas, la página con el paso de autenticación llegó al contexto final para Reintegro; las verificaciones de expansión y presupuesto pasan. |
| El presupuesto prioriza chunks de la fuente cuyo título coincide con el tema escrito por el usuario, y limita a 4 las anclas de una fuente para dejar espacio a fuentes complementarias. | Prueba dirigida: el paso de autenticación permaneció dentro del presupuesto y la respuesta en vivo lo incluyó. Se confirmó también que sinónimos de MultiQuery ya no elevan manuales genéricos como fuentes preferidas por título. |

## Última prueba del grupo residual: 20 preguntas

Modelo generador y juez: `gpt-6-luna`. Se llamó directamente al servicio RAG para evitar que Golden Cache leyera una respuesta y ocultara el comportamiento actual; el juez recibió los chunks finales y las políticas institucionales por separado.

| Resultado | Cantidad |
|---|---:|
| Correctas en la reejecución original de estos 20 casos | 10/20 |
| Correctas tras los 3 retests dirigidos de acceso y su evaluación actualizada | 13/20 |
| Parciales después de esos ajustes | 7/20 |
| Incorrectas | 0/20 |
| Fuente esperada presente en contexto final | 18/20 |
| Guardadas en Golden Cache en la tanda original de 20 | 8 |
| Guardadas luego de retests dirigidos | 3 (incluye Reintegro, validado por el juez actualizado con evidencia final) |
| Golden Cache antes de la tanda de 20 → estado actual | 371 → 382 |

**Nota sobre la evaluación:** el primer resultado parcial de `doc0006-q1` correspondía a una respuesta anterior. El script estaba heredando ese veredicto y saltaba la evaluación de la nueva respuesta. Tras corregirlo, el juez recibió y marcó correcta la respuesta completa, respaldada por las páginas 2, 4, 5, 6 y 7. Los casos `doc0073-q1` y `doc0226-q1` también pasaron a correctos en retests dirigidos después de preservar las páginas vecinas.

### Resultado por pregunta

| ID | Documento esperado | Pregunta | Estado | Fuente final | Qué pasó |
|---|---|---|---|:---:|---|
| doc0006-q1 | 6. Reintegro.pptx | ¿Cómo ingreso al sistema para generar el informe de reintegro? | Correcta tras retest y evaluación actualizada; Golden Cache | Sí | La última respuesta incluye URL/Portales, usuario/contraseña y «Acceder», módulo Rectoría, informe Reintegro, filtros Año/Periodo/Fecha y Generar PDF. |
| doc0026-q2 | Asignación Académica.pptx | ¿Cómo ingreso al sitio web de la Universidad para comenzar el instructivo? | Correcta; Golden Cache | Sí | Correcta: explica la URL institucional y «Portales». |
| doc0073-q1 | Evaluacion Profesoral - Estudiante.pdf | ¿Cómo ingreso al sistema para realizar la evaluación profesoral? | Correcta tras retest dirigido; Golden Cache | Sí | La expansión de páginas contiguas permitió incluir la entrada al sistema junto con los pasos de la evaluación. |
| doc0078-q1 | Evaluaciones de selección ILE-TICS (FUNCIONARIOS).pptx | ¿Cómo modifico una oferta de evaluación? | Correcta; Golden Cache | Sí | Correcta: distingue evaluación ILE-TICS y conserva Editar, campos y Guardar. |
| doc0083-q2 | Gestión de Ayudas Educativas.pdf | ¿Qué hago después de modificar los campos de una ayuda educativa? | Parcial | Sí | La fuente de Ayudas Educativas no documenta cómo guardar; abstención segura, no se mezcló con otro aplicativo. |
| doc0111-q1 | Instructivo autorizaciones grados.pdf | ¿Por dónde ingreso al portal para iniciar el trámite de autorización de inscripción a grado? | Correcta | Sí | Correcta: ruta exacta SIA WEB → Registro y Control Académico → Autorización Inscripción para Grado. |
| doc0129-q1 | Instructivo Reportes Estrategias.pdf | ¿Qué datos tengo que seleccionar para generar el reporte de Estudiantes Remitidos? | Correcta; Golden Cache | Sí | Correcta: reporte, programa, estrategia, fechas, Buscar y advertencia de fecha inicial. |
| doc0131-q2 | Instructivo Verificación pagos V2.pdf | ¿Cómo exporto a Excel el listado de resultados de la búsqueda? | Correcta; Golden Cache | Sí | Correcta y prudente: distingue los módulos que exportan a Excel porque la pregunta no especifica cuál. |
| doc0135-q1 | Listado de volantes.pptx | ¿Cómo llego a la opción para generar el listado de volantes? | Correcta | Sí | Correcta: ruta hasta Listado de volantes y generación. |
| doc0136-q1 | Malla academica.pptx | ¿Qué datos debo completar al crear una malla académica? | Parcial | Sí | Omitió campos de creación presentes en la guía: código, periodos, año, periodo, reconocimiento si aplica y Guardar. |
| doc0151-q2 | Movilidad Académica - Estudiantes.pdf | ¿Qué debo completar en la sección de financiación de la movilidad? | Parcial | Sí | Omitió el campo «Idiomas», aunque estaba explícito en el contexto. |
| doc0159-q1 | P-GT-07_Procedimiento_Proteccion_de_Codigo_Malicioso_.pdf | ¿Qué debo hacer si recibo un correo sospechoso? | Correcta; Golden Cache | Sí | Correcta: no abrir ni responder, reportar y no reenviar. |
| doc0178-q2 | Programas.pptx | ¿Cómo agrego una asignatura a una malla académica? | Parcial | No | La fuente esperada no llegó al contexto final; el RAG paró en «Nuevo» y omitió buscar/elegir asignatura, periodo y Guardar. |
| doc0195-q1 | Reporte de estudiantes graduados.pptx | ¿Qué módulo debo seleccionar para generar el reporte de estudiantes graduados? | Parcial | Sí | La guía de graduados no identifica el módulo; el nombre de otro reporte no se debe transferir. La respuesta afirmó Estadísticas Institucionales sin respaldo específico. |
| doc0201-q2 | Reporte de Seguimiento.pptx | ¿Cómo llego al reporte «Mercadeo / Seguimiento» dentro del sistema? | Correcta; Golden Cache | Sí | Correcta: ruta completa por Portales → Mercadeo → Reportes → Mercadeo / Seguimiento. |
| doc0220-q2 | Reportes de Desertores.pdf | ¿Qué filtros debo completar antes de buscar un reporte de deserción? | Parcial | Sí | Omitió exigir «Nivel» y «Programa», y los dejó como condicionales pese a estar documentados en una fuente complementaria. |
| doc0226-q1 | Resultados de aprendizaje.pptx | ¿Cómo entro al portal para consultar los resultados de aprendizaje? | Correcta tras retest dirigido; Golden Cache | Sí | La expansión contigua incorporó Portal Estudiantes y Barranquilla a la respuesta. |
| doc0234-q1 | Todos_Reportes.pptx | ¿Cómo ingreso al sistema para generar informes de inscripciones y matrículas? | Parcial | No | La fuente Todos_Reportes llegó como título al candidato #1, bajó al puesto 23 tras rerank y no entró al contexto final. |
| doc0241-q1 | Volantes de pagos - Funcionarios.pptx | ¿Cómo ingreso al módulo de Volantes de Pagos? | Correcta; Golden Cache | Sí | Correcta: portal de la Universidad → Portales → Volantes de Pagos. |
| doc0242-q1 | Volantes.pdf | ¿Cómo llego al portal de estudiantes para acceder al instructivo de descarga del volante? | Correcta; Golden Cache | Sí | Correcta: Portal Estudiantes e inicio de sesión; aclara el límite de la guía sobre dónde está el instructivo. |

## Balance acumulado del grupo de 185 respuestas inicialmente parciales

Combinando la revisión multi-evidencia y los retests dirigidos, el estado actual de las 185 inicialmente parciales es **178 correctas de 185 (96,2 %), 7 parciales, 0 incorrectas y 0 no verificables**. Esta cifra es compuesta; **no** significa que se hayan repetido las 484 preguntas completas con la versión actual. De los 58 casos residuales que se generaron en vivo, 51 están correctos y 7 siguen parciales después de las correcciones.

En el conjunto original de 484, al combinar la línea base con las correcciones verificadas, hay **347 correctas (71,7 %), 7 parciales, 124 incorrectas y 6 no verificables**. Este total incorpora además la corrección del caso HTTP 500 `doc0001-q1`, que respondió correctamente en su retest. Las 124 incorrectas y las otras 6 no verificables de la corrida original no se reejecutaron dentro de esta campaña residual; por eso esta cifra tampoco es una nueva prueba de producción completa.

Golden Cache pasó de 239 casos tras la primera corrida a 343 después de promover 104 respuestas verificadas en la revisión multi-evidencia, y a **382** tras las reejecuciones posteriores. Desde 343 se promovieron 39 respuestas verificadas, incluidas las tres respuestas correctas de los retests dirigidos de páginas vecinas. Otras respuestas no superaron todos los controles estrictos y no se guardaron.

## Fallos que siguen pendientes

1. **Contexto contiguo y cobertura del presupuesto:** quedó resuelto para los tres casos dirigidos `doc0006-q1`, `doc0073-q1` y `doc0226-q1`; ahora se recupera el conjunto de chunks de páginas adyacentes con orden verificable y se priorizan vecinos del documento temáticamente exacto al ajustar el presupuesto. Debe mantenerse en futuras evaluaciones porque los 8 casos parciales restantes pueden tener causas distintas.
2. **Recuperación léxica/morfológica:** `doc0178-q2` no recuperó el instructivo de adición de asignaturas, aunque existe en el índice. «Agrego» y las formas «agregar/adición» no coinciden de forma suficiente con la búsqueda léxica actual. Se requiere normalización de lemas/sufijos o expansión morfológica no específica de este caso, evaluada contra consultas de verbos diferentes.
3. **Ancla de documento y ruta de entrada:** `doc0234-q1` encontró el título `Todos_Reportes.pptx` como candidato #1, pero el reranker lo bajó al puesto 23 y no entró en los chunks finales. Conviene preservar una ancla del documento cuyo título coincide fuertemente con el trámite y expandir su secuencia de acceso.
4. **Uso completo de evidencia ya recuperada:** `doc0136-q1` omitió campos de creación; `doc0151-q2` omitió «Idiomas»; `doc0220-q2` dejó «Nivel» y «Programa» como condicionales pese a evidencia explícita en documentos complementarios. El prompt por sí solo no bastó; hace falta una revisión de cobertura de cada subpregunta/campo o una segunda pasada de corrección con la evidencia pertinente.
5. **Límites seguros y calidad del benchmark:** `doc0083-q2` no tiene una instrucción de guardado para Ayudas Educativas, y `doc0195-q1` no identifica el módulo en la guía específica de graduados. Se mantuvieron parciales y fuera de Golden Cache porque no debe copiarse un botón o módulo de otro proceso. La evaluación debe marcar como no verificable/parcial una expectativa que no esté respaldada por el documento correcto.

## Archivos de evidencia

- Campaña original de 484 preguntas: `reports/indexed_documents_eval_20261006.md` y `.json`.
- Desglose de preguntas por grupos de 5 documentos (10 preguntas por grupo) y estado compuesto: `reports/five_document_group_summary_20261013.md`.
- Revisión multi-evidencia de 185 parciales: `reports/partial_multievidence_review_20261006.md` y `.json`.
- Reevaluación de los 20 casos residuales: `reports/partial_remaining_retest_20261013.json`.
- Detalle de los ajustes dirigidos anteriores: `reports/partial_context_detector_retest_20261013.json`, `reports/partial_account_guard_retest_20261013.json` y `reports/partial_hardware_guard_retest_20261013.json`.
- Retests de expansión por páginas y selección por fuente: `reports/partial_neighbor_context_retest_20261013.json`, `reports/partial_anchor_diversity_retest_20261013.json`, `reports/partial_preferred_neighbor_retest_20261013.json` y `reports/partial_preferred_neighbor_retest2_20261013.json`.
- Revisión actualizada de la respuesta nueva de Reintegro: `reports/partial_preferred_neighbor_retest2_rejudged_20261013.json`.
- Pruebas automatizadas dirigidas de expansión/presupuesto: `tests/test_rag_retrieval_precision.py`.
