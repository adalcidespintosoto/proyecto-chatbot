# 🎓 UniMon Backend - Asistente Virtual de Soporte Técnico USB

Backend modular y asíncrono desarrollado en **FastAPI** y **Python** para el Asistente Virtual de Soporte Técnico de la **Universidad Simón Bolívar (USB)**, denominado **"UniMon"**.

El sistema integra:
1. **Clasificación de Intenciones & Router de Soporte:** Detecta si la consulta es de tipo informativo (`RAG_QUERY`) o si requiere apertura de ticket (`CREATE_TICKET`), calculando la urgencia institucional y categoría del incidente.
2. **Integración con GLPI REST API:** Conexión asíncrona segura con GLPI (`initSession`, `createTicket`, `killSession` garantizado) para registrar incidentes técnicos de la USB.
3. **Módulo RAG / LLM con Ollama:** Consultas institucionales con modelo `llama3.1` y base de conocimientos especializada (Campus Virtual, WiFi Eduroam, DTI/DST, correo institucional `@usb.ve`).

---

## 🏛️ Estructura del Proyecto

```text
importante/
├── app/
│   ├── __init__.py
│   ├── config.py             # Configuración centralizada con Pydantic Settings (.env)
│   ├── main.py               # Punto de entrada FastAPI, CORS, Lifespans, Docs
│   ├── routers/
│   │   ├── __init__.py
│   │   └── chat.py           # Endpoint POST /api/chat y esquemas de datos Pydantic
│   └── services/
│       ├── __init__.py
│       ├── glpi_service.py   # Cliente asíncrono con httpx para GLPI REST API
│       ├── rag_service.py    # Cliente asíncrono para Ollama + Base de conocimiento USB
│       └── router_logic.py   # Clasificador de intención, tipología y urgencia (1-5)
├── .env                      # Variables de entorno activas
├── .env.example              # Plantilla de variables de entorno
├── requirements.txt          # Dependencias de Python
├── setup.ps1                 # Script PowerShell de instalación y entorno (.venv)
├── run.ps1                   # Script PowerShell para iniciar Uvicorn
└── README.md                 # Documentación completa del backend
```

---

## ⚙️ Requisitos Previos

- **Python 3.10+** instalado en el sistema.
- **Ollama** (Opcional pero recomendado para respuestas de IA generativa con `llama3.1`):
  ```bash
  ollama run llama3.1
  ```
  *(Si Ollama no está activo, el sistema incluye un mecanismo de contingencia institucional automático).*

---

## 🚀 Instalación y Despliegue Rápido (Windows PowerShell)

### 1. Configuración del entorno e instalación
Ejecuta el script automatizado:
```powershell
.\setup.ps1
```
Este script:
- Verifica la presencia de Python.
- Crea el entorno virtual en `.venv`.
- Instala y actualiza todas las dependencias listadas en `requirements.txt`.
- Inicializa el archivo `.env` a partir de `.env.example`.

### 2. Iniciar el servidor FastAPI
Ejecuta:
```powershell
.\run.ps1
```
El servidor quedará disponible en:
- **API Base:** `http://localhost:8000`
- **Documentación Interactiva Swagger UI:** `http://localhost:8000/docs`
- **Documentación ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`

---

## 🔐 Variables de Entorno (`.env`)

Las variables de configuración admitidas por la aplicación son:

| Variable | Descripción | Valor Predeterminado / Ejemplo |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Ambiente de ejecución | `development` |
| `PORT` | Puerto de escucha | `8000` |
| `HOST` | Host de escucha | `0.0.0.0` |
| `GLPI_BASE_URL` | URL de la API REST de GLPI | `https://pruebas.us5.glpi-network.cloud/api.php/v1` |
| `GLPI_APP_TOKEN` | Token de aplicación GLPI | *Configurado en `.env`* |
| `GLPI_USER_TOKEN` | Token de usuario técnico GLPI | *Configurado en `.env`* |
| `OLLAMA_BASE_URL` | URL del servidor local de Ollama | `http://localhost:11434` |
| `LLM_MODEL` | Nombre del modelo LLM | `llama3.1` |

---

## 📡 Especificación de Endpoints

### 1. `POST /api/chat`
Endpoint principal para interacción con el asistente virtual UniMon.

#### **Cuerpo de la Petición (Request Body):**
```json
{
  "message": "No puedo conectarme a la red WiFi eduroam en el edificio MEM",
  "user_data": {
    "name": "Alejandro Hernández",
    "email": "18-10000@usb.ve",
    "usb_id": "18-10000",
    "campus": "Sartenejas",
    "role": "Estudiante"
  },
  "force_ticket": false
}
```

#### **Ejemplo de Respuesta - Consulta RAG (`RAG_QUERY`):**
```json
{
  "intent": "RAG_QUERY",
  "reply": "Para conectarte a la red Wi-Fi institucional eduroam en la USB:\n• SSID: eduroam\n• Usuario: tu_usuario@usb.ve\n• Contraseña: Clave única de acceso...",
  "ticket_details": null,
  "category": "Red WiFi USB / Eduroam / Conectividad",
  "source": "ollama_llama3.1"
}
```

#### **Ejemplo de Respuesta - Creación de Ticket (`CREATE_TICKET`):**
Si el usuario describe una falla persistente (ej: *"El servidor del campus virtual no carga y tengo examen ahorita"*):
```json
{
  "intent": "CREATE_TICKET",
  "reply": "Estimado/a Alejandro Hernández, he generado exitosamente su solicitud de soporte técnico.\n\n📌 Número de Ticket GLPI: #1042\n🏷️ Categoría: Campus Virtual / Moodle USB\n⚡ Nivel de Urgencia: 5/5...",
  "ticket_details": {
    "ticket_id": 1042,
    "category": "Campus Virtual / Moodle USB",
    "urgency": 5,
    "impact": 4,
    "status": "success",
    "tracking_url": null
  },
  "category": "Campus Virtual / Moodle USB",
  "source": "GLPI_REST_API"
}
```

---

### 2. `GET /health`
Verifica el estado y configuración de los servicios conectados.

```json
{
  "status": "healthy",
  "app": "UniMon - Asistente Virtual de Soporte Técnico USB",
  "version": "1.0.0",
  "environment": "development",
  "glpi_endpoint_configured": true,
  "ollama_endpoint": "http://localhost:11434",
  "llm_model": "llama3.1"
}
```

---

## 🏛️ Lógica Institucional de Soporte USB

- **Cálculo de Urgencia (1 a 5):** Evaluado dinámicamente según términos críticos como evaluaciones, exámenes, caídas masivas en laboratorios o inscripciones.
- **Tipologías USB:**
  1. `Campus Virtual / Moodle USB`
  2. `Red WiFi USB / Eduroam / Conectividad`
  3. `Correo Institucional (@usb.ve / Google Workspace)`
  4. `Cuentas USB / Recuperación de Contraseñas / DTI`
  5. `Equipos de Computación / Laboratorios USB`
  6. `Soporte Técnico General USB`
- **Garantía de Sesión GLPI:** El servicio utiliza bloques estructurados `try / finally` para asegurar que tras cualquier petición `initSession` se libere el token mediante `killSession`.
