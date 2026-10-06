# Diagnóstico del RAG — traza de 100 consultas

Fecha: 2026-10-05T16:22:22-0500

## Método

- Se reprodujeron las 100 preguntas con las variantes multi-consulta generadas por el sistema, el filtro por rol, recuperación Chroma, reranker y ensamblado de contexto.
- Se simuló la llamada final al LLM para capturar exactamente los mensajes/contexto, sin generar otra respuesta ni guardar más pares en Golden Cache.
- La fuente esperada se comparó por nombre normalizado en candidatos, reranking y contexto final. Para las dos preguntas de credenciales se exigió que aparecieran ambos documentos complementarios.

## Antes del cambio

- Fuente(s) esperada(s) presentes en candidatos: **80/100**.
- Fuente(s) esperada(s) presentes tras reranking: **71/100**.
- Fuente(s) esperada(s) conservadas en el contexto enviado al LLM: **49/100**.
- Pérdidas por etapa, con el primer punto donde falta la evidencia: **20** en recuperación inicial, **9** en reranking, **22** al construir/limitar contexto; **49** llegaron con todas sus fuentes esperadas.

## Causa raíz confirmada y cambio

El filtro de hardware comprobaba si la subcadena `red` aparecía en la consulta. La frase coloquial **«me enredé»** contiene esas letras, activaba el filtro de red y excluía la categoría `academico` aunque la pregunta fuera de matrícula/inscripciones.

Reproducción confirmada: al agregar «me enredé» a una pregunta de cursos intersemestrales, `_build_query_filter` devolvía `category NOT IN (financiero, academico)`; al quitar esa frase, no aplicaba filtro. Cambié esa detección para exigir coincidencia de palabra completa, conservando el filtro para preguntas reales como «no puedo conectarme a la red wifi».

## Comparación tras el cambio

- Candidatos: **82/100** (antes 80).
- Reranking: **71/100** (antes 71).
- Contexto final: **50/100** (antes 49).
- Pérdidas tras el cambio: **18** en recuperación, **11** en reranking, **21** en contexto; **50** llegaron completos.

El cambio recuperó por completo la fuente del caso **35** («inscripción a cursos intersemestrales»): aparece en candidatos, reranking y contexto final (páginas 6–8 y 11). En el caso **95**, «me enredé» dejó de excluir la fuente: `Gestión de inscripciones.pdf` entró a candidatos, pero el reranker la descartó.

## Otros fallos que quedan aislados

- **Reranker:** el caso 95 tiene la fuente esperada en candidatos, pero no en el top rerankeado. Revisar relevancia del Cross-Encoder y cobertura por documento/entidad; no subir top-k a ciegas.
- **Empaquetado de contexto:** hay casos con la fuente en candidatos y reranking pero no en el contexto final. El caso 33 es un ejemplo. Se debe inspeccionar sus anclas, expansión vecina, orden de selección, límite de 12 chunks y presupuesto global de 2.400 tokens.
- **Filtro por rol/datos de prueba:** varias preguntas se redactaron con roles contradictorios (por ejemplo, «soy estudiante» y luego pide una operación de docente). El filtro de audiencia puede excluir documentos válidos; caso 21 terminó con rol `estudiante` pese a preguntar por ingreso docente de calificaciones. Esta batería no permite concluir que el clasificador falla igual con usuarios reales, pero sí muestra que los roles de la prueba deben ser coherentes.
- **Contexto presente, respuesta mala:** 13 respuestas incorrectas tenían la fuente esperada en su contexto por nombre; eso requiere revisar el texto real del chunk y el prompt final para diferenciar fragmento incompleto de fallo del LLM. El nombre de un archivo por sí solo no prueba que la página contenga el paso necesario.
- **Calidad del juez:** sus cuatro casos `no_verificable` son señales para revisión; el juez recibió como máximo dos fragmentos por fuente y recortes de evidencia. No los trataría como verdad de referencia sin verificar páginas y pasos esperados.

## Validación del cambio

- Prueba nueva: «me enredé» no debe activar el filtro de red en una consulta académica.
- Prueba de control: «no puedo conectarme a la red wifi institucional» conserva el filtro de hardware.
- Resultado dirigido: **3 pruebas aprobadas**.

## Archivos

- Traza previa (100 preguntas, candidatos/reranking/contexto/prompt): `coloquial_100_20261005_trace.json`.
- Traza repetida tras el cambio: `coloquial_100_20261005_trace_after.json`.
- Resultados de respuestas y evaluación de calidad: `coloquial_100_20261005_review.md`.
