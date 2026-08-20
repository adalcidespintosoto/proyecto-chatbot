# 🎓 UniMon Backend - Asistente Virtual de Soporte Técnico y Gestión de TI (Unisimon)

Backend modular y asíncrono desarrollado en **FastAPI** y **Python** para el Asistente Virtual Oficial de Soporte Técnico y Gestión de TI de la **Universidad Simón Bolívar (Sedes Barranquilla y Cúcuta, Colombia)**, denominado **"UniMon"**.

El sistema integra:
1. **Clasificación Semántica de Intenciones & Router de Soporte:** Detecta si la consulta es de tipo informativo/procedimental (`RAG_QUERY`) o si requiere apertura de ticket (`CREATE_TICKET`), calculando la urgencia institucional y categoría del incidente.
2. **Motor RAG Local con ChromaDB + Ollama (`llama3.1:8b`):** Base de conocimientos vectorizada basada en los procedimientos institucionales de TI (`P-GT-01`, `P-GT-07`, `P-GT-08`, `P-GT-10`, `P-GT-11`, `P-GT-13`) con embeddings `intfloat/multilingual-e5-base` y $k=4$ fragmentos recuperados.
3. **Integración con GLPI REST API:** Conexión asíncrona segura con GLPI Cloud (`initSession`, `createTicket`, asociación de actor solicitante vía `Ticket_User` y cierre garantizado `killSession`).
4. **Carga y Reindexación Dinámica en Caliente:** Endpoints y controles visuales para subir nuevos documentos PDF, reindexar la base vectorial y recargar la memoria sin reiniciar el servidor.
5. **Interfaz Web Interactiva:** Cliente visual integrado con selectores de sede (*Barranquilla* y *Cúcuta*), atajos rápidos a procedimientos y chat en tiempo real.

---

## 🏛️ Estructura del Proyecto

```text
proyecto-chatbot/
├── app/
│   ├── __init__.py
│   ├── config.py             # Configuración centralizada con Pydantic Settings (.env)
│   ├── main.py               # Punto de entrada FastAPI, CORS, Lifespans, Static Files
│   ├── routers/
│   │   ├── __init__.py
│   │   └── chat.py           # Endpoints /api/chat, /api/admin/upload y /api/admin/reindex
│   ├── services/
│   │   ├── __init__.py
│   │   ├── glpi_service.py   # Cliente asíncrono para GLPI REST API (Tickets y Actores)
│   │   ├── rag_service.py    # Pipeline RAG con ChromaDB, Embeddings y Ollama
│   │   └── router_logic.py   # Clasificador de intención, categorías y urgencia (1-5)
│   └── static/
│       └── index.html        # Interfaz Web del Chatbot y panel de administración
├── data/
│   └── docs/                 # Carpeta de almacenamiento de procedimientos PDF
├── chroma_db/                # Base de datos vectorial persistente (ChromaDB)
├── scripts/
│   └── ingest_docs.py        # Script de ingestión limpia, chunking y vectorización
├── .env                      # Variables de entorno activas
├── .env.example              # Plantilla de variables de entorno
├── requirements.txt          # Dependencias de Python
├── run.ps1                   # Script PowerShell para iniciar Uvicorn
├── setup.ps1                 # Script PowerShell de instalación del entorno (.venv)
├── test_rag.py               # Script de prueba del motor RAG
├── test_glpi.py              # Script de prueba de creación de tickets en GLPI
└── README.md                 # Documentación completa del proyecto
```

---

## ⚙️ Requisitos Previos

- **Python 3.10+** (recomendado Python 3.11 / 3.12 / 3.14).
- **Ollama** con el modelo `llama3.1:8b` descargado:
  ```bash
  ollama run llama3.1:8b
  ```
  *(Si Ollama no está activo o disponible, el sistema incluye un mecanismo de contingencia institucional automático con las guías de Unisimon).*

---

## 🚀 Instalación y Despliegue Rápido (Windows PowerShell)

### 1. Configuración del entorno e instalación
Ejecuta el script automatizado:
```powershell
.\setup.ps1
```
Este script:
- Crea el entorno virtual en `.venv`.
- Instala todas las dependencias listadas en `requirements.txt`.
- Inicializa el archivo `.env` a partir de `.env.example`.

### 2. Ingestión y vectorización de documentos PDF
Para procesar los PDFs institucionales ubicados en `./data/docs/`:
```powershell
.\.venv\Scripts\python.exe scripts/ingest_docs.py
```

### 3. Iniciar el servidor FastAPI
Ejecuta:
```powershell
.\run.ps1
```
O directamente con el ejecutable del entorno virtual:
```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
```

El servidor quedará disponible en:
- **Interfaz Web del Chatbot:** [http://localhost:8000](http://localhost:8000)
- **Documentación Interactiva Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Documentación ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 🔐 Variables de Entorno (`.env`)

| Variable | Descripción | Valor Predeterminado / Ejemplo |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Ambiente de ejecución | `development` |
| `PORT` | Puerto de escucha | `8000` |
| `HOST` | Host de escucha | `0.0.0.0` |
| `GLPI_BASE_URL` | URL de la API REST de GLPI | `https://pruebas.us5.glpi-network.cloud/api.php/v1` |
| `GLPI_APP_TOKEN` | Token de aplicación GLPI | *Configurado en `.env`* |
| `GLPI_USER_TOKEN` | Token de usuario técnico GLPI | *Configurado en `.env`* |
| `OLLAMA_BASE_URL` | URL del servidor Ollama | `http://localhost:11434` |
| `LLM_MODEL` | Modelo LLM en Ollama | `llama3.1:8b` |
| `CHROMA_DB_DIR` | Ruta de almacenamiento ChromaDB | `./chroma_db` |
| `DOCS_DIR` | Directorio de documentos PDF | `./data/docs` |
| `EMBEDDING_MODEL` | Modelo de Embeddings | `intfloat/multilingual-e5-base` |

---

## 📡 Especificación de Endpoints

### 1. `POST /api/chat` (Fase 4: Chatbot Nivel 1 Proactivo & Router)
Procesa el mensaje del usuario de forma conversacional mediante una máquina de estados por `session_id`.

#### **Cuerpo de la Petición (Request Body):**
```json
{
  "session_id": "sess_user_12345",
  "mensaje": "El proyector del auditorio no da video y parpadea"
}
```

#### **Esquema de Respuesta (`ChatResponse`):**
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `tipo` | `str` | Estado / Intención (`SALUDO`, `DIAGNOSTICO`, `SOLUCIONADO`, `RADICANDO_TICKET`, `TICKET_CREADO`, `ERROR`) |
| `mensaje` | `str` | Respuesta en lenguaje natural generada por el bot |
| `ticket_id` | `int \| null` | ID del ticket en GLPI una vez completada la radicación |

#### **Flujo Conversacional de Nivel 1:**
1. **Diagnóstico Proactivo (`tipo: "DIAGNOSTICO"`):** El bot entrega de 2 a 3 pasos de descarte basados en RAG y pregunta si funcionó o si persiste.
2. **Caso Solucionado (`tipo: "SOLUCIONADO"`):** Si el usuario indica que se arregló (*"gracias, ya funcionó"*), se limpia la sesión y se cierra cordialmente.
3. **Falla Persiste y Slot-Filling (`tipo: "RADICANDO_TICKET"`):** Si el problema continúa, se solicita en orden:
   - **Nombre completo**
   - **Correo institucional**
   - **Ubicación (Sede, Bloque, Sala o Laboratorio)**
   - **Placa o Activo del equipo** (*permite "N/A"*)
4. **Radicación Oficial (`tipo: "TICKET_CREADO"`):** Al completar los 4 datos, se crea el ticket en GLPI, se asocia al solicitante y se retorna el `ticket_id`.


---

### 2. `POST /api/admin/upload`
Permite subir un nuevo archivo PDF institucional en formato multipart (`file`), guardarlo en `./data/docs/`, reindexar ChromaDB automáticamente y recargar la memoria en caliente.

#### **Ejemplo con cURL:**
```bash
curl -X POST "http://localhost:8000/api/admin/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./data/docs/Nuevo_Procedimiento.pdf"
```

---

### 3. `POST /api/admin/reindex`
Fuerza la reindexación de todos los PDFs existentes en `./data/docs/` y actualiza ChromaDB en memoria.

#### **Ejemplo con cURL:**
```bash
curl -X POST "http://localhost:8000/api/admin/reindex"
```

---

### 4. `GET /health`
Verifica el estado y configuración de los servicios conectados.

```json
{
  "status": "healthy",
  "app": "UniMon - Asistente Virtual de Soporte Técnico USB",
  "version": "1.0.0",
  "environment": "development",
  "glpi_endpoint_configured": true,
  "ollama_endpoint": "http://localhost:11434",
  "llm_model": "llama3.1:8b"
}
```

---

## 🏛️ Canales y Procedimientos Institucionales (Unisimon)

- **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: `(605) 3444333` Ext. `8003` y `8004`.
- **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: `(607) 5827070` Ext. `129`.
- **Procedimientos TI Soportados:**
  - `P-GT-01`: Mantenimiento de Equipos de Cómputo.
  - `P-GT-02`: Gestión de Cuentas y Accesos a Sistemas de Información.
  - `P-GT-07`: Protección de Código Malicioso (Antivirus / Malware).
  - `P-GT-08`: Aseguramiento de Servicios en la Red.
  - `P-GT-10`: Generación y Restauración de Backup de la Información.
  - `P-GT-11`: Atención de Incidencias y Requerimientos Kactus y Seven.
  - `P-GT-12`: Gestión de Cuentas de Usuario en Kactus o Seven.
  - `P-GT-13`: Gestión de Requerimientos de Recursos y Soluciones Tecnológicas.
  - `P-GT-14`: Gestión de Actualizaciones de Versiones en Kactus y Seven.

