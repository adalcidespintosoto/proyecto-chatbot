# Plan: replicar la ingesta de la Base de Conocimiento por dependencia

## Objetivo

Usar en cada chatbot de dependencia la misma experiencia y el mismo proceso que ya existe en **📤 Cargar Nuevo Documento** de UniMon: cargar el original, convertirlo a Markdown con el proceso existente, validar el resultado y hacer que RAG indexe el Markdown. Replicar también las opciones **🔍 Analizar Ambigüedad y Redundancia** y **⚡ Subir Directo**.

No crear una segunda implementación de ingesta. Reutilizar los servicios y componentes actuales y permitirles recibir la instancia destino. Los archivos temporales, la comparación de redundancia y la indexación deben quedar aislados por dependencia.

## Comportamiento acordado

1. Aceptar **PDF, PPTX y DOCX**. El original se conserva.
2. Reutilizar la conversión y validación a Markdown existentes. Solo el Markdown aprobado se divide en chunks y se indexa.
3. Usar **GPT-6 Luna como modelo primario para la ingesta**. Si no está disponible o la salida no supera la validación, permitir **Ollama como último recurso**. Registrar cuál se usó. El modelo que responde en el chat de cada dependencia no se cambia por la ingesta.
4. Mantener los dos caminos de la interfaz actual:
   - **Analizar Ambigüedad y Redundancia:** prepara y valida el Markdown, presenta el análisis y permite indexar conservando todo, reemplazar una fuente coincidente o cancelar.
   - **Subir Directo:** prepara, valida e indexa el Markdown sin abrir primero el análisis interactivo.
5. El análisis y las acciones posteriores comparan y modifican **solo el índice de la dependencia seleccionada**. No deben consultar ni alterar el ChromaDB global de UniMon ni el Golden Cache. “Deduplicar” conserva los chunks: como en la carga global actual, el análisis muestra similitud, pero no descarta contenido automáticamente.
6. Un fallo de conversión, validación o indexación se informa con la etapa concreta. El original permanece disponible; un Markdown no aprobado no se indexa.

## Lo que ya existe y lo que falta

- La Base de Conocimiento global ya presenta los controles **Analizar Ambigüedad y Redundancia** y **Subir Directo**.
- La carga global transforma documentos a Markdown antes de indexarlos, pero las rutas de auditoría y resolución actuales operan sobre el ChromaDB global. No se pueden reutilizar tal cual para una dependencia sin pasarles su índice y sus rutas.
- Las instancias ya tienen directorios de documentos, Markdown y ChromaDB propios. La carga de instancia actualmente solo acepta PDF/PPTX y no ofrece el mismo flujo de análisis/resolución.
- La conversión a Markdown ya tiene validaciones estructurales. Se debe conectar la comprobación de fidelidad con el original al mismo proceso para evitar indexar una conversión incompleta o contradictoria.

## Interfaz que se replicará

En cada tarjeta/formulario de una dependencia, presentar el mismo control de carga de la Base de Conocimiento, con la instancia seleccionada como destino:

```text
📤 Cargar Nuevo Documento
PDF / PPTX / DOCX → Markdown
Arrastra un archivo aquí o haz clic para examinar
El original se conserva y el Markdown validado es lo que se indexa en RAG.

[🔍 Analizar Ambigüedad y Redundancia] [⚡ Subir Directo]
```

No mostrar el selector global de carpetas por perfil en esta carga: la dependencia ya determina el espacio documental. Si se conserva algún metadato de audiencia para organizar archivos, este no debe filtrar la recuperación.

## Dónde queda cada elemento

Con la configuración actual (`DOCS_DIR=./data/docs`), una instancia se aloja en:

```text
data/chatbots/instances/<bot_id>/
├── docs/                         Originales PDF, PPTX o DOCX
├── sanitized_docs/
│   ├── markdown/                 Markdown aprobado que alimenta RAG
│   ├── rejected/                 Conversiones rechazadas o pendientes, si aplica
│   └── manifest.json             Estado, origen, proveedor/modelo y validación
├── chroma_db/                    Vectores, chunks y metadatos de esa instancia
└── specialization.md             Perfil de especialidad generado para enrutar
```

El archivo `.md` se guarda en disco. ChromaDB no guarda ese archivo como tal: guarda los chunks extraídos del Markdown, sus embeddings y metadatos. El índice global y Golden Cache quedan separados y fuera del flujo de ingesta de instancias.

## Fases y criterios de aceptación

### 1. Reutilizar el cargador normal en las instancias

- [x] Agregar en cada dependencia las acciones **Analizar Ambigüedad y Redundancia** y **Subir Directo**.
- [x] Presentar el resultado del análisis en la tarjeta, con métricas, coincidencias, fragmentos comparados y acciones de resolución.
- [x] Reutilizar sanitización, fidelidad, fragmentación y embeddings existentes.
- [x] La interfaz y el servidor aceptan `.pdf`, `.pptx` y `.docx`.

**Verificación:** revisar ambas acciones en una instancia de prueba; confirmar que UniMon global conserva su comportamiento actual.

### 2. Aislar análisis y resolución por dependencia

- [x] El análisis compara chunks del Markdown validado con el Chroma del `bot_id` seleccionado.
- [x] Cada sesión temporal queda dentro de la carpeta de su instancia y valida el `bot_id` al resolverla.
- [x] El reemplazo indexa el documento nuevo y después retira la fuente seleccionada del mismo `bot_id`.
- [x] No se eliminan chunks automáticamente por similitud; la interfaz comunica que conservará toda la evidencia.
- [x] Las rutas de carga de instancia no llaman al Chroma global ni modifican Golden Cache.

**Verificación:** analizar un documento en dos dependencias con índices distintos y comprobar que los resultados y cambios permanecen separados.

### 3. Admitir Word sin alterar los formatos existentes

- [x] Procesar `.docx`, agrupar por encabezados y conservar párrafos, listas, tablas e imágenes reconocidas.
- [x] Rechazar `.doc` binario antiguo mediante el mensaje de formato no admitido.
- [x] Mantener las rutas existentes de PDF/PPTX.

**Verificación:** un DOCX con títulos, lista y tabla produce Markdown trazable; PDF y PPTX de referencia siguen funcionando.

### 4. Aplicar proveedor de ingesta y validación antes de indexar

- [x] GPT-6 Luna procesa primero la extracción y la generación/organización del Markdown.
- [x] Ollama se intenta como último recurso y proveedor/modelo quedan registrados en manifiesto y metadatos.
- [x] La ruta de instancia compara el Markdown con el original antes de indexar; diferencias o comparaciones inconclusas bloquean la indexación.
- [x] Los errores de procesamiento se muestran sin exponer credenciales.

**Verificación:** simular éxito GPT-6 Luna, fallo de API, Markdown incompleto, datos alterados y fallo de Ollama. Comprobar los estados en Admin y en los logs.

### 5. Carga, límites, almacenamiento y reversión

- [x] Se aplica el límite configurado mediante el validador compartido (15 MB por defecto).
- [x] La carga directa conserva el original si falla la transformación o validación y no anuncia éxito de indexación.
- [x] Las rutas por instancia están documentadas arriba; la carga auditada permite reintentar de forma idempotente.
- [ ] Ejecutar una prueba funcional con ambas opciones, tres formatos y dos instancias; confirmar que RAG global y Golden Cache no cambian.

**Verificación:** archivo aceptado y archivo demasiado grande; inspeccionar directorios, manifiesto y conteos antes/después.

## Riesgos y decisiones

| Riesgo | Respuesta del plan |
|---|---|
| El análisis actual usa el RAG global | Pasar explícitamente el runtime/índice de la dependencia; no llamar esa ruta con valores globales por defecto. |
| Markdown y contenido comparado no coinciden | Analizar el contenido ya preparado para indexación, manteniendo referencias al original. |
| El fallback local produce Markdown de menor calidad | Aplicar las mismas validaciones y no indexar si no las supera. |
| El archivo supera 15 MB | Informar el límite actual; cambiarlo solo mediante configuración explícita y un límite finito. |
| Word tiene paginación variable | Guardar referencias a encabezados, párrafos y tablas en vez de inventar números de página estables. |

## Fuera de alcance

- Cambiar el LLM que responde en la conversación de cada dependencia.
- Cambiar embeddings, reranker, Golden Cache o el índice global de UniMon.
- Añadir carpetas por rol como filtro de búsqueda.
- Crear otro proceso paralelo de ingesta que replique por separado el actual.

## Estado

La implementación está lista para validación funcional. Se verificaron sintaxis Python, sintaxis JavaScript y limpieza del diff; no se ejecutó una ingesta ni se inició/reinició el servidor.
