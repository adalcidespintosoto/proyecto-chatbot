# Manual técnico integral de UniMon

**Revisión documental:** 21 de octubre de 2026 (árbol de trabajo local; validar las funciones recientes en el entorno de entrega)

**Audiencia:** practicante de TI, desarrollador, administrador del servicio y responsable de conocimiento.  
**Fuente de verdad:** código y configuración presentes en el repositorio. Este manual corrige descripciones históricas que ya no coinciden con el flujo actual.

## 1. Resumen del sistema

UniMon es una aplicación Python/FastAPI para soporte TI de primera línea. Incluye canales web y opcionalmente WhatsApp; un router conversacional con sesiones; recuperación documental RAG; un cliente para modelos OpenAI, Gemini u Ollama; integración opcional con GLPI; un panel administrativo y telemetría local.

No es un agente general que pueda operar los sistemas institucionales, aprobar trámites ni confirmar permisos. La generación de texto propone una respuesta a partir de evidencia; los sistemas externos y las áreas institucionales siguen siendo responsables de ejecutar o autorizar acciones.

### Componentes principales

| Componente | Responsabilidad |
|---|---|
| FastAPI | API HTTP, CORS, cabeceras básicas, páginas web, rutas y ciclo de vida. |
| Router conversacional | Estado y contexto por session_id, reglas de dominio, diagnóstico, feedback y flujo de ticket. |
| Recuperación RAG | Busca fragmentos de la base documental, ordena evidencia y la limita por presupuesto. |
| ChromaDB | Índice persistente de chunks del corpus y, en otra ruta, memoria Golden Cache. |
| Cross-Encoder | Vuelve a ordenar candidatos; su score no se trata como una probabilidad calibrada de verdad. |
| Cliente LLM | Envía generación al proveedor configurado y tiene fallback a Ollama en los flujos conversacionales. |
| Ingesta multimodal | Transforma PDF, PPTX y DOCX compatibles a Markdown, valida la estructura y genera chunks; las cargas de instancias agregan cotejo de fidelidad antes de indexar. |
| Catálogo de enrutamiento | Resume metadatos de Markdown elegibles para comparar UniMon y las dependencias sin copiar procedimientos completos al clasificador. |
| GLPI | Crea o consulta tickets cuando la integración externa está configurada. |
| SQLite | Guarda telemetría y eventos consultados por el panel de analítica. |
| Interfaz web/WhatsApp | Presenta mensajes, botones y continuidad de la conversación. |

CrewAI y LangGraph **no están instalados ni son necesarios para ejecutar el sistema actual**. LangChain sí aparece en requirements y se usa como integración de documentos, splitters, embeddings y Chroma; el flujo y las transiciones están programados directamente en servicios Python, no son un grafo LangGraph.

## 2. Flujo de una consulta

~~~mermaid
flowchart TD
    U[Web o WhatsApp] --> API[FastAPI: validación y sanitización]
    API --> R[Router conversacional por session_id]
    R --> G{Saludo, límite de dominio, acción, ticket o consulta}
    G -->|saludo / regla| S[Respuesta de regla]
    G -->|avería física| D[Diagnóstico breve y oferta de escalamiento]
    G -->|consulta documental| C[Normalización y expansión de consulta]
    C --> F[Filtro temático por categoría si aplica]
    F --> V[Búsqueda vectorial Chroma top 8 por variante]
    F --> B[Recuperación léxica BM25 complementaria]
    V --> M[Unión y deduplicación de candidatos]
    B --> M
    M --> X[Cross-Encoder: ordena hasta 80 candidatos]
    X --> N[Selector de anclas y vecinos secuenciales]
    N --> T[Presupuesto de chunks y tokens estimados]
    T --> L[LLM configurado]
    L --> O[Normalización y guardrails de salida]
    O --> R
    S --> R
    D --> R
    R -->|solicitud autorizada por el usuario| GL[GLPI: alta o seguimiento de ticket]
    R --> TEL[Telemetría SQLite]
~~~

### Paso a paso del endpoint de chat

1. POST /api/chat admite mensaje/message y un session_id. Si el cliente no lo envía, el servidor genera uno; para continuar una conversación, reutiliza el ID recibido. El valor literal `default_session` se rechaza.
2. La capa HTTP rechaza contenido vacío, limita el texto a 600 caracteres, quita etiquetas HTML y aplica el detector de instrucciones maliciosas.
3. RouterLogic carga o crea una TicketSession en memoria, agrega historial y detecta saludos, cancelaciones, feedback, preguntas fuera de dominio, solicitudes físicas y acciones GLPI antes de llamar RAG.
4. Si es una pregunta institucional, el rol puede mantenerse/inferirse para el tono y reglas conversacionales. En el índice RAG no se excluyen documentos porque su metadato audience sea estudiante, docente o administrativo. Sí hay filtros **temáticos** de category para reducir colisiones en ciertos tipos de consulta.
5. RAG recupera y ordena evidencia. Si no hay contexto que considere utilizable, devuelve una abstención/oferta de soporte; no consulta GLPI para responder una pregunta documental.
6. El proveedor LLM genera la respuesta con instrucción de soporte N1, el contexto recuperado y partes recientes del historial. Golden Cache puede aportar una pregunta similar para ampliar búsqueda, pero la respuesta almacenada no se copia al contexto factual.
7. Se limpian patrones de salida y se registra interacción, latencia, fuente y contadores de tokens en analytics.db.
8. ChatResponse expone tipo, mensaje, ticket_id, estado, quick replies y fuentes cuando están disponibles. Una ruta de regla directa puede no contener fuentes documentales.

## 3. Pipeline RAG actual

### 3.1 Indexación

La entrada de compatibilidad `scripts/ingest_multimodal_docs.py` delega la transformación e indexación actual a `scripts/ingest_sanitized_documents.py`:

- Recorre el directorio configurado DOCS_DIR y subdirectorios; procesa PDF, PPTX y DOCX compatibles.
- PDF: extrae texto por página y metadatos de página. Páginas escaneadas pueden depender de extracción visual configurada.
- PPTX: extrae texto por diapositiva, tablas, notas e imágenes incrustadas.
- La interpretación visual de imágenes intenta OpenAI `gpt-6-luna` cuando hay clave configurada y usa el modelo de visión de Ollama como último recurso. Si ambos intentos fallan, la extracción se detiene para evitar indexar un documento incompleto. Esto no demuestra por sí solo que toda imagen haya quedado descrita correctamente.
- Limpia boilerplate y divide con RecursiveCharacterTextSplitter: chunk_size 800 y chunk_overlap 150. Son **caracteres aproximados**, no tokens.
- Añade prefijo passage: al generar embeddings E5 normalizados y guarda en Chroma con metadatos y IDs deterministas que contienen origen/página/chunk cuando ese origen permite verificar el orden.
- El modo incremental usa hashes de fuente y Markdown del manifiesto para evitar reconvertir y reindexar archivos vigentes; vuelve a procesar fuentes modificadas. El flujo administrativo de reemplazo sigue requiriendo revisión antes de retirar otra fuente.

El corpus puede cambiar entre revisiones: consulta el manifiesto, el catálogo administrativo y la colección activa para contar las fuentes realmente indexadas. Los XLSX presentes no forman parte de este pipeline. La presencia de un archivo en `data/docs` o la aceptación de una subida no equivalen a su incorporación al RAG; comprueba el estado de transformación, la auditoría aplicable y los chunks indexados.

### 3.2 Búsqueda y selección

1. Las consultas se normalizan y MultiQuery produce hasta tres reformulaciones más la pregunta original (hasta cuatro consultas totales); se filtran variantes que cambian el idioma o pierden la plataforma consultada.
2. E5 consulta Chroma con prefijo query:. La búsqueda vectorial usa hasta 8 hits por variante y el umbral MIN_RELEVANCE_SCORE_THRESHOLD configurado en el servicio.
3. BM25 añade candidatos léxicos. El score vectorial y el léxico sirven para construir el conjunto; la recuperación híbrida no es una prueba de que el resultado resuelva la acción.
4. Se deduplican contenidos y se filtran candidatos por algunas categorías temáticas (por ejemplo, finanzas frente a asuntos académicos). El metadato audience existe en el índice, pero **no se usa como filtro por rol**. El rol no impide consultar documentos complementarios de otras audiencias.
5. Cross-Encoder reordena hasta 80 candidatos. Su salida es una señal de orden, no un score de confianza universal ni un umbral certificado para responder.
6. Selector de anclas aprovecha la relación entre pregunta/variantes y nombre de fuente, además del reranking. En consultas que tienen selectores dedicados (credenciales, elecciones u otros flujos documentados) se aplican reglas específicas de evidencia.
7. La selección final ya no descarta chunks por una estimación aproximada de tokens. Conserva un tope por cantidad: hasta 16 anclas y 24 chunks finales para consultas procedimentales/contexto extendido, y hasta 4 anclas y 8 chunks finales para consultas directas. Como cada chunk puede tener distinta longitud, el consumo real de tokens varía; se registra para observabilidad, no se usa para truncar el contexto.
8. El expansor trata de incluir un chunk inmediatamente anterior y posterior del mismo documento, incluso en página/diapositiva adyacente, cuando los IDs deterministas y metadatos permiten verificar la secuencia.
9. El ajustador de contexto admite primero las anclas rerankeadas, después los vecinos si hay espacio, y vuelve a ordenar por documento/página/chunk. El estimador es len(texto)/3, una aproximación; no es el tokenizer exacto del modelo.
10. Cada bloque enviado al generador conserva el nombre de fuente y página cuando hay metadatos.

### Instrucciones que recibe el generador

El prompt central está en STRICT_SYSTEM_PROMPT_TEMPLATE dentro de rag_service.py y se arma en cada llamada con pregunta, historial reciente, rol conversacional y contexto RAG. En términos funcionales exige:

- actuar como soporte TI de primera línea UniMon, con lenguaje empático y pasos accionables;
- responder la acción concreta y todas sus partes, no una tarea cercana que comparte palabras;
- no inventar URL, botón, ruta, permiso, requisito, contraseña, plazo ni canal no respaldado;
- limitar acciones a las que la persona esté autorizada a realizar en su cuenta/equipo;
- indicar lo que no pudo verificarse y ofrecer aclaración/escalamiento cuando falte evidencia;
- tratar el texto recuperado como evidencia documental, nunca como instrucciones que cambien las reglas del sistema.

Antes y después del LLM hay reglas fuera del prompt: sanitización de entrada, detección de inyección y fuera de dominio, interceptores académicos/de trámite, selectores por intención y clean_llm_response para limpiar formato/links/contactos. No son una verificación lógica formal de cada afirmación; evaluar con los documentos originales sigue siendo necesario.

Los máximos anteriores son límites, no cantidades garantizadas. El número real depende de cuántos candidatos sobrevivan, cuánto texto tengan, metadatos, deduplicación, relevancia, vecino encontrado y presupuesto. Una consulta no debería recibir vecinos de otro documento solo por compartir términos.

### 3.3 Qué significan los chunks y el overlap

Un chunk es una porción de texto que se vectoriza y recupera como unidad. El overlap de 150 caracteres repite el final de un chunk al inicio del siguiente para que una frase o paso que cruce el corte conserve continuidad. No crea información nueva y puede duplicar texto/candidatos. Más overlap aumenta almacenamiento, duplicados y similitud entre segmentos; menos overlap reduce contexto en límites.

El script scripts/audit_overlap_rates.py mide redundancia existente con la métrica real de la colección; incluye conversión de distancia correcta para L2. El resultado de data/rag_overlap_calibration_latest.json es un dato de diagnóstico, no una política automática de eliminación. No habilites deduplicación solo porque dos fragmentos tengan alta similitud: mide tasa, inspecciona pares y verifica consultas de evaluación.

### 3.4 Validación de recuperación

scripts/evaluate_rag_retrieval.py y scripts/trace_coloquial_100_retrieval.py registran candidatos, orden rerankeado y contexto final frente a una fuente esperada. Los scripts load_test_* ejercitan además el endpoint real y respuestas LLM. La promoción por scripts/promote_quality_to_golden.py requiere una evaluación marcada correcta y fuente final alineada; un feedback de usuario aislado no equivale a una auditoría independiente.

Última medición documentada en este repositorio, 6-oct-2026: 50 sesiones liberadas simultáneamente, 50 respuestas HTTP exitosas, cero respuestas 429/5xx, fuente esperada en 49 de 49 respuestas comprobables. El evaluador calificó 25 correctas, 14 parciales, 9 incorrectas y 2 no verificables (50% de exactitud estricta). Latencia p50 65,1 s, p95 70,7 s, máximo 85,9 s. Es una medición local/configurada, no un SLA ni prueba de redes físicas diversas. No demuestra la meta de 90%.

## 4. Conversación, diagnóstico y tickets

- Las sesiones y su historial se guardan en diccionarios Python en memoria; se purgan por inactividad mayor a 20 minutos y el ciclo de limpieza corre cada 5 minutos.
- Reiniciar el proceso pierde el estado conversacional. Varias réplicas/worker independientes no comparten memoria: sin almacenamiento compartido y afinidad de sesión, un turno puede llegar a otro proceso sin contexto.
- El clasificador conversacional encamina mensajes a autoservicio, falla física, límites académicos, respuesta de regla y acciones de ticket. Su clasificación no modifica el corpus.
- Una falla común puede recibir diagnóstico y botones. En hardware o problemas que exijan visita, la aplicación puede ofrecer escalamiento; los pasos sugeridos no autorizan abrir equipos, manipular cableado ni intervenir infraestructura.
- El flujo de GLPI puede pedir nombre, correo y descripción. Puede comprobar casos activos del día y preguntar si se agrega un seguimiento o se abre otro ticket. La confirmación y respuesta final dependen de disponibilidad/configuración externa.
- GLPI usa GLPI_BASE_URL, GLPI_APP_TOKEN, GLPI_USER_TOKEN y timeout. El cliente abre/cierra sesiones de API y puede consultar resúmenes/seguimientos. Sin credenciales válidas no crea un ticket real.
- El estado de conversación, el código HTTP 200 y la fuente RAG no prueban por sí solos que la respuesta esté resuelta correctamente.

~~~mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> DIAGNOSTICO: consulta con contexto utilizable
    IDLE --> OFRECIENDO_RADICACION: falla física, regla directa o falta evidencia
    DIAGNOSTICO --> DIAGNOSTICO: nueva consulta o reintento permitido
    DIAGNOSTICO --> FINALIZADO: persona confirma resolución
    DIAGNOSTICO --> PIDIENDO_NOMBRE: solicita ticket o escala
    OFRECIENDO_RADICACION --> PIDIENDO_NOMBRE: persona confirma radicación
    OFRECIENDO_RADICACION --> IDLE: cancela o inicia conversación aparte
    PIDIENDO_NOMBRE --> PIDIENDO_CORREO: no incluye correo válido
    PIDIENDO_NOMBRE --> PIDIENDO_DESCRIPCION: nombre y correo válidos
    PIDIENDO_CORREO --> PIDIENDO_DESCRIPCION: correo válido
    PIDIENDO_DESCRIPCION --> CONFIRMANDO_SEGUIMIENTO: hay caso previo del día
    PIDIENDO_DESCRIPCION --> TICKET_CREADO: GLPI acepta alta nueva
    CONFIRMANDO_SEGUIMIENTO --> ESCRIBIENDO_SEGUIMIENTO: elige agregar avance
    CONFIRMANDO_SEGUIMIENTO --> TICKET_CREADO: elige un caso nuevo y GLPI lo acepta
    ESCRIBIENDO_SEGUIMIENTO --> FINALIZADO: GLPI acepta seguimiento
    TICKET_CREADO --> IDLE: la implementación limpia la sesión después del resultado
    FINALIZADO --> IDLE: la persona inicia otro tema
~~~

PIDIENDO_ROL permanece como estado de compatibilidad/transición, pero IDLE normalmente asigna general y deja escribir sin selección obligatoria. PIDIENDO_UBICACION y PIDIENDO_ACTIVO aparecen como valores de compatibilidad del enum; el flujo actual estándar de ticket pide nombre, correo y descripción, no esos campos obligatoriamente.

### Golden Cache

La colección `golden_resolved_qa` de UniMon vive por defecto bajo `data/chroma_db`; cada asistente adicional guarda otra colección bajo su carpeta `golden_cache`. Las interacciones pueden guardarse después de feedback positivo si pasan validaciones sintácticas y de anomalías; la valoración no certifica documentalmente la respuesta. En UniMon, la referencia previa amplía la búsqueda, pero los hechos oficiales deben provenir de los documentos recuperados. Las instancias registran feedback y consultan solo su propia memoria; una coincidencia puede añadirse como referencia secundaria al generador incluso si no hubo chunks documentales. Por ello, una respuesta con caché no acredita fundamentación documental. Hay scripts de evaluación/promoción para registrar respuestas juzgadas y respaldadas. Revisa y purga entradas anómalas con `scripts/clean_golden_cache.py`.

La búsqueda predeterminada pide una coincidencia de similitud coseno de al menos 0.90 y valida compatibilidad de intención/anomalías antes de devolverla. La escritura usa hash de rol+pregunta para upsert, pero la llamada actual de búsqueda no pasa rol como filtro; no usar el rol del índice Golden como control de autorización.

## 5. Proveedores LLM y modelos

LLM_PROVIDER selecciona anthropic, gemini, openai u ollama para UniMon. Las instancias pueden configurar además un endpoint personalizado compatible con Anthropic Messages API o el formato de chat de OpenAI. La opción activa, claves, endpoint y timeouts vienen de Settings/.env; .env.example no es la configuración real. El valor por defecto del código y el archivo de ejemplo no coinciden en todos los campos, por lo que el practicante debe verificar .env y /api/admin/system-status. `/health` solo confirma que responde la aplicación.

- OpenAI: OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL, OPENAI_TIMEOUT.
- Anthropic: ANTHROPIC_API_KEY, ANTHROPIC_MODEL, ANTHROPIC_BASE_URL, ANTHROPIC_TIMEOUT.
- Gemini: GEMINI_API_KEY, GEMINI_MODEL, GEMINI_BASE_URL, GEMINI_TIMEOUT.
- Ollama: OLLAMA_BASE_URL, LLM_MODEL, OLLAMA_TIMEOUT.
- La generación de conversación intenta el proveedor cloud y el código actual puede hacer fallback a Ollama si falla o falta la clave. Los métodos auxiliares de generación también tienen contingencia local. No asumas modo cloud exclusivo solo porque LLM_PROVIDER diga openai o gemini.
- OpenAI para modelos GPT-5/6 envía max_completion_tokens y reasoning_effort low; la interfaz oculta el manejo de los proveedores.
- Visión documental intenta primero OpenAI `gpt-6-luna`, independientemente del proveedor del chat, y solo después prueba Ollama con `VISION_MODEL`. Necesita que al menos uno de esos servicios esté disponible para procesar imágenes sin omitirlas.
- Modelos de embeddings y Cross-Encoder se cargan localmente con archivos del cache de Hugging Face. En equipos nuevos hay que descargar esos modelos previamente; el primer inicio no necesariamente puede obtenerlos por sí solo.

Modelfile define un modelo Ollama local heredado basado en llama3.1:8b. No controla la instrucción central del prompt escrita en rag_service.py. Revísalo antes de asumir que sus reglas son la fuente efectiva o que coinciden con el proveedor cloud.

## 6. Configuración

No copies ni publiques secretos. En un entorno nuevo copia .env.example a .env y asigna credenciales propias. Configuración disponible:

| Clave | Uso |
|---|---|
| ENVIRONMENT, PORT, HOST, DEBUG | Ambiente y servidor. El run.ps1 admite parámetros propios de host y puerto. |
| ADMIN_USERNAME, ADMIN_PASSWORD | HTTP Basic para panel y endpoints protegidos. El password vacío hace que el admin falle cerrado. Usa uno único y fuerte. |
| GLPI_BASE_URL, GLPI_APP_TOKEN, GLPI_USER_TOKEN, GLPI_TIMEOUT | API de GLPI. |
| LLM_PROVIDER | anthropic, gemini, openai u ollama. |
| ANTHROPIC_API_KEY, ANTHROPIC_MODEL, ANTHROPIC_BASE_URL, ANTHROPIC_TIMEOUT | Proveedor Anthropic. |
| OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL, OPENAI_TIMEOUT | Proveedor OpenAI. |
| GEMINI_API_KEY, GEMINI_MODEL, GEMINI_BASE_URL, GEMINI_TIMEOUT | Proveedor Gemini. |
| OLLAMA_BASE_URL, LLM_MODEL, OLLAMA_TIMEOUT | Generación/fallback local. |
| VISION_MODEL, VISION_TIMEOUT, VISION_MAX_IMAGE_SIZE | Modelo de contingencia Ollama, espera y resolución máxima de imágenes durante la ingesta; la ruta primaria de visión usa OpenAI `gpt-6-luna` si existe `OPENAI_API_KEY`. |
| CHROMA_DB_DIR | Índice de documentos RAG, por defecto ./chroma_db. |
| GOLDEN_CACHE_DB_DIR | Índice separado de Golden Cache, por defecto ./data/chroma_db. |
| DOCS_DIR | Corpus fuente, por defecto ./data/docs. |
| EMBEDDING_MODEL | Modelo E5 de embeddings, valor configurado multilingual-e5-large. |
| MAX_UPLOAD_SIZE_MB | Tamaño máximo de la ruta de carga simple que lo aplica. No todos los endpoints de carga hacen la misma validación. |
| WHATSAPP_ENABLED, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_WABA_ID, WHATSAPP_ACCESS_TOKEN | Habilitación e identidad del canal Meta. |
| WHATSAPP_VERIFY_TOKEN, WHATSAPP_APP_SECRET, WHATSAPP_API_VERSION | Validación del webhook, firma cuando se configura y versión Graph API. |

La API pública tiene rate limit global predeterminado de 30 solicitudes/minuto por clave configurada. Comportamiento detrás de proxy depende de cómo se ejecute Uvicorn y de qué cabecera use el rate limiter; no aceptes una cabecera de IP no confiable como control de seguridad.

## 7. Mapa de API

Consulta `/docs` para el esquema FastAPI en desarrollo; en `ENVIRONMENT=production` se deshabilitan `/docs`, `/redoc` y `/openapi.json`.

| Método y ruta | Función |
|---|---|
| GET / | Sirve app/static/index.html. |
| GET /health | Indica que la aplicación responde; no comprueba GLPI, proveedores LLM ni el índice de cada dependencia. |
| POST /api/chat | Mensaje conversacional. Campos: mensaje/message y session_id. |
| GET /api/chatbots/{bot_id}/config | Nombre y saludo público de una instancia adicional habilitada. |
| POST /api/chatbots/{bot_id}/chat | Consulta RAG aislada para una dependencia. Conserva sesión y Golden Cache propias, sin utilizar las de UniMon. |
| GET /api/chatbot-router/config, POST /api/chatbot-router/chat | Modo opcional `/?router=1`: clasifica con alcances y catálogos de documentos elegibles; delega a una instancia o usa UniMon como fallback. |
| GET /api/admin/chatbot-instances | Lista instancias, perfiles de especialidad y métricas filtradas; requiere autenticación administrativa. |
| POST /api/admin/chatbot-instances | Crea una instancia y sus directorios aislados; requiere autenticación administrativa. |
| PATCH /api/admin/chatbot-instances/{bot_id} | Edita nombre, dependencia, alcance y contactos sin cambiar el identificador. |
| DELETE /api/admin/chatbot-instances/{bot_id}, POST /api/admin/chatbot-instances/{bot_id}/reactivate | Desactiva/reactiva una instancia conservando sus documentos e índice. |
| GET /api/admin/chatbot-instances/{bot_id}/metrics | Devuelve consultas, sesiones, tokens y latencia por instancia y período. |
| POST /api/admin/chatbot-instances/{bot_id}/documents/audit | Convierte PDF/PPTX/DOCX, comprueba fidelidad con el original y compara los chunks con el índice privado; deja el resultado en staging sin indexar. |
| POST /api/admin/chatbot-instances/{bot_id}/documents/resolve | Acepta, reemplaza o descarta la carga auditada; solo indexa un Markdown con fidelidad confirmada. |
| POST /api/admin/chatbot-instances/{bot_id}/documents | Ruta directa compatible para PDF/PPTX/DOCX; conserva el original aunque falle la indexación. El panel vigente usa `audit` y `resolve` incluso al pulsar «Convertir e indexar». |
| GET /admin, GET /admin.html | Panel administrativo; protegido por HTTP Basic desde admin_router. |
| GET /api/admin/docs | Lista fuentes en el directorio documental. |
| POST /api/admin/upload-doc | Sube a subcarpeta/audiencia; puede auditar/indexar según banderas. Verifica formato e indexación antes de darlo por disponible. |
| POST /api/admin/audit-doc | Preauditoría de duplicidad/ambigüedad. |
| POST /api/admin/resolve-upload | Resuelve staging como replace, deduplicate, force o cancel. |
| POST /api/admin/reindex | Recorre el corpus compatible e intenta taxonomía; wipe_db borra el índice activo después de intentar backup. |
| DELETE /api/admin/docs/{filename} | Elimina fuente y trata de purgar sus chunks. |
| GET /api/admin/system-status | Diagnóstico de proveedor, Chroma, telemetría y servicios disponibles. |
| GET /api/analytics/kpis | Resumen de métricas con fecha opcional; HTTP Basic requerido por el router. |
| GET /api/analytics/unresolved-queries | Ranking de preguntas no resueltas; HTTP Basic requerido por el router. |
| POST /api/analytics/unresolved-queries/dismiss | Descarta una consulta; HTTP Basic requerido. |
| GET /api/analytics/unresolved-queries/dismissed | Lista consultas descartadas; HTTP Basic requerido. |
| POST /api/analytics/unresolved-queries/restore | Restaura consulta al ranking; HTTP Basic requerido. |
| GET /api/analytics/compare | Compara períodos de KPIs; HTTP Basic requerido por el router. |
| GET /api/analytics/ai-insights | Genera resumen/insights; HTTP Basic requerido por el router. |
| POST /api/analytics/draft-procedure | Genera un borrador sin indexarlo; HTTP Basic requerido por el router. |
| POST /api/analytics/save-procedure | Guarda e indexa un procedimiento; HTTP Basic requerido. |
| GET /api/analytics/export-unresolved-csv | Exporta preguntas sin resolver; HTTP Basic requerido. |
| GET /api/analytics/clusters | Devuelve clusters/temas; HTTP Basic requerido por el router. |
| GET /api/analytics/export-dpo-dataset | Exporta JSONL DPO; HTTP Basic requerido. |
| POST /api/analytics/reset-metrics | Destructivo para telemetría; HTTP Basic requerido. Puede solicitar también limpiar Golden Cache. |
| POST /api/admin/upload y POST /api/admin/reindex | Rutas compatibles heredadas definidas también en chat.py; tienen auth y sus propios límites/formatos. |
| GET/POST /api/whatsapp | Handshake GET y recepción webhook POST. |
| GET /api/whatsapp/status | Resumen de credenciales/estado; trata su salida como dato operativo. |
| /static/* | Assets estáticos si el directorio existe. |

Hay rutas repetidas de administración heredadas en routers distintos. No asumas que todas aceptan el mismo formato, límite, staging o comportamiento. El router de analítica aplica HTTP Basic a todas sus rutas; el control de origen también se ejecuta en operaciones mutantes. Swagger muestra el contrato activo; esta tabla describe su propósito, no reemplaza la revisión de autenticación de cada endpoint.

## 8. Persistencia y carpetas de datos

| Ubicación | Contenido | No contiene |
|---|---|---|
| data/docs | Archivos fuente que deben gobernarse, corregirse y reindexarse. | Garantía de que todos los formatos presentes sean indexables. |
| chroma_db | Índice vectorial del RAG. | Fuente autoritativa de procedimientos; puede reconstruirse desde las fuentes compatibles. |
| data/chroma_db | Índice separado de Golden Cache por defecto. | Corpus de documentos institucionales. |
| data/chatbots/unimon/specialization.json y .md | Catálogo de metadatos documentales para elegir UniMon en el router; se reconstruye desde los Markdown elegibles. | Cuerpo íntegro de procedimientos o índice RAG. |
| data/chatbots/instances/<identificador> | Originales, Markdown, manifiesto, índice RAG, Golden Cache y catálogo aislados de cada dependencia; `instances.sqlite3` conserva su configuración. | Sesiones persistentes entre reinicios. |
| data/analytics.db | Historial de telemetría, consultas, etiquetas, métricas y datos de tickets. | Estado persistente de TicketSession. |
| data/.vision_cache.json | Descripciones cacheadas de imágenes calculadas durante ingesta. | Índice final de búsqueda. |
| data/chroma_db_backup, chroma_db_backup | Respaldos de Chroma de distintas ubicaciones/revisiones. | Copia garantizada de configuración y corpus sincronizados; verifica cuál corresponde al entorno. |
| data/scratch/staged_uploads | Subidas en espera de revisión/resolución administrativa. | Fuentes activas hasta que se acepten e indexen. |
| reports | Carpeta local para los resultados nuevos de evaluaciones y pruebas; solo se versiona su README. | Dependencia del runtime o conservación de informes históricos. |
| scratch | Archivos temporales, scripts de trabajo y logs locales. | Artefactos necesarios para arrancar. |

No borres ni sobrescribas un índice o analytics.db activo sin validar respaldo, ruta en .env y proceso detenido.

## 9. Instalación y operación

La guía reproducible y el inventario fichero por fichero están en [REPLICAR_Y_OPERAR_UNIMON.md](REPLICAR_Y_OPERAR_UNIMON.md). En resumen:

~~~powershell
.\setup.ps1
# Editar .env: reemplazar placeholders y configurar proveedor/credenciales.
.\run.ps1
~~~

Comprobaciones posteriores: /health, /docs, acceso web, consulta sencilla, consulta procedimental con respuesta/fuentes, health de admin y flujo de ticket sólo en entorno de prueba controlado.

Carga de corpus:

~~~powershell
.\.venv\Scripts\python.exe scripts\ingest_multimodal_docs.py
.\.venv\Scripts\python.exe scripts\apply_document_taxonomy.py
~~~

El procesamiento de imágenes usa primero OpenAI `gpt-6-luna` cuando está configurado y Ollama como último recurso. La ingesta admite PDF/PPTX/DOCX, pero no XLSX; si una imagen no puede interpretarse por ninguno de los dos servicios, se detiene la extracción de ese documento. En una base existente, consulta los argumentos del script antes de elegir incremento, reemplazo o wipe. No uses wipe en un entorno con datos que no puedas regenerar.

## 10. Observabilidad, pruebas y mantenimiento

- Logs: consola; opcionalmente run.ps1 -CaptureLogs escribe scratch/unimon-runtime.log. Trátalo como dato sensible.
- KPIs y errores de recuperación: /admin y /api/analytics según autenticación de cada ruta.
- Pruebas automatizadas: `pytest.ini` señala `tests`. Ejecuta pruebas solo en un entorno dedicado; las pruebas de reglas GLPI sustituyen la API externa y no demuestran un ticket creado en el servidor institucional. Valida la contingencia cloud→Ollama y la carga de documentos con pruebas controladas del entorno antes de declarar disponibilidad operativa.
- Revisión documental real: conserva query, candidates, reranked, final_context y documento esperado; evalúa contenido además de HTTP 200.
- Carga: scripts/load_test_quality_50.py ofrece --concurrency 1..50; cada consulta usa sesión independiente.
- Solapamiento: primero scripts/audit_overlap_rates.py y consulta su reporte. No activar deduplicación global sin medir precisión/recobrado.
- Actualiza este manual cuando cambien settings, rutas, formatos, límites, flujos o dependencias.

## 11. Seguridad y límites conocidos

- .env, credenciales Meta/GLPI, texto de consulta, analytics.db, logs y reportes pueden ser sensibles. No copiarlos en commits, capturas o documentos.
- El admin requiere ADMIN_USERNAME/ADMIN_PASSWORD válidos; la protección actual usa HTTP Basic. La aplicación limita tamaño en algunas rutas, pero el endpoint administrativo heredado y el endpoint nuevo tienen validaciones distintas; revisa antes de exponer públicamente.
- CORS y cabeceras de seguridad están definidos en main.py; no constituyen por sí solos una estrategia completa de producción.
- Rate limit no reemplaza autenticación, proxy confiable, monitoreo de cuotas, protección contra abuso ni revisión de los endpoints analíticos.
- Las sesiones están en RAM y hay una protección periódica TTL. Persistencia distribuida, balanceo multiinstancia y tareas largas escalables requieren diseño adicional.
- No considerar el reranker, Golden Cache o la respuesta positiva como validador de verdad. Usar documentos y evaluación etiquetada.
- Los documentos pueden contradecirse o estar obsoletos. La aplicación extrae y recupera texto; no comprueba vigencia institucional automáticamente.

## 12. Asistentes adicionales por dependencia

El administrador puede crear instancias desde **Diagnóstico de Servidor** en `/admin`. Cada instancia tiene un identificador, nombre, alcance, canales de soporte y rutas propias para originales, Markdown, ChromaDB y Golden Cache. La carga del panel sigue PDF/PPTX/DOCX → Markdown → cotejo de fidelidad y posible corrección → análisis de similitud en su índice → confirmación → chunks e índice. Si la auditoría queda en `revisar` o `no_verificable`, no se indexa. El resultado automatizado orienta la revisión humana; no prueba que cada dato del Markdown sea correcto.

Las nuevas instancias consultan solo su índice y guardan proveedor/modelo LLM de forma independiente. Las credenciales de proveedores incorporados permanecen en `.env`; las claves de endpoints personalizados se cifran en el registro de la instancia con una clave maestra configurada. Embeddings y reranker se comparten por el servidor. No usan GLPI ni la Golden Cache de UniMon: guardan sus propios casos valorados. Su catálogo `specialization.json`/`.md` contiene metadatos de Markdown elegibles; el router usa fichas pertinentes y el alcance declarado para elegir entre dependencias y UniMon. El chat se abre con `/?bot=<identificador>`, y el router opcional en `/?router=1`. Configuración, límites y respaldo están en [CHATBOTS_POR_DEPENDENCIA.md](CHATBOTS_POR_DEPENDENCIA.md).

