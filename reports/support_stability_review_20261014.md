# Revisión de estabilidad de respuestas de UniMon — 14/10/2026

## Resultado

Se ejecutó `RouterLogic.procesar_mensaje` con el proveedor OpenAI real, sesiones aisladas y los documentos ya indexados. Cada respuesta se revisó por contenido; un HTTP 200 o una respuesta fluida no bastaron para calificarla como correcta. Los reportes JSON guardan pregunta, respuesta completa, fuentes, latencia y veredicto de cada caso.

| Lote | Correctas | Parciales | Incorrectas | Acierto estricto |
| --- | ---: | ---: | ---: | ---: |
| Segunda ronda, antes de estos ajustes | 13/20 | 5 | 2 | 65 % |
| Segunda ronda, repetición final | 16/20 | 4 | 0 | 80 % |
| Preguntas nuevas, antes del ajuste final | 15/20 | 4 | 1 | 75 % |
| Preguntas nuevas, repetición final | 19/20 | 1 | 0 | 95 % |

En las dos repeticiones finales: **35/40 correctas, 5 parciales y 0 incorrectas (87,5 %)**. El mínimo observado por lote fue 80 %. Las medianas de respuesta fueron 6,8 s en ambos lotes; el máximo fue 18,7 s y 16,5 s, respectivamente. Son muestras pequeñas y parcialmente reutilizadas para corregir fallos: todavía no permiten prometer que cualquier lote futuro alcance 80 %.

## Causas y cambios

1. **Se perdían páginas decisivas después del reranker.** La selección ahora reserva una fuente cuyo título coincide con la intención, conserva páginas textuales de los extremos de procedimientos largos, expande hasta tres páginas contiguas en esa fuente para consultas de varios pasos y elige los chunks finales según coincidencia con la acción, dentro del presupuesto de tokens. Se mantiene la página y el orden documental verificable. No se reindexó Chroma ni se modificaron los documentos.
2. **Las expresiones coloquiales se interpretaron como otra intención.** Se normalizaron `meter`/`invitar` con `agregar`, `equipo` con `grupo`, `bajar` con `descargar`, y `notas` con `calificaciones`. Se evita leer `miro` como el nombre de una plataforma en “en el portal miro las notas”. La consulta sobre bajar Office ya no se clasifica como recuperación de credenciales solo por mencionar “cuenta institucional”.
3. **La evidencia de canales, VPN y seguridad quedaba desplazada.** Se reconocen preguntas como “¿a qué correo se envía?”, se reservan páginas con el canal de la acción, se da preferencia a siglas explícitas como VPN y se detectan alertas de antivirus y mensajes que piden validar credenciales mediante un enlace.
4. **El LLM a veces omite un dato presente.** La restauración de backup lo mostró: en la repetición focalizada no usó el correo aunque la página 18 del P-GT-10 estaba presente; en la ronda completa posterior sí respondió `solicitudcomputo@unisimon.edu.co`. Esto sigue siendo variación de generación, no una ausencia del documento.

## Parciales que siguen abiertos

- **Segunda ronda:** creación de cuenta institucional sin sistema identificado; certificado de estudiante sin opción concreta; informe de estudiantes nuevos sin el paso inicial de Rectoría; restauración de un archivo de carpeta compartida sin procedimiento específico confirmado.
- **Lote nuevo:** recuperación de contraseña estudiantil: indica el flujo, pero omite el nombre exacto de la opción que lo inicia.

Las 35 respuestas calificadas como correctas fueron revisadas, pasaron el validador del Golden Cache y se guardaron con rol general. Las cinco parciales no se promovieron. La colección pasó de 595 a 630 casos; las respuestas de Golden siguen siendo ejemplos históricos y los documentos recuperados conservan prioridad como evidencia institucional.

## Verificaciones técnicas

- `tests/test_rag_retrieval_precision.py`: 56 pruebas aprobadas antes de añadir los nuevos casos; 58 incluidas en la ejecución combinada posterior.
- `tests/test_router_rules.py` junto con recuperación: **80/80 aprobadas**. Tres pruebas antiguas esperaban pedir un rol antes de responder; se actualizaron para comprobar el flujo vigente, sin volver a introducir ese paso.
- El servidor se reinició con `.venv` tras los cambios de código. No se alteró el índice documental.

## Archivos de evidencia

- `support_effectiveness_round2_20261014.json`: referencia de 65 %.
- `support_effectiveness_round2_final_20261014.json`: repetición final de esa ronda.
- `support_effectiveness_holdout_20261014.json`: 20 formulaciones nuevas antes del ajuste final.
- `support_effectiveness_holdout_after_fixes_20261014.json`: repetición final de las 20 formulaciones.

Para medir estabilidad operativa, tomar lotes nuevos y no vistos de al menos 50 preguntas, con distribución por tema y rol, revisar los veredictos contra fuentes y seguir el porcentaje por lote. No entrenar ni ajustar el RAG usando las preguntas reservadas para medición.
