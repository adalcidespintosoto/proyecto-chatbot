# Replicar y operar UniMon: guía para el próximo practicante

**Revisión del repositorio:** 6 de octubre de 2026.  
**Objetivo:** permitir que una persona nueva entienda qué hay en el repositorio, prepare un entorno aislado, arranque UniMon, actualice el corpus, pruebe recuperación y reconozca qué componentes requieren configuración institucional.

Empieza por [Manual de usuario](MANUAL_DE_USUARIO.md) para el comportamiento visible y [Manual técnico integral](MANUAL_TECNICO_INTEGRAL.md) para arquitectura y límites. El [flujo de procesamiento](flujo_procesamiento_sistema.md) resume el recorrido por capas.

## 1. Antes de replicar

### Qué necesitas pedir a quien entrega el proyecto

- Acceso autorizado al repositorio y a una versión estable del corpus documental.
- Credenciales propias de prueba para un proveedor LLM (OpenAI, Gemini u Ollama) si se harán respuestas reales.
- Acceso de prueba separado para GLPI si se probará radicación; no uses tickets reales de usuarios.
- Configuración de Meta WhatsApp solo si se desplegará ese canal.
- Claves nuevas para el panel admin y webhook verify token.
- Confirmación del modelo de embeddings/reranker y política de red del laboratorio.

El archivo .env local no debe copiarse al repositorio, al manual, al chat ni a un equipo personal. Solicita secretos por el mecanismo institucional. Nunca uses datos de usuarios reales en pruebas.

### Requisitos observados

- Python 3.10 o superior por código/requirements; para reproducibilidad usa la versión aprobada por TI y crea un venv nuevo. El setup está escrito para Windows PowerShell.
- Git y PowerShell en Windows si usarás setup.ps1/run.ps1.
- Conectividad a la API configurada, o un servidor Ollama local para generación/fallback.
- Caché local de Hugging Face para multilingual-e5-large y cross-encoder/ms-marco-MiniLM-L-6-v2. El código configura carga local de estos modelos; en equipo nuevo descarga/cachea antes de arrancar.
- GPU CUDA mejora la ingesta/modelos si hay soporte; CPU puede funcionar con más memoria/latencia. La ingesta visual necesita Ollama local y un modelo de visión disponible.
- Espacio para corpus, embeddings, pesos locales y bases persistentes.

CrewAI/LangGraph no son requisitos. LangChain sí se usa en componentes de parsing, Document, splitter e integración Chroma.

## 2. Preparación en Windows

Clona el proyecto desde la URL institucional que te proporcione el responsable; no deduzcas ni publiques la URL del repositorio.

~~~powershell
git clone <URL_AUTORIZADA>
Set-Location proyecto-chatbot
.\setup.ps1
~~~

setup.ps1 crea .venv si falta, actualiza pip, instala requirements.txt y copia .env.example a .env si todavía no existe. No crea credenciales válidas ni descarga automáticamente el corpus o todas las ponderaciones del modelo.

Edita .env sin compartirlo. Configura al menos:

- ADMIN_USERNAME y una contraseña única larga.
- LLM_PROVIDER y la clave correspondiente para el proveedor, o los requisitos Ollama.
- GLPI tokens solo si pruebas con un GLPI autorizado.
- DOCS_DIR, CHROMA_DB_DIR, GOLDEN_CACHE_DB_DIR si usarás rutas diferentes.
- Variables WhatsApp solo para ese canal.

En esta revisión .env.example elige OpenAI, mientras Settings en app/config.py tiene Gemini como valor por defecto si no existe esa variable. run.ps1 también contiene valores de detección propios. La autoridad al ejecutar es el entorno efectivo cargado; revisa /health y /api/admin/system-status. No interpretes un .env.example como el estado real.

Descarga los dos modelos locales en el cache usado por sentence-transformers antes del primer arranque si no están ya disponibles:

~~~powershell
.\.venv\Scripts\python.exe -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('intfloat/multilingual-e5-large'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"
~~~

Si se usará fallback, instala Ollama, descarga el modelo de chat configurado y valida que sea accesible. Para ingesta visual verifica VISION_MODEL aparte. Modelfile parte de llama3.1:8b y crea unimon:8b; no se confunde con el modelo de visión ni con el modelo del proveedor principal.

## 3. Corpus e índice desde cero

### Regla de formatos

La ruta principal scripts/ingest_multimodal_docs.py recorre data/docs y procesa PDF/PPTX. Convierte DOCX/XLSX a un formato aprobado que conserve tablas/páginas o amplía los parsers de manera probada antes de contar esos cuatro archivos como conocimiento del chatbot. La carga web nueva acepta extensiones más amplias para auditoría/guardado, pero no significa que el indexador las procese. Revisa resultados de ingestión por archivo.

El corpus contiene un PDF bajo data/docs/1_estudiantes/test_dedup_doc.pdf, cuyo nombre identifica un artefacto de prueba. Está debajo del DOCS_DIR y la búsqueda recursiva lo incluye; sácalo del corpus operativo o confirma con responsable que debe estar indexado.

### Indexación

Con un corpus aprobado en DOCS_DIR y modelos disponibles:

~~~powershell
.\.venv\Scripts\python.exe scripts\ingest_multimodal_docs.py --help
.\.venv\Scripts\python.exe scripts\ingest_multimodal_docs.py
.\.venv\Scripts\python.exe scripts\apply_document_taxonomy.py
~~~

El modo incremental es el valor por defecto y normalmente solo agrega archivos que no encuentra por nombre. No equivale a actualizar automáticamente un documento del mismo nombre que cambió; usa el flujo de reemplazo y comprueba que los chunks previos se purgaron.

Para reindexar o cambiar el índice:

1. Detén el servidor para evitar consultas en mitad de la operación.
2. Copia corpus fuente, .env con custodia segura e índice Chroma a un respaldo con fecha.
3. Decide entre el endpoint de reindexación incremental, una acción del panel o CLI.
4. Usa --wipe únicamente si quieres reconstruir todo y tienes las fuentes/copia restaurable. El script elimina el backup anterior del mismo nombre antes de escribir el nuevo, por lo que conserva solo una copia rotativa.
5. Corre taxonomía, recarga vector store y captura estadísticas/logs.
6. Ejecuta evaluación de recuperación con fuente esperada y prueba la respuesta completa.
7. Si falló, detén servidor y restaura el respaldo comprobando que CHROMA_DB_DIR apunta a esa ubicación.

El área data/chroma_db es la Golden Cache, no el índice de manuales. No reemplaces una base con la otra.

## 4. Arranque y comprobación rápida

~~~powershell
.\run.ps1
~~~

El script verifica .venv, intenta resolver el proveedor cloud configurado o Ollama, muestra IP LAN y GPU e inicia Uvicorn en modo reload. Admite los parámetros -Port, -HostIP, -Tunnel y -CaptureLogs. El túnel es exposición de red: úsalo solo con autorización institucional y durante la ventana necesaria. --reload es para desarrollo; no es administrador de procesos de producción.

En navegador:

1. GET /health: debe devolver status healthy, proveedor/modelo elegido e indicadores de configuración.
2. GET /docs: muestra el OpenAPI del proceso activo.
3. GET /: abre chat web.
4. GET /admin: solicita HTTP Basic si el admin está configurado.
5. GET /api/admin/system-status: inspecciona dependencias configuradas. No publiques la salida si incluye datos internos.
6. Pregunta una consulta sencilla y una procedimental conocida. Comprueba mensaje, fuentes, páginas y logs.

No concluyas “está bien” con solo HTTP 200: para RAG revisa que el documento esperado aparezca en candidates, reranked y final_context, y juzga que los pasos contesten la acción correcta.

## 5. Flujo para agregar o corregir documentos

1. Obtén la versión vigente del área dueña del procedimiento.
2. Confirma audiencia prevista, fecha/versión, duplicados, sede, capturas sensibles y autorización de uso.
3. Comprueba que sea PDF o PPTX para que el ingestor principal lo procese.
4. Desde /admin utiliza listado, auditoría y resolución de carga o ejecuta una carga controlada. replace elimina contenido anterior; deduplicate omite contenido que la métrica considere repetido; force agrega contenido sin filtro; cancel descarta staging.
5. Lee los logs: archivos extraídos, páginas/diapositivas, imágenes interpretadas, fallos, chunks generados/descartados y total Chroma.
6. Recarga o reinicia servicio si el proceso conservaba una instancia antigua de colección.
7. Corre evaluación con preguntas de ese flujo y preguntas de regresión ajenas al cambio.
8. Confirma que las respuestas no mezclen tareas homónimas y que no inventen permisos/pasos.

No deduplicar manuales parecidos en bloque sin revisar los pares. El documento similar puede ser anexo complementario o pertenecer a otro rol/sistema. No asignes audience suponiendo que el RAG filtra por rol: hoy el metadato no aplica ese filtro.

## 6. Sesiones, telemetría y escalado

Las sesiones web usan un identificador guardado en sessionStorage por pestaña. El servicio tiene sesiones en memoria con limpieza TTL a los 20 minutos. En WhatsApp el número participa en la identidad de sesión y Meta puede repetir webhooks; el servicio conserva IDs procesados en memoria por hasta 10 minutos. Al reiniciar, las sesiones y deduplicación se pierden.

data/analytics.db es telemetría operativa local. Puede contener preguntas, respuestas, fuentes, tiempos, rol, tokens, estado/tickets y PII. No la envíes en una incidencia o repositorio público; administra retención/acceso con TI. Las conversaciones no se reconstruyen de esa base como memoria activa del chatbot.

Para probar tickets usa un GLPI de pruebas. El flujo de atención puede pedir nombre, email y descripción y consultar tickets del día. Comprueba que ticket_id real existe en ese servidor antes de informar éxito. Nunca simules una radicación al usuario ni afirmes que una llamada POST se completó si GLPI no respondió.

## 7. Evaluación técnica y Golden Cache

### Recuperación sin generación

~~~powershell
.\.venv\Scripts\python.exe scripts\evaluate_rag_retrieval.py --help
.\.venv\Scripts\python.exe scripts\evaluate_rag_retrieval.py --output reports\mi_evaluacion.json
~~~

La fixture está en tests/fixtures/rag_retrieval_eval.json. Cada fila contiene consulta y fuente esperada. La salida captura candidates, reranked y final_chunks. Inspecciona la fuente, la página, similitud/reranker y si todos los fragmentos necesarios llegan al contexto.

### Endpoint real y carga

~~~powershell
.\.venv\Scripts\python.exe scripts\load_test_quality_50.py --help
.\.venv\Scripts\python.exe scripts\load_test_quality_50.py --concurrency 50 --output reports\mi_carga_50.json
~~~

Este script tiene 50 preguntas distintas, sesión independiente por pregunta, concurrencia configurable de 1 a 50, latencia por solicitud, fallos HTTP y fuente esperada. Concurrency 50 puede elevar la latencia; no es lo mismo que 10 concurrentes. Las IP en X-Forwarded-For son simuladas y no equivalen a 50 redes físicas.

Los scripts de revisión usan un LLM como juez para apoyar la calificación. Sus etiquetas no son un oráculo: confirma errores con lectura del prompt, chunks exactos y documentos originales. No ajustes reglas hasta poder describir una causa repetible, no solo un caso aislado.

### Admisión al Golden Cache

La señal “Sí” guarda automáticamente una interacción si validadores locales la aceptan; no hay revisión documental humana incorporada al botón. Por ello:

- No declares todo feedback positivo como verdad.
- Revisa fuentes y respuesta antes de promover una prueba.
- Usa scripts/promote_quality_to_golden.py para entradas correctas de un reporte cualificado.
- Mide consultas similares, diferencias de intención, falsos positivos y regresión antes/después.
- Cache aporta búsqueda/consulta similar; no es fuente institucional independiente en el prompt final.
- Si una respuesta fue mala, usa invalidación/purga y confirma que no quede en memoria o en el índice vectorial incorrecto.

### Métricas observadas el 6-oct-2026

La última corrida de 50 sesiones todas simultáneas registró 50/50 respuestas HTTP satisfactorias, 0 errores 429 y 0 errores 5xx, fuente esperada en 49/49 verificables, p50 65,1 s, p95 70,7 s y máximo 85,9 s. La evaluación estricta: 25 correctas, 14 parciales, 9 incorrectas, 2 no verificables (50%). Estos datos son una línea base en la máquina y configuración de esa prueba; la latencia requiere trabajo antes de afirmar que aguanta producción o experiencia fluida.

## 8. Qué contiene cada carpeta

### Carpetas de código de producto: app

| Archivo | Qué hace | Qué no hace |
|---|---|---|
| app/config.py | Declara Settings y carga variables de .env con Pydantic; get_settings usa caché singleton. | No almacena secretos por sí solo ni prueba todas las conexiones al cargar. |
| app/main.py | Crea FastAPI, middlewares CORS/headers/rate limit, inicia SQLite, modelos/index/cache y limpiador TTL; monta rutas y HTML. | No persiste sesiones distribuidas ni convierte la app en servicio productivo multiworker. |
| app/security.py | Valida HTTP Basic del admin con comparación resistente a timing y falla cerrado si faltan credenciales. | No gestiona usuarios/roles institucionales ni sesiones SSO. |
| app/routers/chat.py | Esquemas de request/response, sanitización, endpoint POST /api/chat, telemetría y rutas heredadas de upload/reindex. | No contiene el reranking ni aprueba la respuesta RAG. |
| app/routers/admin_router.py | Panel protegido, lista/audita/sube/resuelve/elimina documentos, reindexa y reporta estado. | Aceptar/guardar una extensión no significa que el parser principal la indexe. |
| app/routers/analytics.py | API de KPIs, consulta no resuelta, reportes, borradores y reset. | No todas las rutas tienen la misma dependencia de autenticación; revisar decorators. |
| app/routers/whatsapp.py | GET handshake, POST eventos y GET status Meta. | No envía la respuesta al usuario; delega a whatsapp_service. |
| app/services/router_logic.py | Estados por sesión, historial, reglas de diálogo, límites de dominio, ticket y conexión de RAG/cache/GLPI. | No usa memoria durable o compartida entre procesos. |
| app/services/router_service.py | Clasificación de intención, detección de hardware, respuestas rápidas, transiciones de feedback. | No busca en Chroma ni valida documentalmente una salida generativa. |
| app/services/rag_service.py | Expansión, filtros temáticos, retrieval vectorial/léxico, reranker, vecinos/presupuesto, prompt y salida RAG. | El score no demuestra verdad; no aplica audience como filtro por rol. |
| app/services/llm_client.py | Cliente unificado para OpenAI/Gemini/Ollama, tokens, timeouts y fallback local. | No elige si el trámite es autorizado; no asegura que cada respuesta sea correcta. |
| app/services/golden_cache_service.py | Valida pares, persiste/consulta/invalida la colección golden_resolved_qa. | Feedback del usuario no es verificación factual/humana. |
| app/services/normalizer_service.py | Normaliza jerga, cabeceras y sinónimos de consultas. | No corrige el contenido institucional original. |
| app/services/glpi_service.py | Cliente HTTP para autenticación, tickets, actores, estado y seguimiento. | Sin tokens válidos no puede operar GLPI; una respuesta del bot no prueba creación remota. |
| app/services/telemetry_service.py | Escribe/consulta analytics.db y produce KPIs, ranking y gestión de consultas. | No comparte session_history del router ni funciona como base de chat. |
| app/services/clustering_service.py | Agrupa consultas y exporta datasets/analítica semántica. | El clustering no clasifica automáticamente las respuestas como verdaderas. |
| app/services/whatsapp_service.py | Deduplica webhooks, convierte formato, procesa mensajes/eventos y envía respuestas a Meta. | El cache dedup/session es en RAM y se pierde al reiniciar. |
| app/services/__init__.py | Marca el paquete de servicios. | No implementa flujo. |
| app/routers/__init__.py | Marca el paquete de routers. | No registra rutas por sí solo; main.py los incluye. |
| app/__init__.py | Marca el paquete Python de UniMon. | No arranca el servidor. |
| app/utils/__init__.py | Marca el paquete de utilidades reservado. | Actualmente no contiene utilidades funcionales adicionales. |
| app/static/index.html | SPA web del usuario; chat, estado, quick replies y botón Nueva conversación con sessionStorage por pestaña. | No implementa recuperación, secretos ni lógica GLPI del backend. |
| app/static/admin.html | Panel de conocimiento, métricas y estado administrativo. | No reemplaza validación de autenticación del servidor. |

### Scripts ejecutables: scripts

| Archivo | Uso |
|---|---|
| ingest_multimodal_docs.py | PDF/PPTX a texto/chunks/embeddings/Chroma; maneja visión, caché visual, incremental, wipe, delete, auditoría de duplicidad. |
| apply_document_taxonomy.py | Calcula metadatos audience/doc_type/category por fuente y actualiza Chroma. Audience es metadata, no filtro RAG por rol. |
| update_chroma_metadata.py | Stub legado; imprime que apply_document_taxonomy.py lo reemplazó. |
| audit_overlap_rates.py | Mide redundancia/overlap de chunks y convierte distancia según la métrica Chroma detectada. |
| purge_orphan_chunks.py | Elimina chunks huérfanos que ya no corresponden a fuentes presentes; revisar argumentos/salida antes de ejecutar. |
| clean_golden_cache.py | Purga Golden Cache anómala o limpiable; no reconstruye documentación. |
| evaluate_rag_retrieval.py | Evalúa candidatos, reranking y contexto final contra fixture sin respuesta LLM real. |
| trace_coloquial_100_retrieval.py | Reproduce recuperación y registra etapas de consulta de pruebas coloquiales sin generar respuestas finales. |
| load_test_chat.py | Utilidad compartida de HTTP, casos, latencias, escritura de reportes para pruebas de carga. |
| load_test_quality_50.py | 50 preguntas de usuarios y fuentes esperadas, sesiones separadas y --concurrency 1..50. |
| load_test_coloquial_100.py | Prueba de 100 consultas en lotes simultáneos de 10; genera reportes de latencia/respuesta. |
| review_quality_50.py | Califica respuestas de la prueba de 50 frente a fuente/contexto; no promueve por sí solo al cache. |
| review_coloquial_100.py | Juzga las respuestas de prueba coloquial y puede preparar cache según sus validaciones. |
| promote_quality_to_golden.py | Promueve solo resultados correctos/grounded desde un reporte y su traza. |
| report_reranker_calibration.py | Cruza etiquetas de calidad con scores del reranker para estudiar umbrales. |
| reset_metrics.py | Reinicia los datos de telemetría; destructivo para analytics.db y requiere control del ambiente. |
| generate_docx_report.py | Produce informe comparativo RAG local/cloud en DOCX. |
| generate_request_docx.py | Genera solicitud formal de infraestructura/WhatsApp en DOCX. |

### Tests: tests

| Archivo | Cobertura |
|---|---|
| test_admin_panel.py | HTML del panel, auth override, listados, status, subida/eliminación y staging. |
| test_accuracy_boosters.py | Golden Cache, expansión, reranker, filtros de salida e integración de feedback. |
| test_architect_features.py | Cabeceras, sanitización, rate limit, rol/pendientes, diagnóstico y reglas GLPI. |
| test_clustering.py | Clusters, brecha de conocimiento, fallbacks y exportación. |
| test_domain_limits_and_elections.py | Límites académicos, elecciones, normalización y hardware. |
| test_incremental_ingest.py | Conversión L2, IDs deterministas, deduplicación y borrado/ingesta. |
| test_rag_retrieval_precision.py | Recuperación precisa y separación de intenciones en ejemplos. |
| test_role_quick_replies.py | Normalización de rol, botones y compatibilidad de metadatos. Sus expectativas de filtro deben contrastarse con el diseño actual de búsqueda global. |
| test_router_rules.py | Transiciones, feedback, retry, hardware y sanitización. |
| test_security_hardening.py | Autenticación, límites de carga, IP/rate limit y cabeceras. |
| test_telemetry_analytics.py | Esquema, KPIs, eventos, API y reset SQLite. |
| test_whatsapp_integration.py | Conversión de formato, handshake, status, eventos, deduplicación y flujo WhatsApp. |
| fixtures/rag_retrieval_eval.json | Casos de consulta y fuente esperada para evaluación de recuperación. |
| pytest.ini | Configura pytest: carpeta tests, pythonpath raíz y modo asyncio automático. |

Las pruebas son evidencia sobre el alcance implementado en ese momento, no sustituyen una prueba end-to-end con API/modelo/GLPI/Meta reales. Algunas descripciones heredadas de pruebas hablan de filtro de rol y deben actualizarse cuando se alineen tests a la decisión actual de búsqueda global.

### Documentación del proyecto: docs

| Archivo | Propósito |
|---|---|
| MANUAL_DE_USUARIO.md | Instrucciones para personas usuarias, límites, conversación y ticket. |
| MANUAL_TECNICO_INTEGRAL.md | Arquitectura, RAG, modelos, configuración, API, persistencia y riesgos. |
| REPLICAR_Y_OPERAR_UNIMON.md | Esta guía de instalación, operación y mapa de archivos. |
| flujo_procesamiento_sistema.md | Secuencia técnica resumida en diagrama. |
| COMPARATIVA_RAG_LOCAL_VS_CLOUD_GPT5.6.md | Comparativa de una evaluación anterior; los modelos, precios y resultado no son catálogo vigente. |
| PROMPT_TRANSFORMACION_DOCUMENTOS_RAG.md | Instrucción editorial para convertir procedimientos a texto útil de RAG; no se ejecuta al atender consultas. |
| PROMPT_TRANSFORMACION_A_PDF.md | Instrucción editorial de transformación/documentación; no es prompt de runtime. |
| Informe_Ejecutivo_Comparativa_RAG_Local_vs_Cloud.docx | Informe generado o entregable histórico de comparación. |
| RESUMEN_INTEGRACION_OPENAI.md (raíz) | Bitácora de migración antigua; contiene nombres/precios/resultados de modelos históricos. Para estado actual usar .env, /health y manual técnico. |
| SOLICITUD_TECNICA_INFRAESTRUCTURA_WHATSAPP_UNIMON_DEFINITIVA.docx (raíz) | Solicitud formal de infraestructura; sus datos deben validarse con TI. |

### Carpetas auxiliares locales

- .agents/skills: instrucciones y herramientas auxiliares para asistentes de desarrollo. No las carga FastAPI. Contiene agent-md-refactor, command-creator, daily-meeting-update, debugging-strategies, dependency-updater, github-actions-templates, plugin-forge, reducing-entropy, session-handoff y systematic-debugging; references/evals/scripts son recursos de esas guías.
- .vscode/settings.json: fija intérprete local .venv y rutas de análisis/autocompletado del editor.
- .venv: entorno Python generado por setup.ps1 y requirements; no versionar ni copiar entre máquinas. Es recreable, pero puede ocupar gigabytes.
- .git: datos e historial de control de versiones; no forma parte del runtime ni se edita manualmente.
- __pycache__ y .pytest_cache: bytecode y estado de tests generados; pueden borrarse con el proceso detenido.
- chroma_db y chroma_db_backup: índice documental y copia local; son binarios de Chroma que deben tratarse como datos, no editar sus archivos HNSW/SQLite a mano.
- data/chroma_db y data/chroma_db_backup: instancia y copias de Golden Cache.
- data/scratch/staged_uploads: subidas sin resolver en el panel; verificar y limpiar en forma controlada.
- scratch: logs, código de experimentación y fragmentos locales; puede contener consultas reales; no se usa como fuente normal.
- reports: ejecuciones de calidad, carga, trazas y calibración. Pueden contener prompts/respuestas/sources y resultados de usuario; no publicar sin revisión.
- .agents, .vscode, bases, caches, staging, logs y reports no son dependencias de ejecución indistintamente: cada uno tiene retención/seguridad propia.

### Archivos de la raíz

| Archivo | Función |
|---|---|
| README.md | Entrada rápida y enlaces a documentación vigente. |
| requirements.txt | Dependencias Python base del entorno. |
| setup.ps1 | Aprovisiona venv, dependencias y copia inicial de .env.example. |
| run.ps1 | Inicia proveedor elegido, diagnóstico local/LAN y servidor Uvicorn; puede abrir túnel opcional. |
| .env.example | Plantilla de variables, con placeholders no válidos. |
| .env | Credenciales locales activas; secreto, no compartir ni versionar. |
| .gitignore | Excluye entorno, secretos, archivos de base de datos/temporales y logs. |
| Modelfile | Modelo local Ollama derivado de llama3.1:8b y un prompt heredado. |
| pytest.ini | Configuración de suite Pytest. |
| test_rag.py | Smoke test que llama RAG directamente para una consulta fija; consulta al modelo real según configuración. |
| RESUMEN_INTEGRACION_OPENAI.md | Registro histórico de migración; no representa obligatoriamente modelos o precios actuales. |
| skills-lock.json | Lock de dependencias/versiones de herramientas/skills del entorno de desarrollo, no carga del chatbot. |
| SOLICITUD_TECNICA_INFRAESTRUCTURA_WHATSAPP_UNIMON_DEFINITIVA.docx | Solicitud administrativa de infraestructura; sus datos deben validarse con TI. |

### Dependencias declaradas en requirements.txt

| Dependencia | Uso en este proyecto |
|---|---|
| fastapi, uvicorn[standard], slowapi | API ASGI, ejecución del servidor y limitación de solicitudes. |
| pydantic, pydantic-settings, python-dotenv | Validación de esquemas, Settings y lectura de variables locales. |
| httpx, python-multipart | Clientes HTTP a proveedores/GLPI/Meta y recepción multipart de archivos. |
| langchain, langchain-community, langchain-chroma, langchain-huggingface | Integraciones para Documents, vector store, modelos de embeddings y pipeline documental. |
| langchain-text-splitters | Segmentación de páginas/diapositivas en fragmentos. |
| chromadb | Persistencia y búsqueda del índice RAG y la colección Golden Cache. |
| sentence-transformers | Modelo E5 de embeddings y Cross-Encoder reranker. Su backend de cómputo depende de PyTorch instalado. |
| pypdf, pymupdf | Extracción PDF y lectura/renderizado de páginas. |
| python-pptx | Texto, tablas, notas e imágenes de presentaciones PPTX. |
| Pillow | Normalización y lectura de imágenes incrustadas. |
| tqdm | Progreso visual de ingesta por lotes. |
| scikit-learn | Algoritmos de clustering/analítica semántica. |
| python-docx | Lectura de DOCX en la utilidad de staging/auditoría; no vuelve DOCX compatible con la ingesta RAG principal. |

No se declaran CrewAI ni LangGraph. No instales una librería por su popularidad: agrega dependencias solo si una función concreta las necesita y documenta su impacto.

## 9. Datos que deben tratarse como privados o regenerables

| Ruta | Qué representa | Cuidado |
|---|---|---|
| data/analytics.db | Interacciones y telemetría. | Puede contener preguntas, respuestas, roles y tickets; no copiar a demos públicas. |
| data/.vision_cache.json | Hashes y descripciones visuales. | Puede reproducir texto contenido en capturas internas. |
| data/rag_retrieval_eval_latest.json | Resultados de evaluación de recuperación. | Puede contener consulta/contexto; revisar antes de compartir. |
| data/rag_overlap_calibration_latest.json | Resumen de medición de redundancia. | Reproducible ejecutando auditoría. |
| chroma_db/ | Índice y embeddings derivados del corpus. | Usar backup/restore soportado, nunca editar binary files. |
| data/chroma_db/ | Vector store Golden Cache. | Eliminar o modificar cambia aprendizaje/ejemplos persistidos. |
| scratch/ y reports/ | Logs, trazas, casos y respuestas. | Revisar datos sensibles y limpiar según política. |
| .env | Tokens API y secretos. | Nunca adjuntar, publicar ni guardar en documentos. |

## 10. Criterios para entregar el proyecto

Antes de cerrar una práctica:

1. Indica qué commit/revisión se usó, Python, proveedor/modelo, dispositivo de embeddings y fecha del corpus.
2. Conserva instrucciones sin secretos y deja fuera bases/logs personales salvo que TI autorice respaldarlas.
3. Ejecuta prueba smoke de web, una consulta simple y una consulta procedural con expectativa documental.
4. Adjunta reporte exacto de recuperación y, si aplica, latencia concurrente con shape claro (10 o 50 simultáneas).
5. Reporta por separado éxito HTTP, fuente recuperada, exactitud juzgada, latencia y errores por caso.
6. Promueve Golden Cache solamente con evidencia revisada y resultados calificados.
7. Deja anotado qué documentos no soporta el ingestor, errores conocidos y procedimiento para restaurar índice.
8. No afirmes que UniMon está listo para producción solo porque inicia o responde 200.


## 11. Inventario completo de fuentes documentales

La tabla enumera todos los archivos presentes bajo data/docs en esta revisión (247 archivos: 128 PDF, 115 PPTX, 2 DOCX y 2 XLSX). La explicación identifica el tema por el título del archivo; no reemplaza la lectura de su contenido, la validación del dueño del procedimiento ni la comprobación de vigencia. “Sí” significa formato admitido por el pipeline actual, no extracción garantizada ni aprobación de contenido.

| Ruta relativa | Formato | Qué representa / límite | Ingesta principal |
|---|---|---|---|
| data/docs/1_estudiantes/test_dedup_doc.pdf | PDF | Fuente documental cuyo tema/título registrado es “test dedup doc”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. Artefacto de prueba alojado dentro del corpus: la búsqueda recursiva actual sí lo indexa; excluirlo del corpus operativo si no es intencional. | Sí, sujeto a extracción |
| data/docs/1. Estudiantes Nuevos Pregrado.pptx | PPTX | Fuente documental cuyo tema/título registrado es “1. Estudiantes Nuevos Pregrado”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/2. Estudiantes Antiguos Pregrado.pptx | PPTX | Fuente documental cuyo tema/título registrado es “2. Estudiantes Antiguos Pregrado”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/3. Matricula Completa-Media matricula.pptx | PPTX | Fuente documental cuyo tema/título registrado es “3. Matricula Completa-Media matricula”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/4. Transferencia Externa.pptx | PPTX | Fuente documental cuyo tema/título registrado es “4. Transferencia Externa”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/5. Ser Pilo Paga.pptx | PPTX | Fuente documental cuyo tema/título registrado es “5. Ser Pilo Paga”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/6. Reintegro.pptx | PPTX | Fuente documental cuyo tema/título registrado es “6. Reintegro”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/7. Valor matrícula.pptx | PPTX | Fuente documental cuyo tema/título registrado es “7. Valor matrícula”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Activación de matrículas.pdf | PDF | Fuente documental cuyo tema/título registrado es “Activación de matrículas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Activar Usuario y Correo institucional.pdf | PDF | Fuente documental cuyo tema/título registrado es “Activar Usuario y Correo institucional”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Administración de Autoevaluación.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Administración de Autoevaluación”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Agregar_miembros_Grupos_MS_Teams.pdf | PDF | Fuente documental cuyo tema/título registrado es “Agregar miembros Grupos MS Teams”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Ajustes participantes reuniones  Ms Teams.pdf | PDF | Fuente documental cuyo tema/título registrado es “Ajustes participantes reuniones Ms Teams”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Anexo_1_CP-GT-01_Descripcion_de_Indicadores_del_proceso__Gestion_de_TI.pdf | PDF | Fuente documental cuyo tema/título registrado es “Anexo 1 CP-GT-01 Descripcion de Indicadores del proceso Gestion de TI”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Anulación y Modificación de Programa Pre-inscripciones.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Anulación y Modificación de Programa Pre-inscripciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Aplicativo Elecciones -  Cómo votar.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Aplicativo Elecciones - Cómo votar”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Aplicativo Elecciones -  Módulo Docentes.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Aplicativo Elecciones - Módulo Docentes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Aplicativo Elecciones -  Módulo Egresados.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Aplicativo Elecciones - Módulo Egresados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Aplicativo Elecciones -  Módulo Estudiantes.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Aplicativo Elecciones - Módulo Estudiantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Aplicativo Elecciones -  Módulo Funcionarios.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Aplicativo Elecciones - Módulo Funcionarios”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Aplicativo Elecciones -  Módulo Usuarios Votantes.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Aplicativo Elecciones - Módulo Usuarios Votantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Aplicativo Elecciones -  Órganos colegiados.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Aplicativo Elecciones - Órganos colegiados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Aplicativo elecciones - Módulo Configuración.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Aplicativo elecciones - Módulo Configuración”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Aprobación de Requisitos.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Aprobación de Requisitos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Aprobacion Solicitudes de credito.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Aprobacion Solicitudes de credito”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Asignación académica - Listados.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Asignación académica - Listados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Asignación Académica.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Asignación Académica”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Aspirantes - Reactivación de Inscripción.pdf | PDF | Fuente documental cuyo tema/título registrado es “Aspirantes - Reactivación de Inscripción”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Autoevaluacion por Grupos - Funcionarios.pdf | PDF | Fuente documental cuyo tema/título registrado es “Autoevaluacion por Grupos - Funcionarios”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Automatización_de_creación_de usuarios_en_LDAP_(estudiantes).docx | DOCX | Fuente documental cuyo tema/título registrado es “Automatización de creación de usuarios en LDAP (estudiantes)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. Formato DOCX no procesado por la ingesta principal. | No |
| data/docs/Autorizacion de Inscripcion Curso de Enfasis.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Autorizacion de Inscripcion Curso de Enfasis”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Autorización de Supletorios.pdf | PDF | Fuente documental cuyo tema/título registrado es “Autorización de Supletorios”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Autorización estudiantes en proceso de créditos_v2.pdf | PDF | Fuente documental cuyo tema/título registrado es “Autorización estudiantes en proceso de créditos v2”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Autorización estudiantes en proceso de créditos.pdf | PDF | Fuente documental cuyo tema/título registrado es “Autorización estudiantes en proceso de créditos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Autorizaciones cursos intersemestrales.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Autorizaciones cursos intersemestrales”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Bancos y cuentas_v1_20211007.pdf | PDF | Fuente documental cuyo tema/título registrado es “Bancos y cuentas v1 20211007”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Bienestar universitario manual.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Bienestar universitario manual”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Bloqueos, Sanciones y Excepciones.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Bloqueos, Sanciones y Excepciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Calificaciones Posgrados-S3-DITI-PC07.pdf | PDF | Fuente documental cuyo tema/título registrado es “Calificaciones Posgrados-S3-DITI-PC07”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Calificaciones Posgrados.pdf | PDF | Fuente documental cuyo tema/título registrado es “Calificaciones Posgrados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Calificaciones.pdf | PDF | Fuente documental cuyo tema/título registrado es “Calificaciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Calificaciones.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Calificaciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Capacidades de admision_v1_11102021.pdf | PDF | Fuente documental cuyo tema/título registrado es “Capacidades de admision v1 11102021”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Caracterización de estudiantes.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Caracterización de estudiantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Carga de codigos EK.pdf | PDF | Fuente documental cuyo tema/título registrado es “Carga de codigos EK”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Carga de resultados EK.pdf | PDF | Fuente documental cuyo tema/título registrado es “Carga de resultados EK”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Certificados Electrónicos.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Certificados Electrónicos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Certificados estudiantes_v2.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Certificados estudiantes v2”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Como_acceder_a_Microsoft_Teams.pdf | PDF | Fuente documental cuyo tema/título registrado es “Como acceder a Microsoft Teams”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Como_acceder_MS_Teams_Estudiantes.pdf | PDF | Fuente documental cuyo tema/título registrado es “Como acceder MS Teams Estudiantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Condonación de saldo cartera castigada.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Condonación de saldo cartera castigada”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Configuracion de Evaluacion Profesoral - Funcionarios.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Configuracion de Evaluacion Profesoral - Funcionarios”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Configuracion de Evaluaciones.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Configuracion de Evaluaciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Consulta de Excepciones, bloqueos y sanciones.pdf | PDF | Fuente documental cuyo tema/título registrado es “Consulta de Excepciones, bloqueos y sanciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Consulta de Hoja de Vida - Matrículas.pdf | PDF | Fuente documental cuyo tema/título registrado es “Consulta de Hoja de Vida - Matrículas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Consulta de Hoja de Vida.pdf | PDF | Fuente documental cuyo tema/título registrado es “Consulta de Hoja de Vida”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Convenio Institucional.pdf | PDF | Fuente documental cuyo tema/título registrado es “Convenio Institucional”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/CP-GT-01_Gestion_de_TI.pdf | PDF | Fuente documental cuyo tema/título registrado es “CP-GT-01 Gestion de TI”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Creación de Programas.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Creación de Programas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Crear reuniones en teams - iPads aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.pdf | PDF | Fuente documental cuyo tema/título registrado es “Crear reuniones en teams - iPads aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Crear reuniones No asociadas a grupos.pdf | PDF | Fuente documental cuyo tema/título registrado es “Crear reuniones No asociadas a grupos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Credenciales microsoft.pdf | PDF | Fuente documental cuyo tema/título registrado es “Credenciales microsoft”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Demo tipos de admisión.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Demo tipos de admisión”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Depuración de cursos (Teams y Aula Extendida).pdf | PDF | Fuente documental cuyo tema/título registrado es “Depuración de cursos (Teams y Aula Extendida)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Descarga de certificados.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Descarga de certificados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Descarga e instalación Ms 365.pdf | PDF | Fuente documental cuyo tema/título registrado es “Descarga e instalación Ms 365”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Descuentos por Programa.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Descuentos por Programa”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Detalle factura (Anexos).pptx | PPTX | Fuente documental cuyo tema/título registrado es “Detalle factura (Anexos)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/dificultades_plataforma.xlsx | XLSX | Fuente documental cuyo tema/título registrado es “dificultades plataforma”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. Formato XLSX no procesado por la ingesta principal. | No |
| data/docs/Diligenciamiento de PAC (Profesores).pdf | PDF | Fuente documental cuyo tema/título registrado es “Diligenciamiento de PAC (Profesores)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Distribución por escolaridad de los miembros de la familia.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Distribución por escolaridad de los miembros de la familia”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Distribución por formación Escolar.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Distribución por formación Escolar”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Distribución por procedencia educativa oficial y privada.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Distribución por procedencia educativa oficial y privada”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Estadísticas institucionales.pdf | PDF | Fuente documental cuyo tema/título registrado es “Estadísticas institucionales”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Estudiantes_Matricular grupos en teams ymoodle.pdf | PDF | Fuente documental cuyo tema/título registrado es “Estudiantes Matricular grupos en teams ymoodle”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Evaluacion Profesoral - Estudiante.pdf | PDF | Fuente documental cuyo tema/título registrado es “Evaluacion Profesoral - Estudiante”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Evaluación Profesoral.pdf | PDF | Fuente documental cuyo tema/título registrado es “Evaluación Profesoral”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Evaluaciones de selección - ASPIRANTES.pdf | PDF | Fuente documental cuyo tema/título registrado es “Evaluaciones de selección - ASPIRANTES”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Evaluaciones de selección ILE-TICS (ASPIRANTES).pdf | PDF | Fuente documental cuyo tema/título registrado es “Evaluaciones de selección ILE-TICS (ASPIRANTES)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Evaluaciones de selección ILE-TICS (FUNCIONARIOS).pdf | PDF | Fuente documental cuyo tema/título registrado es “Evaluaciones de selección ILE-TICS (FUNCIONARIOS)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Evaluaciones de selección ILE-TICS (FUNCIONARIOS).pptx | PPTX | Fuente documental cuyo tema/título registrado es “Evaluaciones de selección ILE-TICS (FUNCIONARIOS)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Experiencias Extracurriculares (Estudiantes).pptx | PPTX | Fuente documental cuyo tema/título registrado es “Experiencias Extracurriculares (Estudiantes)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Experiencias Extracurriculares (Funcionarios).pptx | PPTX | Fuente documental cuyo tema/título registrado es “Experiencias Extracurriculares (Funcionarios)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Financiera ERP.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Financiera ERP”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Fucionarios_Integración Moodle y Teams.pdf | PDF | Fuente documental cuyo tema/título registrado es “Fucionarios Integración Moodle y Teams”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Gabriel Garate.xlsx | XLSX | Fuente documental cuyo tema/título registrado es “Gabriel Garate”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. Formato XLSX no procesado por la ingesta principal. | No |
| data/docs/Gestión de Ayudas Educativas.pdf | PDF | Fuente documental cuyo tema/título registrado es “Gestión de Ayudas Educativas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Gestión de caracterización.pdf | PDF | Fuente documental cuyo tema/título registrado es “Gestión de caracterización”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Gestión de Códigos EK.pdf | PDF | Fuente documental cuyo tema/título registrado es “Gestión de Códigos EK”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Gestión de Ingreso -  Funcionarios.pdf | PDF | Fuente documental cuyo tema/título registrado es “Gestión de Ingreso - Funcionarios”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Gestión de Ingreso -  Solo Consulta .pdf | PDF | Fuente documental cuyo tema/título registrado es “Gestión de Ingreso - Solo Consulta”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Gestión de inscripciones - Anexo actualizaciones.pdf | PDF | Fuente documental cuyo tema/título registrado es “Gestión de inscripciones - Anexo actualizaciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Gestión de inscripciones - Anexo actualizaciones.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Gestión de inscripciones - Anexo actualizaciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Gestión de inscripciones.pdf | PDF | Fuente documental cuyo tema/título registrado es “Gestión de inscripciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Gestión de Notas Crédito.pdf | PDF | Fuente documental cuyo tema/título registrado es “Gestión de Notas Crédito”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Gestión Prácticas - Estudiantes.pdf | PDF | Fuente documental cuyo tema/título registrado es “Gestión Prácticas - Estudiantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Gestión Prácticas - Funcionarios.pdf | PDF | Fuente documental cuyo tema/título registrado es “Gestión Prácticas - Funcionarios”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/GIE - ASPIRANTES NOV.2021.pptx | PPTX | Fuente documental cuyo tema/título registrado es “GIE - ASPIRANTES NOV.2021”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Grabar un clase en Teams y compartir en Stream.pdf | PDF | Fuente documental cuyo tema/título registrado es “Grabar un clase en Teams y compartir en Stream”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Grabar videollamadas en Teams.pdf | PDF | Fuente documental cuyo tema/título registrado es “Grabar videollamadas en Teams”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Graduar.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Graduar”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Grupos_en_Teams.pdf | PDF | Fuente documental cuyo tema/título registrado es “Grupos en Teams”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Habilitar permisos PAC (Director de programa).pdf | PDF | Fuente documental cuyo tema/título registrado es “Habilitar permisos PAC (Director de programa)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Homologaciones.pdf | PDF | Fuente documental cuyo tema/título registrado es “Homologaciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Ingreso de Causas de Desertores y Ausentes.pdf | PDF | Fuente documental cuyo tema/título registrado es “Ingreso de Causas de Desertores y Ausentes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Inscripcion - Educacion Continuada.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Inscripcion - Educacion Continuada”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Inscripcion de cursos intersemestrales.pdf | PDF | Fuente documental cuyo tema/título registrado es “Inscripcion de cursos intersemestrales”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Inscripcion de cursos intersemestrales.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Inscripcion de cursos intersemestrales”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Inscripción.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Inscripción”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instrucciones Actualización Datos Estudiantes.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instrucciones Actualización Datos Estudiantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo - Estudiantes.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Instructivo - Estudiantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo - Inscripción ed. continuada_v2.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo - Inscripción ed. continuada v2”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo - Inscripción ed. continuada.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo - Inscripción ed. continuada”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo - Reporte de asistencias QR.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo - Reporte de asistencias QR”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Activar Periodo.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo Activar Periodo”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Aplicativo Programas.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Instructivo Aplicativo Programas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Aprobación de Requisitos.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo Aprobación de Requisitos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Atencion a Estudiantes (Tutorías).pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo Atencion a Estudiantes (Tutorías)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo autorizaciones grados.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo autorizaciones grados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Bloqueos.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo Bloqueos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Credito Empresarial.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Instructivo Credito Empresarial”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/instructivo desertores y ausentes.pptx | PPTX | Fuente documental cuyo tema/título registrado es “instructivo desertores y ausentes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Módulo Atención Estudiantes (Completo).pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo Módulo Atención Estudiantes (Completo)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/instructivo parametrizacion desertores y ausentes.pptx | PPTX | Fuente documental cuyo tema/título registrado es “instructivo parametrizacion desertores y ausentes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Planeación Actualizado.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo Planeación Actualizado”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/instructivo portales estudiantes.pdf | PDF | Fuente documental cuyo tema/título registrado es “instructivo portales estudiantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/instructivo portales estudiantes.pptx | PPTX | Fuente documental cuyo tema/título registrado es “instructivo portales estudiantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Programas y Preparatorios.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo Programas y Preparatorios”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Programas y Preparatorios.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Instructivo Programas y Preparatorios”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Remisiones desde Calificaciones y Módulo Atención.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo Remisiones desde Calificaciones y Módulo Atención”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/instructivo reporte desertores.pptx | PPTX | Fuente documental cuyo tema/título registrado es “instructivo reporte desertores”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Reportes Consolidados.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo Reportes Consolidados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Reportes Estrategias.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo Reportes Estrategias”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo StrategicU.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo StrategicU”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Instructivo Verificación pagos V2.pdf | PDF | Fuente documental cuyo tema/título registrado es “Instructivo Verificación pagos V2”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Jefe Inmediato - Funcionarios.pdf | PDF | Fuente documental cuyo tema/título registrado es “Jefe Inmediato - Funcionarios”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Liquidacion de servicios academicos - Configuración.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Liquidacion de servicios academicos - Configuración”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Listado de créditos.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Listado de créditos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Listado de volantes.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Listado de volantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Malla academica.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Malla academica”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Mantenimiento de Salones.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Mantenimiento de Salones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Manual de Usuario - Portal CovidApp.pdf | PDF | Fuente documental cuyo tema/título registrado es “Manual de Usuario - Portal CovidApp”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Manual de Usuario - Registro de Ingreso.pdf | PDF | Fuente documental cuyo tema/título registrado es “Manual de Usuario - Registro de Ingreso”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Manual Evaluación CAQ - Aspirantes.pdf | PDF | Fuente documental cuyo tema/título registrado es “Manual Evaluación CAQ - Aspirantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Manual Evaluación CAQ - Funcionarios.pdf | PDF | Fuente documental cuyo tema/título registrado es “Manual Evaluación CAQ - Funcionarios”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Matricula (2).pptx | PPTX | Fuente documental cuyo tema/título registrado es “Matricula (2)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Matrícula Antiguos Posgrados.pdf | PDF | Fuente documental cuyo tema/título registrado es “Matrícula Antiguos Posgrados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Matricula de Cursos Intersemestrales.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Matricula de Cursos Intersemestrales”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Matricula.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Matricula”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Matricular_grupos_teams_Estudiante.pdf | PDF | Fuente documental cuyo tema/título registrado es “Matricular grupos teams Estudiante”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Matricular_grupos_teams_moodle_Estudiante.pdf | PDF | Fuente documental cuyo tema/título registrado es “Matricular grupos teams moodle Estudiante”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Mercadeo - Seguimiento.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Mercadeo - Seguimiento”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Módulo de instrumentos de autoevaluación.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Módulo de instrumentos de autoevaluación”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Movilidad Académica - Administrativo.pdf | PDF | Fuente documental cuyo tema/título registrado es “Movilidad Académica - Administrativo”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Movilidad Académica - Estudiantes.pdf | PDF | Fuente documental cuyo tema/título registrado es “Movilidad Académica - Estudiantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Nivel de Ingles Vs Nivel de Avance.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Nivel de Ingles Vs Nivel de Avance”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Nueva Hoja de Vida.pdf | PDF | Fuente documental cuyo tema/título registrado es “Nueva Hoja de Vida”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Ofertas de inscripción para grados.pdf | PDF | Fuente documental cuyo tema/título registrado es “Ofertas de inscripción para grados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Ofertas Intersemestrales.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Ofertas Intersemestrales”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Ofertas.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Ofertas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/P-GT-01_Procedimiento_mantenimiento_equipos_de_computo.pdf | PDF | Fuente documental cuyo tema/título registrado es “P-GT-01 Procedimiento mantenimiento equipos de computo”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf | PDF | Fuente documental cuyo tema/título registrado es “P-GT-02 Procedimiento para el otorgamiento modificacion o retiro de acceso a usuarios del sistema de Informacion”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/P-GT-07_Procedimiento_Proteccion_de_Codigo_Malicioso_.pdf | PDF | Fuente documental cuyo tema/título registrado es “P-GT-07 Procedimiento Proteccion de Codigo Malicioso”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/P-GT-08_Procedimiento_Aseguramiento_de_Servicios_en_la_Red_.pdf | PDF | Fuente documental cuyo tema/título registrado es “P-GT-08 Procedimiento Aseguramiento de Servicios en la Red”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/P-GT-09_Procedimiento_para_el_Mantenimiento_de_Equipos_de_Computo_del_Laboratorio_de_Diagnostico_Molecular.pdf | PDF | Fuente documental cuyo tema/título registrado es “P-GT-09 Procedimiento para el Mantenimiento de Equipos de Computo del Laboratorio de Diagnostico Molecular”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/P-GT-10_Procedimiento_para_la_Generacion_y_Restauracion_de_Backup_de_la_Informacion_de_la_Universidad_Simon_Bolivar.pdf | PDF | Fuente documental cuyo tema/título registrado es “P-GT-10 Procedimiento para la Generacion y Restauracion de Backup de la Informacion de la Universidad Simon Bolivar”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/P-GT-11_Proc._Atencion_de_Incidencias_y_Requerimientos_Katus_Y_Seven_.pdf | PDF | Fuente documental cuyo tema/título registrado es “P-GT-11 Proc. Atencion de Incidencias y Requerimientos Katus Y Seven”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf | PDF | Fuente documental cuyo tema/título registrado es “P-GT-12 Procedimiento para la gestion de cuentas de usuario en KACTUS o SEVEN”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/P-GT-13_Procedimiento_para_la_gestion_de_requerimientos_de_recursos_y_soluciones_tecnologicas.pdf | PDF | Fuente documental cuyo tema/título registrado es “P-GT-13 Procedimiento para la gestion de requerimientos de recursos y soluciones tecnologicas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/P-GT-14_Procedimiento_para_la_gestion_de_actualizaciones_de_versiones_en_Kactus_y_o_Seven.pdf | PDF | Fuente documental cuyo tema/título registrado es “P-GT-14 Procedimiento para la gestion de actualizaciones de versiones en Kactus y o Seven”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Pagos en linea - Aspirantes.pdf | PDF | Fuente documental cuyo tema/título registrado es “Pagos en linea - Aspirantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Pagos en linea - Estudiantes.pdf | PDF | Fuente documental cuyo tema/título registrado es “Pagos en linea - Estudiantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Pagos en Linea_vPaymentz.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Pagos en Linea vPaymentz”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Pagos en Linea.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Pagos en Linea”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Parametrización de Requisitos.pdf | PDF | Fuente documental cuyo tema/título registrado es “Parametrización de Requisitos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Parametrizacion Evaluaciones.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Parametrizacion Evaluaciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Paymentez - Manual de usuario Link de pagos y Dashboard (2).pdf | PDF | Fuente documental cuyo tema/título registrado es “Paymentez - Manual de usuario Link de pagos y Dashboard (2)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/PETI.docx | DOCX | Fuente documental cuyo tema/título registrado es “PETI”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. Formato DOCX no procesado por la ingesta principal. | No |
| data/docs/Planeación - Informe de Gestión.pdf | PDF | Fuente documental cuyo tema/título registrado es “Planeación - Informe de Gestión”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Presentación Link to Pay Masivo - Paymentez.pptx.pdf | PDF | Fuente documental cuyo tema/título registrado es “Presentación Link to Pay Masivo - Paymentez.pptx”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Proceso de Autoevaluación.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Proceso de Autoevaluación”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Profesores_Integración teams y moodle.pdf | PDF | Fuente documental cuyo tema/título registrado es “Profesores Integración teams y moodle”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Programas.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Programas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Proveedores Activos.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Proveedores Activos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Proyección (agregar, eliminar, habilitar).pdf | PDF | Fuente documental cuyo tema/título registrado es “Proyección (agregar, eliminar, habilitar)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Proyección (agregar, eliminar, habilitar).pptx | PPTX | Fuente documental cuyo tema/título registrado es “Proyección (agregar, eliminar, habilitar)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Proyección (agregar, elimnar, homologar).pptx | PPTX | Fuente documental cuyo tema/título registrado es “Proyección (agregar, elimnar, homologar)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reactivación de Inscripción.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reactivación de Inscripción”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Remisiones.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Remisiones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Asignacion Académica.pdf | PDF | Fuente documental cuyo tema/título registrado es “Reporte - Asignacion Académica”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Asignacion Académica.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte - Asignacion Académica”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Asignaturas por Grupos.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte - Asignaturas por Grupos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Capacidad vs Matriculados.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte - Capacidad vs Matriculados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Contabilidad - Creditos.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte - Contabilidad - Creditos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Contabilidad - Saldos Empresarial.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte - Contabilidad - Saldos Empresarial”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Costo Nomina.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte - Costo Nomina”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Estudiantes autorizados en proceso de créditos_v2.pdf | PDF | Fuente documental cuyo tema/título registrado es “Reporte - Estudiantes autorizados en proceso de créditos v2”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Estudiantes autorizados en proceso de créditos.pdf | PDF | Fuente documental cuyo tema/título registrado es “Reporte - Estudiantes autorizados en proceso de créditos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Estudiantes sin grupos escogidos.pdf | PDF | Fuente documental cuyo tema/título registrado es “Reporte - Estudiantes sin grupos escogidos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Franja Horaria.pdf | PDF | Fuente documental cuyo tema/título registrado es “Reporte - Franja Horaria”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Grupos sin Estudiantes.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte - Grupos sin Estudiantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Horas x Docente.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte - Horas x Docente”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Inscripción Reactivada.pdf | PDF | Fuente documental cuyo tema/título registrado es “Reporte - Inscripción Reactivada”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Inscripción Reactivada.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte - Inscripción Reactivada”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Inscritos.pdf | PDF | Fuente documental cuyo tema/título registrado es “Reporte - Inscritos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - No matriculados (1).pdf | PDF | Fuente documental cuyo tema/título registrado es “Reporte - No matriculados (1)”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte - Reingresos y Transferencias Internas.pdf | PDF | Fuente documental cuyo tema/título registrado es “Reporte - Reingresos y Transferencias Internas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte -Historico de Asignacion Académica.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte -Historico de Asignacion Académica”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte de aprobadas vs ejecutadas.pdf | PDF | Fuente documental cuyo tema/título registrado es “Reporte de aprobadas vs ejecutadas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte de crédito.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte de crédito”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte de Distribución de estudiantes por promedios acumulados.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte de Distribución de estudiantes por promedios acumulados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte de estudiantes graduados - Resolucion 4008.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte de estudiantes graduados - Resolucion 4008”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte de estudiantes graduados.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte de estudiantes graduados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte de estudiantes inscritos.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte de estudiantes inscritos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte de estudiantes matriculados.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte de estudiantes matriculados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte de estudiantes por edad.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte de estudiantes por edad”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte de preinscritos.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte de preinscritos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reporte de Seguimiento.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reporte de Seguimiento”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reportes - Certificados electrónicos.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reportes - Certificados electrónicos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reportes Anexos de Facturas.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reportes Anexos de Facturas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reportes créditos de matriculados.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reportes créditos de matriculados”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reportes créditos general.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reportes créditos general”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reportes de Bienestar.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reportes de Bienestar”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reportes de Caracterización.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reportes de Caracterización”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reportes de Desertores.pdf | PDF | Fuente documental cuyo tema/título registrado es “Reportes de Desertores”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reportes de Evaluaciones.pdf | PDF | Fuente documental cuyo tema/título registrado es “Reportes de Evaluaciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reportes de Evaluaciones.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reportes de Evaluaciones”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Reportes generales.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Reportes generales”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf | PDF | Fuente documental cuyo tema/título registrado es “Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Restablecimiento de contraseña.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Restablecimiento de contraseña”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Resultados de aprendizaje.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Resultados de aprendizaje”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/retorno al campus 2021.pdf | PDF | Fuente documental cuyo tema/título registrado es “retorno al campus 2021”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Selección de horarios - Idiomas.pdf | PDF | Fuente documental cuyo tema/título registrado es “Selección de horarios - Idiomas”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Servicios Institucionales - Profesores.pdf | PDF | Fuente documental cuyo tema/título registrado es “Servicios Institucionales - Profesores”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/SITE 2.0.pptx | PPTX | Fuente documental cuyo tema/título registrado es “SITE 2.0”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Solicitud de crédito.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Solicitud de crédito”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Solicitud de inscripción para grado.pdf | PDF | Fuente documental cuyo tema/título registrado es “Solicitud de inscripción para grado”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/StrategicU.pdf | PDF | Fuente documental cuyo tema/título registrado es “StrategicU”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Todos_Reportes.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Todos Reportes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Trabajo de grado.pdf | PDF | Fuente documental cuyo tema/título registrado es “Trabajo de grado”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Trazabilidad de transferencia externa.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Trazabilidad de transferencia externa”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Unisimon App.pdf | PDF | Fuente documental cuyo tema/título registrado es “Unisimon App”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Verificación Autorización tratamiento de datos.pdf | PDF | Fuente documental cuyo tema/título registrado es “Verificación Autorización tratamiento de datos”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Verificacion de pagos_v1_20211105.pdf | PDF | Fuente documental cuyo tema/título registrado es “Verificacion de pagos v1 20211105”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Videollamadas en  Teams.pdf | PDF | Fuente documental cuyo tema/título registrado es “Videollamadas en Teams”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Volantes de pagos - Funcionarios.pptx | PPTX | Fuente documental cuyo tema/título registrado es “Volantes de pagos - Funcionarios”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |
| data/docs/Volantes.pdf | PDF | Fuente documental cuyo tema/título registrado es “Volantes”. La ingesta RAG conserva página/diapositiva cuando el parser la extrae. | Sí, sujeto a extracción |

## 12. Inventario de reportes y trazas existentes

Cada archivo de reports conserva una corrida o artefacto distinto. Los sufijos distinguen variantes de configuración y fases antes/después; no mezclar sus denominadores al comparar exactitud. Los resultados pueden contener preguntas reales, respuestas completas y nombres de documentos.

| Ruta | Qué es |
|---|---|
| reports/coloquial_100_20261005_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; prueba de 100 preguntas coloquiales y revisión de sus etapas. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/coloquial_100_20261005_review.md | Resumen legible de la ejecución o revisión; prueba de 100 preguntas coloquiales y revisión de sus etapas. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/coloquial_100_20261005_trace_after.json | Datos de prueba, resultados, traza de recuperación o calificación; prueba de 100 preguntas coloquiales y revisión de sus etapas. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/coloquial_100_20261005_trace_review.md | Resumen legible de la ejecución o revisión; prueba de 100 preguntas coloquiales y revisión de sus etapas. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/coloquial_100_20261005_trace.json | Datos de prueba, resultados, traza de recuperación o calificación; prueba de 100 preguntas coloquiales y revisión de sus etapas. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/coloquial_100_20261005.json | Datos de prueba, resultados, traza de recuperación o calificación; prueba de 100 preguntas coloquiales y revisión de sus etapas. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/coloquial_100_20261005.md | Resumen legible de la ejecución o revisión; prueba de 100 preguntas coloquiales y revisión de sus etapas. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/load_test_100_users_20261005_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; carga de 100 sesiones y resultados/revisión. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/load_test_100_users_20261005_review.md | Resumen legible de la ejecución o revisión; carga de 100 sesiones y resultados/revisión. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/load_test_100_users_20261005.json | Datos de prueba, resultados, traza de recuperación o calificación; carga de 100 sesiones y resultados/revisión. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/load_test_100_users_20261005.md | Resumen legible de la ejecución o revisión; carga de 100 sesiones y resultados/revisión. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/load_test_50_users_20261005.json | Datos de prueba, resultados, traza de recuperación o calificación; carga histórica de 50 sesiones. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/load_test_50_users_20261005.md | Resumen legible de la ejecución o revisión; carga histórica de 50 sesiones. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_50concurrent_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_50concurrent.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_50concurrent.md | Resumen legible de la ejecución o revisión; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_adaptive_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_adaptive.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_adaptive.md | Resumen legible de la ejecución o revisión; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_after_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_after.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_after.md | Resumen legible de la ejecución o revisión; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_anchor_budget_trace.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_anchor_verified_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_anchor_verified.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_anchor_verified.md | Resumen legible de la ejecución o revisión; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_context_fix_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_context_fix_trace.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_context_fix.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_context_fix.md | Resumen legible de la ejecución o revisión; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_final_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_final_trace.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_final.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_final.md | Resumen legible de la ejecución o revisión; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_golden_regression_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_golden_regression.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_golden_regression.md | Resumen legible de la ejecución o revisión; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_grounded_trace.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_intent_guard_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_intent_guard.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_intent_guard.md | Resumen legible de la ejecución o revisión; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_source_cap_trace.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_adaptive.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_after.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_after2.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_before.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_clean.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_final.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_golden.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_intent_guard.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_no_role_filter.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_titles.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_titles2.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_titles3.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_trace_visuals.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_verified_anchor_trace.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_visuals_judged.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_visuals.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006_visuals.md | Resumen legible de la ejecución o revisión; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006.json | Datos de prueba, resultados, traza de recuperación o calificación; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/quality_50_20261006.md | Resumen legible de la ejecución o revisión; una corrida/variante de evaluación de 50 preguntas; sufijo identifica la intervención/etapa. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |
| reports/reranker_calibration_20261006.md | Resumen legible de la ejecución o revisión; análisis de calibración del reranker. Puede incluir preguntas, respuestas, fuentes y datos sensibles. |

## 13. Inventario de recursos locales de desarrollo

Estos archivos pertenecen a .agents. Son recursos para asistentes/agentes de programación y automatizaciones del entorno de desarrollo. FastAPI, el RAG y la interfaz no los cargan.

- .agents/skills/agent-md-refactor/README.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/agent-md-refactor/SKILL.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/command-creator/README.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/command-creator/references/best-practices.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/command-creator/references/examples.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/command-creator/references/patterns.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/command-creator/SKILL.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/daily-meeting-update/README.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/daily-meeting-update/scripts/claude_digest.py: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/daily-meeting-update/SKILL.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/debugging-strategies/SKILL.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/dependency-updater/README.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/dependency-updater/scripts/check-tool.sh: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/dependency-updater/scripts/run-taze.sh: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/dependency-updater/SKILL.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/github-actions-templates/SKILL.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/plugin-forge/README.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/plugin-forge/references/marketplace-schema.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/plugin-forge/references/plugin-structure.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/plugin-forge/references/workflows.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/plugin-forge/scripts/bump_version.py: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/plugin-forge/scripts/create_plugin.py: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/plugin-forge/SKILL.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/reducing-entropy/adding-reference-mindsets.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/reducing-entropy/README.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/reducing-entropy/references/data-over-abstractions.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/reducing-entropy/references/design-is-taking-apart.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/reducing-entropy/references/expensive-to-add-later.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/reducing-entropy/references/simplicity-vs-easy.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/reducing-entropy/SKILL.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/evals/model-expectations.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/evals/results-opus-baseline.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/evals/setup_test_env.py: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/evals/test-scenarios.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/README.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/references/handoff-template.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/references/resume-checklist.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/scripts/check_staleness.py: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/scripts/create_handoff.py: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/scripts/list_handoffs.py: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/scripts/validate_handoff.py: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/session-handoff/SKILL.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/systematic-debugging/condition-based-waiting-example.ts: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/systematic-debugging/condition-based-waiting.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/systematic-debugging/CREATION-LOG.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/systematic-debugging/defense-in-depth.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/systematic-debugging/find-polluter.sh: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/systematic-debugging/root-cause-tracing.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/systematic-debugging/SKILL.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/systematic-debugging/test-academic.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/systematic-debugging/test-pressure-1.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/systematic-debugging/test-pressure-2.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.
- .agents/skills/systematic-debugging/test-pressure-3.md: recurso de una skill de asistente de desarrollo; orienta tareas de documentación/debug/dependencias/plugins/automatización y no se importa en runtime por UniMon.

## 14. Archivos de trabajo, staging e índices generados

### Archivos temporales visibles en esta revisión

Los siguientes ficheros no forman parte del código de runtime; son restos de diagnóstico o cargas en staging. Revisa la fecha, propietario y resultado antes de borrarlos o aceptarlos. Un PDF que quede dentro de staged_uploads aún espera resolución; uno en DOCS_DIR puede indexarse.

| Ruta | Qué contiene / precaución |
|---|---|
| scratch/live_consolidado_check.py | Script local de comprobación de una consulta sobre consolidado. No es una prueba general de la suite. |
| scratch/live_consolidado_check.log | Salida/log de esa comprobación; puede contener interacción real. |
| scratch/P-GT-01_fragmentos_chroma.txt | Volcado de fragmentos del procedimiento desde Chroma para inspección manual. |
| scratch/rag_eval_consolidado.json | Resultados de una evaluación local de búsqueda para el tema consolidado. |
| scratch/rag_eval_context_ampliado.json | Variante de evaluación con otro contexto de recuperación. |
| scratch/unimon-runtime.log | Log de ejecución capturado mediante run.ps1 -CaptureLogs. Puede incluir preguntas y metadatos operativos. |
| data/scratch/staged_uploads/14d93c1fdf_Generación del Informe de Matrícula Completa Media Matrícula.pdf | Archivo PDF en staging que requiere aceptar/reemplazar/deduplicar/cancelar desde la ruta administrativa. No asumir que está indexado. |
| data/scratch/staged_uploads/14d93c1fdf_meta.json | Metadatos de la carga anterior y destino/decisión pendiente. |
| data/scratch/staged_uploads/e4bd6b9089_test_dedup_doc.pdf | PDF de prueba temporal; no es manual institucional confirmado. |
| data/scratch/staged_uploads/e4bd6b9089_meta.json | Metadatos de la carga de prueba; revisar antes de limpiar staging. |

### Directorios internos de Chroma en disco

Los nombres UUID son directorios internos creados por Chroma para colecciones/índices. Se documentan para saber qué hay en este checkout; no asignan significado funcional sin consultar el SQLite de Chroma y no se deben renombrar ni editar manualmente.

| Directorio | UUID observado | Uso |
|---|---|---|
| chroma_db | 0fd0b3bd-5e24-4cfb-bb15-b9d845a38558 | Segmento de base vectorial documental del path por defecto. |
| chroma_db_backup | 1836e071-0b3c-4717-9699-dd58f6d31805 | Segmento guardado en respaldo local del índice documental. |
| data/chroma_db | 1521a24e-e001-4cca-ad20-24521a4bbb3f | Segmento de colección alojada en la ruta Golden Cache configurada; verifica colección concreta en SQLite. |
| data/chroma_db | 36020f9c-2f09-4780-b22e-068f5e0dfb37 | Segmento Chroma generado; no editar directamente. |
| data/chroma_db | 971ecf58-9f26-4319-957b-1cb48c5f98c7 | Segmento Chroma generado; no editar directamente. |
| data/chroma_db | ac68fc6e-5240-4b54-8412-4ee9258f8773 | Segmento Chroma generado; no editar directamente. |
| data/chroma_db_backup | 9be88f5d-db76-48e5-984d-28624733ab04 | Segmento del respaldo Golden Cache. |
| data/chroma_db_backup | a978ee42-4939-42f8-a5aa-e09d18e35b95 | Segmento del respaldo Golden Cache. |
| data/chroma_db_backup | e6aea57a-1fb1-4682-8121-2d86046da590 | Segmento del respaldo Golden Cache. |

Chroma también puede almacenar chroma.sqlite3 y archivos HNSW/metadata dentro de estas raíces. Son binarios regenerables/respaldables desde la aplicación; su cantidad de archivos puede cambiar con cada reindexación. Por eso no se enumeran como código fuente línea por línea. Del mismo modo, no se listan individualmente los miles de ficheros de .venv, .git, __pycache__ ni .pytest_cache: son dependencias, historial o cachés generados y no lógica propia del chatbot.


