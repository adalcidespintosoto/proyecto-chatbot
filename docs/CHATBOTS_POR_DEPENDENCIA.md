# Chatbots por dependencia

## Para qué sirve

El administrador puede crear otro asistente desde el panel, por ejemplo para Bienestar o Admisiones, sin editar Python ni `.env`. UniMon sigue siendo el asistente principal y conserva su flujo actual.

## Crear y preparar una instancia

1. Inicia sesión en `/admin` y abre **Diagnóstico de Servidor**.
2. En **Chatbots por dependencia**, completa el nombre visible, la dependencia, el alcance, al menos un canal de soporte y el proveedor/modelo LLM. El selector consulta los modelos disponibles para las credenciales cloud configuradas y muestra los modelos instalados en Ollama. Si necesitas otro proveedor, elige **Otro proveedor / API compatible** y especifica su nombre, protocolo, modelo, clave API, URL base HTTPS y tiempo máximo de espera. Se admiten Anthropic Messages API y servicios compatibles con el formato de chat de OpenAI. El identificador del enlace es opcional; si se deja vacío, se genera a partir del nombre de la dependencia.
3. Selecciona **Crear asistente**. El sistema registra la instancia y crea sus carpetas.
4. En la tarjeta de la instancia, selecciona **Cargar PDF o PPTX**. El flujo conserva el original, genera y valida el Markdown e indexa ese Markdown en el ChromaDB de esa instancia.
5. Selecciona **Abrir chat** para obtener el enlace. Su forma es `http://localhost:8000/?bot=<identificador>`; en un servidor compartido, usa el dominio de ese servidor.
6. El panel ofrece **Probar en el router** para abrir el chatbot jefe en `/?router=1`.

Si la conversión o indexación falla, el archivo fuente se conserva en la carpeta de esa instancia y el panel muestra el error. Corrige el archivo o revisa la terminal antes de volver a cargarlo; el mismo nombre de archivo no se acepta dos veces dentro de una instancia.

## Datos separados y datos compartidos

Cada instancia tiene almacenamiento independiente, derivado de la ruta configurada en `DOCS_DIR`:

```text
<carpeta de datos>/chatbots/instances.sqlite3
<carpeta de datos>/chatbots/instances/<identificador>/docs/           # PDF/PPTX originales
<carpeta de datos>/chatbots/instances/<identificador>/sanitized_docs/ # Markdown y manifest.json
<carpeta de datos>/chatbots/instances/<identificador>/chroma_db/      # Índice vectorial de esa instancia
<carpeta de datos>/chatbots/instances/<identificador>/specialization.md # Perfil de enrutamiento
```

El nombre, alcance y contactos quedan en SQLite. Las conversaciones de los asistentes adicionales se guardan en memoria por instancia y sesión; se eliminan al vencer su tiempo de inactividad o al reiniciar el servidor. No se reutiliza la conversación, el RAG ni Golden Cache de UniMon.

Cada instancia conserva su selección de proveedor y modelo. Los proveedores incorporados usan las claves globales de `.env`; una configuración personalizada guarda su endpoint, modelo y tiempo de espera en el registro de esa instancia, y cifra su clave API en SQLite. El panel confirma que hay una clave guardada, pero nunca la devuelve ni la vuelve a mostrar. Si se cambia el protocolo o la URL del proveedor, hay que volver a ingresar la clave para evitar reutilizarla en un destino distinto. Para habilitar el cifrado, genera una sola vez un secreto aleatorio con `python scripts/generate_llm_encryption_key.py` y guárdalo como `LLM_CREDENTIALS_ENCRYPTION_KEY` en `.env`. Consérvalo en el gestor de secretos del servidor y en la copia segura, porque perderlo impide descifrar las claves guardadas. El identificador del modelo no instala ni habilita por sí mismo un servicio. Los endpoints personalizados deben ser HTTPS públicos; las URLs privadas/locales y las redirecciones no se admiten. Un proveedor con protocolo propietario distinto de los dos admitidos requiere implementar un adaptador en el backend. Los embeddings, el reranker y los recursos del servidor siguen siendo compartidos. Los documentos, las búsquedas y el índice permanecen aislados por instancia. Las instancias que ya existían reciben durante la migración el proveedor/modelo global que estaba configurado.

## Alcance actual

- Los asistentes adicionales responden consultas documentales con su propio RAG y muestran el correo/teléfono configurado.
- Aceptan PDF y PPTX. Cada archivo sigue el flujo de saneamiento a Markdown usado por la ingesta actual.
- No crean tickets GLPI ni comparten la Golden Cache de UniMon.
- El perfil `specialization.md` se genera automáticamente, sin otra llamada al LLM, con el alcance administrativo y los nombres/secciones de los Markdown saneados. Se actualiza al editar el alcance o terminar una nueva ingesta. Orienta al router; no es una fuente de pasos ni se indexa en el RAG.
- Si una instancia ya existía antes de habilitar el router y no tiene perfil, se crea al iniciar la aplicación.
- El administrador puede editar nombre, dependencia, alcance y contactos. El identificador del enlace no cambia al editar.
- **Desactivar** quita el asistente de los enlaces públicos y del router, pero conserva originales, Markdown, índice y métricas. El panel permite reactivarlo.
- Las consultas de una instancia se guardan en `data/analytics.db` con fuente `CHATBOT_INSTANCE:<identificador>`. Se suman a consultas, sesiones, latencia y tokens de los KPIs globales y aparecen desglosadas por instancia en el panel. La resolución y el escalado porcentuales de UniMon excluyen estas sesiones mientras los asistentes adicionales no tengan una señal propia de feedback.
- Los documentos cargados para estas instancias aparecen en la tarjeta del chatbot correspondiente; no se mezclan con el catálogo documental de UniMon.

## Enrutador o chatbot jefe

El modo router se prueba en `http://localhost:8000/?router=1`; no reemplaza la ruta normal `/`.

1. El enrutador toma el alcance de cada asistente y su `specialization.md`. Si hay más de 12 instancias activas, usa el modelo de embeddings compartido para preseleccionar hasta 12 candidatas; el LLM clasificador elige únicamente entre esa lista permitida y UniMon.
2. Cuando una dependencia coincide claramente, el enrutador reenvía la consulta al endpoint de esa instancia. La respuesta se genera con su índice aislado y conserva la sesión de ese bot.
3. Si no hay coincidencia clara, la clasificación falla o no existen especialistas activos, se usa UniMon como asistente general.
4. La respuesta del chat muestra el nombre del asistente que atendió. La clasificación se añade a los tokens y la latencia de esa interacción.

El modo router agrega una llamada breve al LLM para clasificar y luego la llamada normal del chatbot elegido para redactar la respuesta. Si hay más de 12 instancias, antes se preseleccionan candidatas con los embeddings compartidos.

### Prueba manual recomendada

1. Crea dos instancias con alcances distintos (por ejemplo, Admisiones y Bienestar) y carga un PDF/PPTX en cada una.
2. En el panel abre **Ver perfil de especialidad generado**. El Markdown debe mostrar el alcance, el nombre del documento y sus encabezados.
3. Abre `/?router=1` y realiza una pregunta propia de cada dependencia; valida el nombre que aparece en el pie de la respuesta y las referencias documentales.
4. Haz una pregunta de soporte TI fuera de esos alcances; el destino esperado es UniMon.
5. Revisa el KPI de consultas global, tokens y latencia y las métricas de cada tarjeta. El conteo por bot debe subir una unidad por pregunta.
6. Edita el alcance y verifica el perfil actualizado. Desactiva una instancia: su URL directa debe dejar de estar disponible y el router ya no debe elegirla. Reactívala para restaurar el servicio con los mismos datos.

La clasificación del LLM es una decisión de enrutamiento, no una garantía de acierto. Revisa el destino reportado en cada respuesta durante las pruebas; si una consulta cae en UniMon, el fallback es deliberado para reducir derivaciones incorrectas.

## Copia de seguridad

Para respaldar una instancia, copia juntos `instances.sqlite3` y su carpeta `instances/<identificador>`. Conserva el original, el Markdown, el perfil de especialidad, el manifiesto y ChromaDB. Para restaurar, detén la aplicación, devuelve esas rutas y vuelve a iniciar el servidor. Una copia solo de ChromaDB no conserva la configuración ni los PDF/PPTX originales.
