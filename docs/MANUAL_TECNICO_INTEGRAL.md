# MANUAL TÉCNICO INTEGRAL DE ARQUITECTURA, OPERACIÓN Y RESOLUCIÓN DE FALLOS
## Asistente Virtual de Soporte Técnico TI N1 - UniMon (Universidad Simón Bolívar)

---

## 1. FICHA TÉCNICA Y STACK TECNOLÓGICO

| Componente | Tecnología / Librería | Versión Requerida | Propósito Técnico |
| :--- | :--- | :--- | :--- |
| **Lenguaje Base** | Python | `>= 3.10` (Recomendado 3.11 / 3.12) | Entorno de ejecución principal del backend. |
| **Framework Web** | FastAPI | `>= 0.110.0` | Servidor REST asíncrono de alto rendimiento (ASGI). |
| **Seguridad API** | slowapi | `>= 0.1.9` | Rate Limiting global (30 req/min) para prevención DoS. |
| **Servidor ASGI** | Uvicorn (`[standard]`) | `>= 0.28.0` | Servidor HTTP concurrente para FastAPI. |
| **Validación de Datos** | Pydantic / Pydantic-Settings | `>= 2.6.0` / `>= 2.2.0` | Modelado y validación de esquemas y variables de entorno. |
| **Motor LLM Local** | Ollama (`unimon:8b`) | `>= 0.3.0` | LLM local basado en Llama 3.1 8B cuantizado en 4 bits (`Q4_K_M`). |
| **Vision-LLM (Ingesta)** | Ollama (`llama3.2-vision:11b`)| `>= 0.3.0` | Extracción de texto y contexto de diagramas, flujos y capturas. |
| **Base Vectorial** | ChromaDB / LangChain-Chroma | `>= 0.5.0` / `>= 0.1.0` | Persistencia y búsqueda vectorial multilingüe (HNSW + SQLite). |
| **Embeddings Semánticos** | `BAAI/bge-m3` / `multilingual-e5-base`| `sentence-transformers >= 2.6.0` | Generación de representaciones vectoriales densas y sparse. |
| **Reranker Semántico** | `BAAI/bge-reranker-large` / Cross-Encoder | `sentence-transformers >= 2.6.0` | Re-ordenamiento y cálculo de relevancia contextual cruzada. |
| **Mesa de Ayuda (ITSM)** | GLPI REST API | `v9.5.x` / `v10.0.x` / Cloud | Integración bidireccional para apertura y consulta de tickets TI. |
| **Base Telemetría/KPIs** | SQLite3 Local | Nativo Python (`data/analytics.db`) | Persistencia de sesiones, métricas de resolución, latencias y tokens. |
| **Clustering y Analítica** | Scikit-Learn | `>= 1.4.0` | Detección de brechas de conocimiento (DBSCAN / K-Means). |
| **Procesamiento Documentos**| PyMuPDF (fitz), PyPDF, python-pptx | `>= 1.23.0`, `>= 4.0.0` | Extracción y chunking de PDF, DOCX, PPTX e imágenes. |

---

## 2. ESTRUCTURA DEL PROYECTO Y RESPONSABILIDADES

```text
proyecto-chatbot/
│
├── app/                                 # Paquete principal de la aplicación
│   ├── config.py                        # Configuración con Pydantic Settings (.env)
│   ├── main.py                          # Entrada ASGI, middlewares CORS, lifespan y montaje de rutas
│   ├── routers/                         # Controladores REST API
│   │   ├── chat.py                      # Endpoint POST /api/chat y flujo conversacional
│   │   ├── analytics.py                 # Endpoint GET /api/analytics/kpis, clusters y exportación DPO
│   │   └── analytics_router.py          # Alias de compatibilidad para el router de analítica
│   ├── services/                        # Capa de lógica de negocio y servicios especializados
│   │   ├── router_logic.py              # Máquina de estados conversacional, orquestador y slot-filling
│   │   ├── router_service.py            # Clasificador semántico y léxico de intenciones
│   │   ├── rag_service.py               # Búsqueda vectorial, filtrado por rol, reranker y generación LLM
│   │   ├── glpi_service.py              # Cliente HTTP para autenticación y radicación de tickets GLPI
│   │   ├── golden_cache_service.py      # Memoria rápida de respuestas resueltas (ChromaDB golden_resolved_qa)
│   │   ├── telemetry_service.py         # Registro de eventos, latencias y cálculo de KPIs en SQLite
│   │   ├── clustering_service.py        # Agrupamiento de consultas y detección de vacíos documentales
│   │   └── normalizer_service.py        # Limpieza léxica, sinónimos y lematización de consultas
│   ├── static/                          # Frontend SPA integrado
│   │   └── index.html                   # Interfaz de usuario interactiva, chat y modal de KPIs
│   └── utils/                           # Utilidades auxiliares y helpers
│
├── chroma_db/                           # Directorio persistente de ChromaDB (Embeddings institucionales)
│   ├── [UUIDs]/                         # Índices HNSW binarios por colección
│   └── chroma.sqlite3                   # Metadatos y registros vectoriales
│
├── data/                                # Datos dinámicos y base de conocimiento institucional
│   ├── docs/                            # Documentos fuente (.pdf, .docx, .pptx)
│   └── analytics.db                     # Base de datos SQLite de telemetría y auditoría
│
├── docs/                                # Documentación arquitectónica del sistema
│   ├── flujo_procesamiento_sistema.md   # Diagramas exhaustivos de flujo y decisiones
│   └── MANUAL_TECNICO_INTEGRAL.md       # Este documento
│
├── scripts/                             # Scripts de administración por lotes
│   ├── ingest_multimodal_docs.py        # Pipeline de extracción, OCR/Vision y vectorización
│   ├── apply_document_taxonomy.py       # Clasificación y asignación de metadatos por rol
│   ├── clean_golden_cache.py            # Purgado y mantenimiento de la memoria rápida
│   └── update_chroma_metadata.py        # Actualización incremental de colecciones vectoriales
│
├── tests/                               # Suite de pruebas automatizadas (Pytest)
│   ├── test_telemetry_analytics.py      # Pruebas de métricas, SQLite y endpoints de observabilidad
│   ├── test_role_quick_replies.py       # Pruebas de filtrado por rol y botones interactivos
│   ├── test_incremental_ingest.py       # Pruebas de ingesta por hashes SHA-256
│   └── test_clustering.py               # Pruebas de DBSCAN y detección de brechas
│
├── Modelfile                            # Definición y system prompt del modelo Ollama unimon:8b
├── requirements.txt                     # Lista de dependencias de Python
├── setup.ps1                            # Script PowerShell de instalación y configuración automática
├── run.ps1                              # Script PowerShell para iniciar Uvicorn en producción/desarrollo
└── pytest.ini                           # Configuración de pruebas unitarias
```

---

## 3. FLUJO DE EJECUCIÓN Y CICLO DE VIDA DEL MENSAJE

```
                        [ USUARIO EN LA WEB ]
                                  │
                                  │ POST /api/chat (Rate Limit 30 req/min)
                                  ▼
                     [ FastAPI: app/main.py ]
                                  │ (Verificación CORS)
                                  ▼
             [ Orquestador: app/services/router_logic.py ]
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
[ REGLAS GLOBALES ]       [ CLASIFICADOR ]           [ MÁQUINA ESTADOS ]
1. Cancelación            - Saludo                   - PIDIENDO_ROL
2. Caso Solucionado       - Directorio / Canales TI  - DIAGNOSTICO (RAG)
3. Fuera de Dominio       - Hardware / Físico        - RADICANDO_TICKET
4. Confirmaciones         - Trámite / Software       - SOLUCIONADO / FIN
      │                           │                           │
      └───────────────────────────┼───────────────────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              ▼                                       ▼
     ¿Requiere RAG N1?                       ¿Requiere Ticket?
              │                                       │
     [ golden_cache_service ]               [ glpi_service.py ]
     - Similitud >= 0.90                    - Auth initSession
     - Inyección Few-Shot LLM               - POST /Ticket
              │ (Miss)                      - POST /Ticket_User
     [ rag_service.py ]                     - Cierre sesión
     - Multi-Query Expansion
     - Filtro por Rol                       
     - ChromaDB Top-8
     - Cross-Encoder Reranker Top-3
     - LLM unimon:8b (Temp 0.0)
     - Clean LLM Response (Output Guard)
              │
              └───────────────────┬───────────────────┘
                                  │
                                  ▼
             [ Telemetría: telemetry_service.py ]
             - data/analytics.db (latencia, tokens, kpis)
                                  │
                                  ▼
                        [ RESPUESTA AL USUARIO ]
```

---

## 4. VARIABLES DE ENTORNO Y CONFIGURACIÓN (.env)

El archivo `.env` en la raíz del proyecto controla todo el comportamiento operativo:

```ini
# Configuración del Servidor FastAPI
APP_NAME="UniMon - Asistente Virtual de Soporte Tecnico USB"
APP_VERSION="1.0.0"
ENVIRONMENT="development"        # development / production
PORT=8000
HOST="0.0.0.0"
DEBUG=True

# Configuración de GLPI REST API
GLPI_BASE_URL="https://pruebas.us5.glpi-network.cloud/api.php/v1"
GLPI_APP_TOKEN="4l3q2EMwU12pdL0RCUtxcI8botN7tODo58XxD3MJ"
GLPI_USER_TOKEN="1YfLnz0S6OIjs4yFV2rIPk9PMXIndhW7YpBagyCI"
GLPI_TIMEOUT=15.0

# Configuración de Ollama (LLM Local)
OLLAMA_BASE_URL="http://localhost:11434"
LLM_MODEL="unimon:8b"
OLLAMA_TIMEOUT=45.0

# Configuración de Vision-LLM (Para ingesta de diagramas y capturas)
VISION_MODEL="llama3.2-vision:11b"
VISION_TIMEOUT=120.0
VISION_MAX_IMAGE_SIZE=1024
VISION_MIN_IMAGE_KB=15

# Configuración de ChromaDB y Embeddings
CHROMA_DB_DIR="./chroma_db"
DOCS_DIR="./data/docs"
EMBEDDING_MODEL="intfloat/multilingual-e5-base"
```

---

## 5. CATÁLOGO DE APIS Y ENDPOINTS REST

### 5.1. Chat Conversacional
* **Ruta:** `POST /api/chat`
* **Descripción:** Procesa el mensaje del usuario, evalúa el estado conversacional, consulta RAG o escala a GLPI.
* **Request Body:**
```json
{
  "session_id": "sess_web_123456",
  "mensaje": "¿Cómo restablezco mi contraseña de correo institucional?",
  "message": "¿Cómo restablezco mi contraseña de correo institucional?"
}
```
* **Response Body (200 OK):**
```json
{
  "respuesta": "Para restablecer tu contraseña institucional:\n1. Ingresa al portal...\n¿Te sirvieron estos pasos o prefieres que radique un caso de soporte técnico por ti?",
  "tipo": "DIAGNOSTICO",
  "ticket_id": null,
  "source": "UniMon_RAG",
  "sources": ["Restablecimiento de contraseña.pdf"],
  "quick_replies": [
    {"label": "✅ ¡Me sirvió, muchas gracias!", "payload": "RESOLVED"},
    {"label": "❌ No me sirvió, radicar ticket", "payload": "RETRY_DIAGNOSIS"}
  ]
}
```

### 5.2. Métricas y KPIs de Observabilidad
* **Ruta:** `GET /api/analytics/kpis`
* **Descripción:** Retorna el consolidado ejecutivo de desempeño, latencias, distribución por rol, top documentos y preguntas.
* **Response Body (200 OK):**
```json
{
  "status": "success",
  "data": {
    "resolution_rate": 80.0,
    "escalation_rate": 20.0,
    "resolved_count": 4,
    "escalated_count": 1,
    "avg_latency_ms": 4405.0,
    "tokens_in": 269942,
    "tokens_out": 28518,
    "total_tokens": 298460,
    "total_sessions": 5,
    "total_queries": 375,
    "role_distribution": {
      "general": 3,
      "profesor": 1,
      "administrativo": 1
    },
    "top_documents": [
      {
        "name": "Caracterización del Proceso Institucional de Gestión de TI.pdf",
        "count": 17
      }
    ],
    "top_queries": [
      {
        "query": "se me olvido la clave del portal y ya voy en quinto semestre",
        "count": 8
      }
    ]
  }
}
```

### 5.3. Agrupamiento Semántico y Brechas Documentales
* **Ruta:** `GET /api/analytics/clusters?min_samples=2&eps=0.25`
* **Descripción:** Agrupa semánticamente las dudas de usuarios e identifica temas sin suficiente documentación de soporte.

### 5.4. Exportador de Preferencias DPO
* **Ruta:** `GET /api/analytics/export-dpo-dataset?format=jsonl`
* **Descripción:** Descarga pares `(prompt, chosen, rejected)` para reentrenamiento de modelos de lenguaje.

---

## 6. INSTALACIÓN Y PUESTA EN MARCHA PASO A PASO

### Paso 1: Configurar el Entorno Virtual
Abrir PowerShell en la raíz del proyecto y ejecutar:
```powershell
.\setup.ps1
```
*(Crea `.venv`, instala dependencias de `requirements.txt` y copia `.env.example` a `.env` si no existe).*

### Paso 2: Crear el Modelo en Ollama
Asegurarse de que el servicio de Ollama esté corriendo y crear el modelo personalizado:
```powershell
ollama pull llama3.1:8b
ollama create unimon:8b -f ./Modelfile
```

### Paso 3: Ingesta de Documentos a ChromaDB
Colocar los archivos institucionales en `data/docs/` y ejecutar el pipeline multimodal:
```powershell
.venv\Scripts\python.exe scripts/ingest_multimodal_docs.py
```
Para enriquecer los metadatos de taxonomía por roles:
```powershell
.venv\Scripts\python.exe scripts/apply_document_taxonomy.py
```

### Paso 4: Iniciar el Servidor
Ejecutar el script de arranque:
```powershell
.\run.ps1
```
El sistema estará disponible en:
* **Interfaz de Usuario Web:** `http://localhost:8000`
* **Documentación OpenAPI interactiva (Swagger):** `http://localhost:8000/docs`

---

## 7. GUÍA DE DIAGNÓSTICO Y RESOLUCIÓN DE FALLOS (TROUBLESHOOTING RUNBOOK)

### 7.1. Fallo de Conexión o Timeout con Ollama (`http://localhost:11434`)
* **Síntoma:** El chat se queda esperando o responde con error de timeout tras 45 segundos.
* **Causa:** El daemon de Ollama no está iniciado o el modelo `unimon:8b` no está creado.
* **Solución Paso a Paso:**
  1. Verificar si Ollama responde en consola:
     ```powershell
     curl http://localhost:11434/api/tags
     ```
  2. Si no responde, iniciar el servicio de Ollama en Windows desde el menú inicio o ejecutando `ollama serve`.
  3. Verificar que el modelo `unimon:8b` figure en la lista:
     ```powershell
     ollama list
     ```
  4. Si no aparece, recrearlo con `ollama create unimon:8b -f Modelfile`.

---

### 7.2. Fallo de Autenticación o Radicación con GLPI REST API
* **Síntoma:** Al confirmar la radicación de un caso, el bot informa que ocurrió un problema al conectar con GLPI.
* **Causa:** `GLPI_APP_TOKEN` o `GLPI_USER_TOKEN` caducados o URL errónea.
* **Solución Paso a Paso:**
  1. Verificar en `.env` que `GLPI_BASE_URL` termine en `/api.php/v1` (o la ruta correspondiente de la versión de GLPI).
  2. Comprobar la sesión ejecutando una prueba manual:
     ```python
     from app.services.glpi_service import glpi_client
     token = glpi_client.init_session()
     print("Token obtenido:", token)
     ```
  3. Si retorna `None` o `401 Unauthorized`, ingresar al panel de administración de GLPI -> *Configuración* -> *General* -> *API* y regenerar el *App Token* y el *User Token*.

---

### 7.3. Errores de ChromaDB o Base de Datos Bloqueada
* **Síntoma:** Error de lectura/escritura en `./chroma_db` o fallos de concurrencia en `chroma.sqlite3`.
* **Causa:** Proceso previo bloqueando el archivo o colección corrupta por apagado forzado.
* **Solución Paso a Paso:**
  1. Cerrar todas las terminales de Python/Uvicorn activas.
  2. Si la base de datos vectorial necesita regenerarse completamente:
     ```powershell
     .venv\Scripts\python.exe scripts/ingest_multimodal_docs.py --wipe
     .venv\Scripts\python.exe scripts/apply_document_taxonomy.py
     ```
  3. Si la memoria rápida presenta respuestas desactualizadas:
     ```powershell
     .venv\Scripts\python.exe scripts/clean_golden_cache.py
     ```

---

### 7.4. Fallo de Memoria / Carga de Embeddings en GPU/CPU
* **Síntoma:** `CUDA out of memory` al cargar `BAAI/bge-m3` o `BAAI/bge-reranker-large`.
* **Causa:** GPU con VRAM insuficiente (< 6 GB) para albergar tanto Ollama como los transformadores de PyTorch.
* **Solución Paso a Paso:**
  1. El sistema cuenta con fallback automático a CPU.
  2. Para forzar modo CPU estricto, definir la variable de entorno antes de iniciar:
     ```powershell
     $env:CUDA_VISIBLE_DEVICES = "-1"
     ```
  3. Asegurarse de que el modelo Ollama esté en cuantización 4 bits (`Q4_K_M`) para un consumo menor a 5.5 GB de VRAM.

---

### 7.5. Base de Datos de Telemetría Bloqueada (`data/analytics.db`)
* **Síntoma:** `sqlite3.OperationalError: database is locked`.
* **Causa:** Múltiples escrituras simultáneas en SQLite sin contexto transaccional corto.
* **Solución Paso a Paso:**
  1. Todas las operaciones en `telemetry_service.py` utilizan manejadores de contexto `with sqlite3.connect(...)`.
  2. Si el archivo `data/analytics.db-journal` o `analytics.db-wal` queda bloqueado, detener Uvicorn y reiniciar el proceso.
  3. Verificar integridad de la base:
     ```powershell
     .venv\Scripts\python.exe -c "import sqlite3; conn=sqlite3.connect('data/analytics.db'); print(conn.execute('PRAGMA integrity_check;').fetchall()); conn.close()"
     ```

---

### 7.6. Sesiones Conversacionales Desincronizadas o Atascadas
* **Síntoma:** El bot insiste en pedir datos de ticket o mantiene un estado anterior.
* **Causa:** La sesión en memoria `TicketSession` conservó un estado previo no finalizado.
* **Solución Paso a Paso:**
  1. Enviar el comando `"cancelar"` o `"inicio"` en el chat. La Regla Global 1 reiniciará el estado de la sesión a `PIDIENDO_ROL` o `INICIO`.
  2. En el navegador, abrir una nueva pestaña (genera un nuevo `unimon_session_id` en `sessionStorage`) o limpiar el almacenamiento de sesión de las herramientas de desarrollador.
  3. El limpiador en segundo plano de `main.py` purga automáticamente las sesiones con inactividad superior a 30 minutos.

---

## 8. PRUEBAS AUTOMATIZADAS (TEST SUITE)

Para validar la integridad de todo el backend, ejecutar Pytest utilizando el entorno virtual:

```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```

* **`test_telemetry_analytics.py`**: Comprueba registro de interacciones, cálculo de KPIs, tokens, latencias y endpoints REST.
* **`test_role_quick_replies.py`**: Comprueba normalización de roles, botones interactivos y filtros de acceso a documentos.
* **`test_incremental_ingest.py`**: Comprueba cálculo de hashes SHA-256 para no re-indexar documentos sin cambios.
* **`test_clustering.py`**: Comprueba agrupamiento con DBSCAN y exportación de datasets DPO.

---

### 7.7. Bloqueos por Rate Limiting (HTTP 429 Too Many Requests)
* **Síntoma:** El chat en la web deja de responder o la API retorna código 429.
* **Causa:** El middleware de seguridad `slowapi` detectó que la IP del usuario envió más de 30 peticiones en menos de un minuto.
* **Solución Paso a Paso:**
  1. El bloqueo es temporal. Esperar exactamente 60 segundos y la IP será liberada automáticamente por el servidor.
  2. Si estás realizando pruebas de estrés (ej. JMeter, K6) y necesitas deshabilitarlo, comenta el decorador `@limiter.limit("30/minute")` en el archivo `app/routers/chat.py`.

---

## 8. PANEL DE ADMINISTRACIÓN Y GESTIÓN DE CONOCIMIENTO (Admin Console)

El **UniMon Admin Console** es una interfaz web secreta e interactiva construida para los ingenieros y coordinadores de TI, permitiéndoles auditar el comportamiento del bot y gestionar el corpus documental en tiempo real. 

### 8.1. Acceso al Panel
Para acceder al panel, el administrador debe posicionarse en la pantalla de chat web (`http://localhost:8000`) y presionar el atajo de teclado discreto: **`Ctrl + Alt + A`**. Esto abrirá una nueva pestaña redirigiendo a la ruta segura `/admin.html`.

### 8.2. Dashboard de Métricas (KPIs)
La pantalla principal presenta cuatro cuadros de mando impulsados por `telemetry_service.py` y `analytics.db`:
* **Tasa de Resolución:** Porcentaje de consultas resueltas exitosamente ("✅ Sí, me funcionó") versus las que requirieron escalar a ticket.
* **Tiempo de Respuesta (Latencia):** Promedio en milisegundos que tarda Ollama en generar la respuesta técnica.
* **Consumo de Tokens:** Volumen de palabras procesadas (ideal para calcular costos si a futuro se migra a un LLM de pago como OpenAI o Claude).
* **Distribución de Tráfico y Documentos Top:** Muestra qué manuales PDF son los más consultados y por qué roles institucionales.

### 8.3. Detección de Brechas y Generador IA de Procedimientos (Draft Procedure)
El sistema agrupa automáticamente con Inteligencia Artificial (Algoritmo DBSCAN) aquellas preguntas que los usuarios hicieron pero que el bot no supo responder porque **no existía documento**. 
* **Botón 🪄 (Draft Procedure):** Al lado de cada "Brecha documental", el administrador puede presionar este botón con el ícono de IA. El panel enviará una orden secreta a Ollama para que analice la pregunta no resuelta y redacte un **Borrador de Manual Institucional** de forma automática y técnica.
* **Descartar Preguntas:** Si la pregunta huérfana era basura (ej. "chistes", "ayuda con tarea"), el administrador puede presionar el botón 🗑️ para **Descartar** la métrica, indicando un motivo (Fuera de Contexto, Lenguaje Inapropiado).

### 8.4. Gestor Documental (Indexación Inteligente)
En la sección de Documentos, el administrador puede subir nuevos archivos (PDF, DOCX) y administrar la base vectorial.
* **Botón de Subida Inteligente (Smart Indexing):** Compara los hashes (SHA-256) de los párrafos nuevos contra los que ya existen en ChromaDB. Sólo sube los fragmentos "novedosos" para no saturar ni inflar la base de datos de embeddings innecesariamente.
* **Botón de Indexación Forzada (Force Indexing):** Salta la validación de redundancia y reemplaza a la fuerza toda la información.
* **Borrado de Documentos:** Permite purgar un manual viejo de la base de datos haciendo clic en el botón de la papelera junto al archivo, liberando al RAG de información obsoleta.
