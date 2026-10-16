# Comparación del índice RAG transformado (GPT-6 Luna)

Fecha: 16 de octubre de 2026

## Qué se comparó

Se ejecutaron las mismas 50 preguntas contra el índice actual y el índice candidato, con GPT-6 Luna. Las 50 respuestas de cada variante se generaron sin errores de API. El informe detallado con respuestas y trazas está en `scratch/sanitized_reindex_gpt6luna_20261016/retrieval_evaluation.json` (carpeta local ignorada por Git; contiene consultas históricas).

## Resultados

| Medida | Índice actual | Candidato Markdown |
|---|---:|---:|
| Fragmentos indexados | 7.408 | 2.221 |
| Preguntas con respuesta de API | 50/50 | 50/50 |
| Recuperación media de fuentes esperadas | 55,6% | 66,6% |
| Preguntas que devolvieron todas las fuentes esperadas | 40% | 42% |
| Latencia media | 5.557 ms | 5.382 ms |
| Latencia p95 | 6.938 ms | 6.744 ms |
| Fragmentos finales medios enviados al modelo | 17,92 | 11,92 |
| Fuentes finales medias | 2,22 | 6,26 |

Las referencias esperadas de las 43 preguntas históricas vienen de las fuentes citadas por el chatbot, por lo que son una aproximación y no una etiqueta revisada por una persona. El lector de referencias se corrigió para mantener comas que formen parte del nombre del archivo; los resultados previos a esa corrección se conservaron por separado.

Las siete preguntas de evaluación curadas dieron recuperación media de fuente de 85,7% en el índice actual y 92,9% en el candidato. En ambos, 6 de 7 devolvieron todas las fuentes curadas. Esto mide recuperación de documentos, no exactitud factual de la respuesta.

## Hallazgo detectado y corrección aplicada

En la pregunta «Estoy en primer semestre, ¿qué parte del recibo de matrícula tiene mis datos de acceso?», el documento **Activar Usuario y Correo institucional.pdf** contiene explícitamente que el usuario y la contraseña están al final del recibo. El candidato encontró ese fragmento durante la búsqueda y el reranking, pero no lo incluyó en el contexto final; GPT respondió que el documento no especificaba esa ubicación. Solo llegaron cuatro fragmentos al contexto final.

La causa fue que la frase «datos de acceso» no se reconocía como una consulta de cuenta/activación de primer ingreso. Por eso se aplicó el contexto compacto general y la ruta que reúne evidencia complementaria no se ejecutó. Se amplió la detección de intención para considerar también consultas de primer semestre que mencionan acceso, credenciales o el recibo de matrícula, sin activar esa ruta para preguntas generales de primer semestre.

La prueba de regresión primero reprodujo el fallo y, tras el ajuste, pasó. La suite `tests/test_rag_retrieval_precision.py` pasó 63/63. Después se consultó al GPT-6 Luna real usando los dos índices: el RAG activo (7.408 fragmentos) incluyó los pasos y la página que ubica las credenciales al final del recibo; el candidato (2.221 fragmentos) incluyó esa misma evidencia y el resultado del proceso de matrícula en GIE. Ambos respondieron correctamente y citaron los documentos complementarios. No se modificaron ni reindexaron los índices ni Golden Cache.

El candidato también produjo más fuentes finales en promedio (6,26 frente a 2,22); esto puede añadir distractores aunque baje el número de fragmentos. La corrección de esta consulta puntual no equivale a una nueva medición de exactitud global.

## Decisión y siguiente mejora

El candidato queda aislado y **no se promueve**. El índice activo y Golden Cache permanecen sin cambios.

Antes de plantear una promoción todavía se debe repetir la evaluación curada completa con el código actualizado y revisar la calidad factual de las respuestas; las tasas de fuentes recuperadas de este informe no son una medición de exactitud humana.
