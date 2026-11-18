# Ficha técnica y base para portafolio — UniMon

**Corte de esta ficha:** 30 de octubre de 2026.  
**Proyecto:** Desarrollo y validación de UniMon: asistente conversacional con recuperación documental local, soporte multidependencia e integración con GLPI.  
**Contexto:** práctica profesional de Ingeniería de Sistemas, Universidad Simón Bolívar, Barranquilla, Colombia.  
**Rol documentado:** estudiante y líder de desarrollo / ingeniero de software.

> Esta ficha reúne lo que está documentado en el informe y lo que se puede comprobar en el código del espacio de trabajo. Distingue funcionalidades implementadas, pruebas del desarrollo y aspectos todavía pendientes de validación institucional.

## 1. Resumen del proyecto

UniMon es un asistente conversacional para consultas de soporte de TI y orientación sobre procedimientos institucionales. El usuario escribe en lenguaje natural; el sistema identifica el tipo de solicitud, recupera información de manuales y procedimientos locales, compone una respuesta con un proveedor de lenguaje configurable y ofrece escalar a GLPI cuando se trata de un incidente que requiere atención humana.

El sistema también contempla asistentes separados por dependencia, un panel administrativo para gestionar fuentes e instancias, métricas de telemetría y un canal opcional de WhatsApp. El diseño busca distinguir una comprobación sencilla de autoayuda de una falla que necesita un técnico, y evitar que una consulta sobre un trámite académico o administrativo se convierta automáticamente en un ticket de Soporte Técnico.

**Problema atendido:** parte de las consultas repetidas puede orientarse con procedimientos documentados; otras solicitudes pertenecen a dependencias distintas de TI. Sin una vía de búsqueda sencilla, esas preguntas pueden llegar a la mesa de ayuda sin ser incidentes técnicos o requerir que el usuario navegue manuales extensos.

**Objetivo general:** desarrollar y evaluar un asistente conversacional con recuperación documental local, generación configurable, autoayuda y flujo de radicación de incidentes mediante GLPI, con posibilidad de separar asistentes por dependencia.

## 2. Alcance funcional implementado

- **Chat web:** interfaz servida por FastAPI desde `app/static/index.html`, con sesiones por pestaña, selección o conservación del rol, respuestas, fuentes y opciones de seguimiento.
- **Lógica conversacional:** `RouterLogic` gestiona el estado de la conversación, el diagnóstico inicial, la captura de información y el punto en el que se propone escalar.
- **Autoservicio documental:** búsqueda en el corpus institucional indexado; la respuesta puede incluir referencias a los documentos recuperados.
- **Orientación de trámites:** las consultas no técnicas se deben responder con información institucional disponible y no crear automáticamente tickets de TI.
- **Escalamiento a GLPI:** el flujo puede solicitar nombre, correo y descripción, crear el ticket cuando el servicio externo está configurado y confirmar el resultado solo si GLPI lo devuelve.
- **Asistentes por dependencia:** catálogo de instancias, perfiles de especialidad y separación de configuración e índices documentales.
- **Administración y analítica:** panel en `app/static/admin.html`, endpoints protegidos, métricas operativas y revisión de consultas no resueltas.
- **Canal opcional de WhatsApp:** router y servicio para la API de WhatsApp Cloud; requiere credenciales y configuración de Meta para operar.
- **Telemetría:** registra datos de interacción para analizar latencia, fuentes consultadas, estado de resolución, feedback, uso de tokens y escalamiento.

La disponibilidad de integraciones externas depende de sus credenciales, permisos y conectividad. El código contempla los flujos; eso no equivale a tenerlos desplegados en una instalación institucional activa.

## 3. Recorrido de una consulta

### Interfaces y endpoints

- `GET /` sirve el chat web.
- `POST /api/chat` recibe `mensaje` o `message` junto con `session_id`; rechaza texto vacío, limita el mensaje y neutraliza etiquetas HTML.
- `GET /health` expone estado básico del servicio; `/docs` publica el esquema OpenAPI durante desarrollo.
- `/admin` sirve el panel protegido.
- `GET /api/whatsapp` atiende la verificación del webhook y `POST /api/whatsapp` recibe eventos si el canal está configurado.

1. El usuario envía una consulta al chat web o, si está habilitado, por WhatsApp. El endpoint valida el texto y asocia la conversación con una sesión.
2. `RouterLogic` actualiza la sesión y aplica reglas del dominio. Puede resolver una respuesta breve sin RAG, orientar un trámite no técnico, iniciar un diagnóstico o proponer escalamiento.
3. Cuando necesita documentación, el servicio normaliza la consulta, conserva la pregunta original y puede generar variantes de búsqueda.
4. El RAG busca en ChromaDB con embeddings E5, suma candidatos léxicos, elimina duplicados y reordena candidatos con un Cross-Encoder. Cuando la fuente y los metadatos permiten verificarla, puede recuperar fragmentos cercanos del mismo documento.
5. El sistema construye el contexto con límites de cantidad de fragmentos y solicita una respuesta al proveedor configurado. Ollama local puede funcionar como alternativa cuando la ruta configurada falla y el servicio local está disponible.
6. La respuesta puede incluir fuentes, opciones rápidas y estado de resolución. Si la evidencia documental no alcanza, debe comunicar la limitación.
7. Si el usuario solicita atención o el diagnóstico exige soporte humano, el servicio GLPI intenta autenticar, crear el ticket, asociar al solicitante cuando corresponde y cerrar la sesión remota. El sistema no debe inventar un número de ticket cuando GLPI no confirma la creación.
8. La interacción y los indicadores pertinentes se registran en la telemetría local, sin guardar claves de proveedor como contenido de logs.

## 4. Arquitectura y módulos relevantes

| Área | Responsabilidad | Código principal |
|---|---|---|
| Aplicación y API | Inicio FastAPI, middlewares, archivos estáticos, salud y routers | `app/main.py` |
| Chat y reglas | Entrada de conversación, estado, diagnóstico y decisiones del flujo | `app/routers/chat.py`, `app/services/router_logic.py` |
| Recuperación RAG | Normalización, búsqueda vectorial y léxica, reranking, selección de contexto | `app/services/rag_service.py`, `app/services/normalizer_service.py` |
| Enrutamiento multidependencia | Selección de asistente, perfiles, catálogos y datos por instancia | `app/services/bot_router_service.py`, `app/services/bot_instance_service.py`, `app/services/document_catalog_service.py` |
| Generación LLM | Adaptadores para proveedores y contingencia con Ollama | `app/services/llm_client.py`, `app/services/llm_usage.py` |
| GLPI | Autenticación REST, creación, consulta/seguimiento y cierre de sesión | `app/services/glpi_service.py` |
| Fuentes documentales | Validación, saneamiento, transformación e ingesta | `app/services/sanitized_documents.py`, `app/services/knowledge_base_service.py`, `scripts/ingest_multimodal_docs.py` |
| Panel y analítica | KPIs, consultas no resueltas, administración de fuentes e instancias | `app/routers/admin_router.py`, `app/routers/analytics.py`, `app/services/telemetry_service.py` |
| WhatsApp | Verificación del webhook y manejo de mensajes | `app/routers/whatsapp.py`, `app/services/whatsapp_service.py` |
| Seguridad | Autenticación de administración, carga y validación de URLs de proveedores | `app/security.py`, `app/upload_security.py`, `app/services/llm_endpoint_security.py`, `app/services/secret_store.py` |
| Interfaz | Chat y panel administrativos servidos como estáticos | `app/static/index.html`, `app/static/admin.html` |

El informe incluye diagramas de casos de uso, secuencia, actividad, clases, componentes y despliegue de referencia. El despliegue se identifica como propuesta que requiere validación institucional.

## 5. IA, recuperación e ingesta documental

### Recuperación aumentada (RAG)

- **Almacenamiento vectorial:** ChromaDB local, con colecciones e índices separados según el uso y la instancia.
- **Embeddings configurados:** `intfloat/multilingual-e5-large` mediante Sentence-Transformers.
- **Prefijo de consulta:** el flujo E5 usa `query:` cuando crea la consulta vectorial.
- **Recuperación multiconsulta:** puede generar hasta tres variantes en español y conservar también la consulta original.
- **Búsqueda vectorial:** consulta embeddings E5 en Chroma, hasta ocho resultados por variante; los metadatos temáticos se usan cuando aplican.
- **Búsqueda mixta:** suma candidatos léxicos BM25, combina las listas y elimina duplicados.
- **Reordenamiento:** el Cross-Encoder reordena hasta ochenta candidatos; su score sirve para ordenar, no es una probabilidad calibrada de respuesta correcta.
- **Expansión de contexto:** puede recuperar fragmentos vecinos del mismo archivo si identifica de manera verificable el documento y los metadatos.
- **Límites de contexto:** procedimientos y consultas extensas pueden usar hasta 16 anclas y 24 fragmentos finales; consultas directas, hasta cuatro anclas y ocho fragmentos finales.
- **Golden Cache:** colección Chroma separada para casos validados. La coincidencia similar puede orientar la búsqueda, pero no sustituye por sí misma las fuentes institucionales ni acredita exactitud; la admisión e invalidación requieren controles.

### Ingesta

El pipeline principal procesa PDF y PPTX, extrae texto, tablas e imágenes, sanea contenido, segmenta y persiste fragmentos con metadatos. La segmentación documentada usa bloques de aproximadamente 800 caracteres y un solapamiento de 150 caracteres. La interpretación visual requiere Ollama y un modelo de visión configurado; si no está disponible, se conserva el procesamiento textual.

La guía técnica advierte que archivos DOCX y XLSX colocados en la carpeta de documentos no se indexan automáticamente por el ingestor principal. Para esos formatos debe usarse una transformación aprobada o ampliarse el parser y validarlo antes de tratarlos como conocimiento disponible.

### Proveedores de generación

El código contempla OpenAI, Gemini, Anthropic, Ollama y endpoints compatibles configurados por instancia. La selección depende de `LLM_PROVIDER` y de la configuración efectiva del entorno; no se debe presentar un proveedor como el único usado si no se conserva evidencia de la configuración concreta. La copia de trabajo documenta validación local reportada con `unimon:8b` en Ollama y fallback automatizado mediante dobles de prueba.

## 6. Persistencia e integraciones

| Dato o servicio | Tecnología / ubicación | Propósito y límite |
|---|---|---|
| Fragmentos y embeddings | ChromaDB local | Índices de recuperación, separados por corpus o instancia. |
| Golden Cache | Colección Chroma separada | Casos validados; una coincidencia puede orientar la búsqueda, pero no sustituye fuentes ni acredita exactitud. |
| Telemetría | SQLite `data/analytics.db` | Sesiones analíticas, interacciones, feedback, consultas ignoradas y actividad de tickets. |
| Configuración de instancias | SQLite `instances.sqlite3` | Registro separado de asistentes adicionales; no se relaciona por FK con la telemetría. |
| Sesiones conversacionales | Memoria del proceso | Estado e historial mientras corre la aplicación; se pierden al reiniciarla. |
| Tickets oficiales | GLPI externo | Fuente oficial de radicación y estado; fuera de las bases locales del modelo relacional. |
| LLM externo | API elegida por configuración | Puede recibir la consulta y fragmentos seleccionados cuando la generación cloud está habilitada. |

El esquema declara una relación de uno a muchos entre `telemetry_sessions.session_id` y `telemetry_interactions.session_id`. El código revisado no activa `PRAGMA foreign_keys=ON`, por lo que no conviene afirmar que SQLite garantice esa restricción en cada conexión. `telemetry_tickets.session_id` sirve para correlación y no declara FK; `chatbot_instances` reside en otra base.

### Integración con GLPI

El servicio usa HTTPX y la API REST de GLPI. El flujo documentado incluye apertura de sesión (`initSession`), creación de ticket, asociación del solicitante cuando aplica y cierre (`killSession`); también hay funciones de consulta y seguimiento. La integración real fue reportada como funcional durante el desarrollo. Al actualizar el informe no se pudo repetir la conexión externa porque venció la prueba del entorno usado y estaba pendiente renovar la clave API; las pruebas automatizadas recientes cubrieron el flujo con dobles, incluida una respuesta simulada.

## 7. Tecnologías y herramientas utilizadas

| Categoría | Tecnologías / herramientas | Uso en el proyecto |
|---|---|---|
| Lenguaje y backend | Python, FastAPI, Uvicorn, Pydantic, Pydantic Settings | API asíncrona, validación de datos, configuración y ciclo de vida. |
| Recuperación | ChromaDB, Sentence-Transformers, modelos E5 y Cross-Encoder, LangChain | Índice vectorial, embeddings, reranking, carga y fragmentación documental. |
| Generación | OpenAI, Gemini, Anthropic, Ollama (configurables) | Respuesta con LLM remoto o local según ambiente y disponibilidad. |
| Integración HTTP | HTTPX | Llamadas asíncronas a GLPI, proveedores y pruebas simuladas. |
| Persistencia | SQLite | Telemetría y configuración de instancias. |
| Documentos y multimedia | pypdf, PyMuPDF, python-pptx, Pillow, python-multipart | Lectura de PDF/PPTX e imágenes y recepción de archivos. |
| Seguridad | slowapi, cryptography y validadores propios | Límite de solicitudes, protección de credenciales y validación de cargas/endpoints. |
| Pruebas | Pytest, AsyncMock, HTTPX MockTransport | Pruebas unitarias e integración simulada de servicios externos. |
| Interfaz | HTML/CSS/JavaScript estático | Chat y panel administrativo, servidos por FastAPI. |
| Entorno de desarrollo | Git, GitHub, Visual Studio Code, AntiGravity IDE, PowerShell, Windows, WSL y Docker Desktop | Control de cambios, edición y preparación/ejecución de ambientes de desarrollo. |

**Versiones:** `requirements.txt` declara límites mínimos (`>=`) y no fija un conjunto exacto de versiones. El informe registra Python 3.12 para la ejecución local de pruebas; no debe inventarse una tabla de versiones exactas sin un archivo de bloqueo o una captura del ambiente correspondiente.

**Hardware de desarrollo documentado:** Intel Core Ultra 9 285, 32 GB DDR5, NVIDIA RTX 2000 Ada Generation con 16 GB de VRAM y SSD de 1 TB. Especificación de la estación usada para desarrollo y pruebas, no requisito universal ni servidor productivo.

## 8. Seguridad, privacidad y límites de operación

- El panel administrativo y las APIs sensibles requieren autenticación; la capa también revisa origen para rutas administrativas.
- Las cargas tienen validaciones de extensión/tipo, tamaño máximo configurado y controles antes de guardar o indexar.
- El límite documentado por defecto es 30 solicitudes por minuto; el efecto detrás de un proxy depende de la configuración de red.
- Las credenciales se suministran mediante variables de entorno; no se deben publicar archivos `.env`, tokens de GLPI ni claves de LLM.
- Las claves de proveedores personalizadas por instancia pueden cifrarse con una clave maestra configurada en el servidor.
- Las consultas y fragmentos seleccionados pueden salir al proveedor externo si se configura generación cloud. El corpus y los índices RAG permanecen locales, pero esto no significa que todo el procesamiento permanezca local.
- El RAG principal no filtra documentos por rol. Los filtros temáticos disponibles no sustituyen una política de clasificación y autorización documental.
- La sesión vive en memoria y no sobrevive al reinicio; para escalar horizontalmente se requiere persistencia compartida, además de revisar la coordinación de colas, SQLite, Chroma y modelos.
- La telemetría puede contener consultas, correos o descripciones; su acceso, retención y publicación deben seguir las políticas institucionales y de protección de datos.

## 9. Pruebas y resultados que se pueden citar

Las cifras siguientes corresponden a corridas locales descritas en el informe; no son una evaluación nueva de esta ficha, un SLA ni evidencia de producción.

- **Pruebas automatizadas focalizadas:** una selección de cuatro archivos de pruebas terminó con 71/71 aprobadas después de corregir una regresión detectada inicialmente. No equivale a la suite completa: una corrida amplia aislada recolectó 257 casos, se detuvo tras fallas y una prueba lenta, y excluyó seis pruebas con posibles efectos externos o escrituras reales.
- **Recuperación documental:** la evaluación del 19 de octubre encontró la fuente esperada en 503 de 520 consultas del índice de respaldo (aprox. 96,7 % de presencia de fuente esperada). Eso mide recuperación de referencia; no demuestra que cada respuesta fuera correcta ni que el resultado se reproduzca con otro corpus/índice.
- **Carga histórica:** una prueba del 6 de octubre completó 50/50 respuestas HTTP para 50 sesiones simultáneas, con p50 de 65,13 s y p95 de 70,65 s. El propio informe advierte que no es un SLA ni demuestra capacidad productiva sostenida.
- **Medición por lotes:** 520 consultas con concurrencia 2 registraron p50 7,40 s y p95 13,37 s el 19 de octubre, sobre un índice de respaldo y una configuración anterior al corte.
- **Otra instancia:** una corrida de 55 consultas el 20 de octubre registró mediana de 25,65 s y p95 de 44,98 s; la calidad de esas respuestas quedó pendiente de revisión humana.
- **GLPI:** el funcionamiento externo durante el desarrollo fue reportado por el estudiante; la prueba automatizada actual usa un transporte simulado. Falta repetir la integración externa con acceso vigente y guardar evidencia sanitizada.

### Límites que deben acompañar las métricas

No hay una medición consolidada de tickets institucionales que permita afirmar una reducción real de solicitudes ni una tasa de autoservicio en producción. La presencia de una fuente en las referencias no garantiza exactitud factual. Las métricas dependen del código, corpus, índice, proveedor, modelo, hardware, configuración y criterio evaluador de cada corrida.

## 10. Borrador listo para presentar en un portafolio

### Descripción corta

**UniMon** es un asistente conversacional de soporte TI que combina búsqueda documental local con generación de respuestas configurable. Orienta consultas de autoayuda, diferencia trámites no técnicos y permite escalar incidentes a GLPI. Incluye una interfaz web, administración de fuentes, telemetría y una arquitectura para separar asistentes por dependencia.

### Descripción ampliada

Diseñé e implementé UniMon como solución de práctica profesional para mejorar la orientación inicial de consultas de soporte y procedimientos institucionales. Construí un backend modular en FastAPI que coordina el chat, el estado de conversación, la recuperación aumentada por documentos y la integración REST con GLPI. El componente RAG usa ChromaDB local, embeddings multilingües E5, recuperación léxica y reranking con Cross-Encoder; la generación se configura por proveedor y contempla Ollama local como contingencia. También integré un panel de administración, telemetría SQLite y soporte para asistentes separados por dependencia. La evaluación se realizó con pruebas automatizadas y colecciones locales, con resultados y límites documentados; no se presenta como despliegue productivo ni como reducción demostrada de tickets.

### Responsabilidades para adaptar a primera persona

- Analicé las necesidades de soporte y definí requisitos funcionales y no funcionales verificables.
- Diseñé el flujo conversacional y los modelos de clases, secuencias, actividad, componentes y datos.
- Implementé servicios de backend para chat, reglas de dominio, RAG, proveedores LLM, GLPI, telemetría y administración.
- Integré recuperación vectorial y léxica con reranking y fuentes documentales locales.
- Construí la interfaz web y el panel administrativo para operación y observabilidad.
- Añadí validaciones de carga, control de acceso administrativo y manejo protegido de credenciales.
- Documenté pruebas, métricas, limitaciones técnicas y decisiones de privacidad.

### Habilidades demostradas

Python; diseño de API REST; FastAPI; procesamiento asíncrono; RAG; embeddings; búsqueda vectorial y léxica; reranking; integración con LLM; SQLite; ChromaDB; integración de servicios externos; gestión de estados conversacionales; pruebas automatizadas; seguridad de cargas; telemetría; documentación técnica; evaluación de sistemas de IA.

### Evidencia visual recomendada

Usa capturas sanitizadas del chat, la respuesta con fuente documental, el panel administrativo, los diagramas actualizados del informe y el flujo de radicación de GLPI con datos ficticios. No muestres claves, tokens, correos reales, consultas personales ni tickets institucionales identificables.

## 11. Fuentes dentro del proyecto

- Informe corregido: `Informe_Practica_UniMon_Ajustado_a_Plantilla_Corregido_2026-10-30.docx`.
- Dependencias declaradas: `requirements.txt`.
- Configuración y arranque: `app/config.py`, `app/main.py`, `README.md`.
- Flujo de procesamiento: `docs/flujo_procesamiento_sistema.md`.
- Arquitectura y persistencia: `docs/MANUAL_TECNICO_INTEGRAL.md`.
- Instalación y operación: `docs/REPLICAR_Y_OPERAR_UNIMON.md`.
- Pruebas: carpeta `tests/`.
- Evaluaciones históricas: `reports/`; el informe indica que estos reportes locales están excluidos de Git y deben custodiarse por separado.
