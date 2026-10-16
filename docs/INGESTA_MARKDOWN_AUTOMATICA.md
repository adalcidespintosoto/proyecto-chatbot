# Ingesta automática mediante Markdown

## Flujo

1. UniMon busca archivos PDF y PPTX en `data/docs/` y sus subcarpetas.
2. Compara el hash del archivo y del prompt con `data/sanitized_docs/manifest.json`.
3. Si el documento es nuevo o cambió, extrae su texto por página/diapositiva y lo envía a GPT-6 Luna con `PROMPT_TRANSFORMACION_DOCUMENTOS_RAG.md`.
4. Valida que el Markdown tenga título, contenido y referencias a las páginas/diapositivas extraídas. Si falla la validación, no lo indexa.
5. Guarda la salida en `data/sanitized_docs/markdown/` y deja el original intacto.
6. En una reconstrucción completa, lee también las páginas y mapas visuales `Web_` que ya están en el RAG activo, guarda cada fragmento en `data/sanitized_docs/markdown/public_web/` y los indexa desde esos archivos Markdown. Conserva su URL, título, sección, orden de fragmento y metadatos de verificación visual. La etiqueta `source_type=public_web_ui` se conserva para que el RAG siga encontrando los mapas de pantalla; `indexed_format=markdown` valida el formato realmente indexado.
7. Genera embeddings y escribe en Chroma únicamente texto leído desde archivos `.md`. Cada chunk conserva la fuente, el archivo original o URL, la página, el orden y los hashes.

La carga de un PDF/PPTX desde el panel usa el mismo flujo. Una ejecución incremental vuelve a revisar el directorio, reutiliza Markdown cuyo hash siga vigente y procesa únicamente documentos nuevos o modificados. Una reconstrucción completa reemplaza el índice local solo cuando todos los documentos pasan validación.

## Primera reconstrucción del RAG

La base activa debe estar cerrada para que Windows libere los archivos internos de Chroma.

1. Detén el servidor UniMon.
2. Desde la raíz del proyecto, ejecuta:

   ```powershell
   .\.venv\Scripts\python.exe scripts\ingest_sanitized_documents.py --rebuild
   ```

3. Revisa los `.md` creados en `data/sanitized_docs/markdown/` y el resultado de cada documento en `data/sanitized_docs/manifest.json`.
4. Cuando el comando termine correctamente, inicia UniMon de nuevo:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

`--rebuild` prepara un Chroma temporal, confirma que todos sus registros provienen de Markdown, crea un respaldo verificado y solo entonces lo promueve a `CHROMA_DB_DIR`. También conserva los fragmentos públicos web del índice activo: no vuelve a consultar el sitio durante la reconstrucción ni los envía al LLM; registra que vienen de la instantánea ya indexada. Si falla la transformación, la validación, el respaldo o la promoción, el índice activo se conserva o se restaura.

En la instantánea actual, el índice contiene 101 fragmentos en 18 fuentes web, incluidos dos mapas visuales verificados. El manifiesto informa el conteo real encontrado al ejecutar el rebuild; cada archivo se guarda en `data/sanitized_docs/markdown/public_web/<fuente>/fragment_<n>.md`. Al generar el índice, cada archivo pasa por el splitter normal de 800/150; por eso el número de vectores puede ser mayor que los 101 fragmentos guardados.

## Documentos nuevos o modificados

Para revisar `data/docs/` sin reemplazar el índice:

```powershell
.\.venv\Scripts\python.exe scripts\ingest_sanitized_documents.py
```

El panel también transforma e indexa un archivo PDF/PPTX recién cargado. Si el índice activo todavía contiene documentos crudos, la ingesta incremental se detiene para no mezclar contenido crudo y Markdown; primero se debe completar la reconstrucción inicial con `--rebuild`.

## Reintentos de trazabilidad

Si GPT-6 Luna omite citas de páginas o diapositivas, el flujo intenta corregir la salida con la fuente y los errores concretos. Si aún faltan citas, hace un segundo intento centrado en el borrador, sin relajar la validación. Las salidas no aprobadas quedan en `data/sanitized_docs/rejected/` y no se indexan.

Al repetir la reconstrucción sin `--force`, los Markdown aprobados se reutilizan. Para documentos fallidos, el script intenta retomar el borrador rechazado y reparar sus citas antes de volver a generar el documento completo. El número de llamadas adicionales está limitado; si persiste el error, el rebuild se cancela y conserva el RAG activo.

## Respaldos y Golden Cache

Antes de promover la reconstrucción se copia el RAG activo y el Golden Cache bajo:

```text
%USERPROFILE%\Documents\Backups\UniMon\pre_markdown_ingestion_<fecha_hora>\
```

El `manifest.json` del respaldo registra los archivos, sus tamaños y hashes SHA-256. El Golden Cache se respalda, pero la ingesta no lo borra ni lo modifica. Por tanto, las respuestas que ya contiene pueden seguir utilizándose durante las consultas posteriores.

El respaldo previo a esta integración está en:

```text
C:\Users\adalcides.pintos\Documents\Backups\UniMon\pre_markdown_ingestion_20261016_114545\
```

## Límites

- La automatización admite PDF y PPTX. No transforma DOCX ni otros formatos.
- El Markdown se revisa con validaciones automáticas de estructura y trazabilidad; no sustituye una revisión visual humana del original.
- Los mapas de sitio web representan la última instantánea indexada. Para actualizarlos, ejecuta `scripts/ingest_public_web.py --apply`; ese flujo recorre las URLs aprobadas del manifiesto, guarda primero cada fragmento como Markdown y luego indexa lo leído desde el archivo. La reconstrucción no hace un rastreo web nuevo.
- La ingesta no limpia el Golden Cache; esa colección se conserva por separado.
