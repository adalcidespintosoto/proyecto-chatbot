# Evaluación de documentos indexados — 20261015_152026

- Índice: `langchain`; fragmentos: **7408**; documentos indexados: **260**; seleccionados: **210**.
- Lotes de preguntas completados: **1**; preguntas: **20/420**.
- Preguntas generadas sin una palabra literal distintiva del título: **3** (se revisan contra la fuente completa).
- HTTP: **0** respuestas correctas, **20** fallos.
- Fuente objetivo recuperada: **0/20**.
- Calidad automática preliminar: correctas **0**, parciales **0**, incorrectas **10**, no verificables **10** (0.0% del total).
- Entre preguntas respondibles según la evidencia: **0/20** correctas (0.0%).
- Golden Cache: **0** respuestas guardadas; la promoción automática está habilitada.
- Latencia p50/p95: **240019.6 / 240020.7 ms**.

## Fallas y plan de mejora

- **No se recuperó la fuente objetivo (20 casos):** Revisar consulta generada, variantes léxicas, normalización del nombre de fuente y cobertura de chunks por documento; confirmar con trazas antes de cambiar umbrales.
- **Respuesta parcial, incorrecta o no verificable (20 casos):** Agrupar las razones del juez por tipo de omisión; ajustar recuperación contextual y la instrucción de completar procedimientos, y agregar cada fallo como regresión.
- **Error HTTP o de transporte (20 casos):** Separar fallos del servidor, limitación del proveedor y timeout; ajustar concurrencia/reintentos solo con base en el código de error observado.
- **Latencia superior a 60 segundos (20 casos):** Medir tiempo de recuperación, reranking y generación por separado; reducir candidatos redundantes y aplicar límites de contexto adaptativos.

## Lotes

| Lote | Rango de documentos | Preguntas | Correctas | Fuente objetivo | Fallos HTTP | Golden Cache |
|---:|---|---:|---:|---:|---:|---:|
| 1 | 51-60 | 20 | 0 | 0/20 | 20 | 0 |

## Resultados por pregunta

| # | Documento | Pregunta | HTTP | Fuente | Calidad | Confianza | Golden | Respuesta |
|---:|---|---|---:|---|---|---:|---|---|
| 1 | Configuracion de Evaluaciones.pptx | ¿Cómo llego a la Configuración de Evaluaciones en Bienestar? | — | no | incorrect | 0.99 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot; no indica cómo llegar a la Configuración de Evaluaciones. |  |  |  |  |  |  |
| 2 | Configuracion de Evaluaciones.pptx | ¿Cómo creo una oferta en la Configuración de Evaluaciones y qué tipos de evaluación puedo elegir? | — | no | incorrect | 0.99 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot sobre cómo crear la oferta ni los tipos de evaluación. |  |  |  |  |  |  |
| 3 | Consulta de Excepciones, bloqueos y sanciones.pdf | ¿Cómo consulto los bloqueos, sanciones o excepciones asociados a un estudiante? | — | no | incorrect | 0.99 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot sobre cómo consultar bloqueos, sanciones o excepciones. |  |  |  |  |  |  |
| 4 | Consulta de Excepciones, bloqueos y sanciones.pdf | ¿Se pueden descargar reportes de Bloqueos, Sanciones y Excepciones y cómo se generan? | — | no | incorrect | 0.99 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot sobre los reportes ni cómo generarlos. |  |  |  |  |  |  |
| 5 | Consulta de Hoja de Vida - Matrículas.pdf | En la Consulta de Hoja de Vida de Matrículas, ¿cómo busco a una persona? | — | no | incorrect | 0.99 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot sobre cómo buscar a una persona. |  |  |  |  |  |  |
| 6 | Consulta de Hoja de Vida - Matrículas.pdf | ¿Qué información muestra la Consulta de Hoja de Vida de Matrículas? | — | no | incorrect | 0.99 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot sobre la información que muestra la consulta. |  |  |  |  |  |  |
| 7 | Consulta de Hoja de Vida.pdf | Para la Consulta de Hoja de Vida desde Inscripción, ¿qué icono debo seleccionar en SIA WEB? | — | no | incorrect | 0.99 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot que indique qué icono seleccionar. |  |  |  |  |  |  |
| 8 | Consulta de Hoja de Vida.pdf | ¿Cómo hago una búsqueda en la Consulta de Hoja de Vida desde Inscripción? | — | no | incorrect | 0.99 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot sobre cómo realizar la búsqueda. |  |  |  |  |  |  |
| 9 | Convenio Institucional.pdf | ¿Cómo consulto la información del módulo Convenio Institucional? | — | no | incorrect | 0.99 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot sobre cómo consultar la información del módulo. |  |  |  |  |  |  |
| 10 | Convenio Institucional.pdf | ¿Puedo guardar o imprimir como PDF la información de Convenio Institucional? | — | no | incorrect | 0.99 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot sobre guardar o imprimir la información como PDF. |  |  |  |  |  |  |
| 11 | CP-GT-01_Gestion_de_TI.pdf | ¿Qué servicios abarca el proceso de Gestión de TI? | — | no | no_verificable | 1.0 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot ni estado HTTP exitoso que permita evaluarla. |  |  |  |  |  |  |
| 12 | CP-GT-01_Gestion_de_TI.pdf | ¿Cómo se hace el seguimiento al desempeño del proceso de Gestión de TI? | — | no | no_verificable | 1.0 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot ni estado HTTP exitoso que permita evaluarla. |  |  |  |  |  |  |
| 13 | Creación de Programas.pptx | ¿Cómo llego a la opción para agregar programas en SIAAF WEB? | — | no | no_verificable | 1.0 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot ni estado HTTP exitoso que permita evaluarla. |  |  |  |  |  |  |
| 14 | Creación de Programas.pptx | ¿Cómo registro un programa nuevo en SIAAF WEB? | — | no | no_verificable | 1.0 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot ni estado HTTP exitoso que permita evaluarla. |  |  |  |  |  |  |
| 15 | Crear reuniones en teams - iPads aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.pdf | ¿Cómo creo en Teams una reunión vinculada a un curso y la repito cada semana? | — | no | no_verificable | 1.0 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot ni estado HTTP exitoso que permita evaluarla. |  |  |  |  |  |  |
| 16 | Crear reuniones en teams - iPads aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.pdf | ¿Dónde aparece en Teams una reunión creada para un curso? | — | no | no_verificable | 1.0 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot ni estado HTTP exitoso que permita evaluarla. |  |  |  |  |  |  |
| 17 | Crear reuniones No asociadas a grupos.pdf | ¿Cómo creo una reunión en Teams que no esté asociada a un grupo? | — | no | no_verificable | 1.0 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot ni estado HTTP exitoso que permita evaluarla. |  |  |  |  |  |  |
| 18 | Crear reuniones No asociadas a grupos.pdf | ¿Cómo agrego participantes a una reunión no asociada a grupos en Teams? | — | no | no_verificable | 1.0 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot ni estado HTTP exitoso que permita evaluarla. |  |  |  |  |  |  |
| 19 | Credenciales microsoft.pdf | ¿Dónde consulto mis credenciales de Microsoft desde el Portal de Gestión Académico-Administrativa? | — | no | no_verificable | 1.0 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot ni estado HTTP exitoso que permita evaluarla. |  |  |  |  |  |  |
| 20 | Credenciales microsoft.pdf | ¿Qué requisitos debe cumplir la nueva contraseña de Microsoft? | — | no | no_verificable | 1.0 | no |  |
|  |  | **Motivo:** No hay respuesta del chatbot ni estado HTTP exitoso que permita evaluarla. |  |  |  |  |  |  |
