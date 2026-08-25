"""
Punto de entrada principal para la aplicación FastAPI del Asistente Virtual UniMon (USB).
Configura middlewares de CORS, eventos de ciclo de vida (lifespan), endpoints de salud y documentación.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.config import get_settings
from app.routers import chat, analytics
from app.services.router_logic import RouterLogic
from app.services.telemetry_service import init_telemetry_db

# Configuración básica de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("unimon.main")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejador de ciclo de vida de la aplicación.
    Ejecuta tareas al iniciar y al detener el servidor.
    """
    logger.info("=============================================================")
    logger.info(f"Iniciando {settings.app_name} v{settings.app_version}")
    logger.info(f"Entorno: {settings.environment} | GLPI URL: {settings.glpi_base_url}")
    logger.info(f"Ollama URL: {settings.ollama_base_url} | Modelo: {settings.llm_model}")
    logger.info("=============================================================")

    # Inicializar Base de Datos de Telemetría
    init_telemetry_db()

    # Tarea en segundo plano para limpieza periódica de sesiones inactivas (TTL)
    async def cleanup_loop():
        while True:
            try:
                await asyncio.sleep(300)  # Cada 5 minutos
                cleaned = RouterLogic.clean_inactive_sessions(ttl_minutes=20)
                if cleaned > 0:
                    logger.info(f"[TTL Background] {cleaned} sesiones inactivas reiniciadas a IDLE.")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[TTL Background] Error en tarea de limpieza: {e}")

    cleanup_task = asyncio.create_task(cleanup_loop())

    yield

    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("Deteniendo el servicio UniMon Backend...")


# Inicialización de la aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend oficial del Asistente Virtual de Soporte Técnico para la Universidad Simón Bolívar (USB). Provee conexión con GLPI REST API y módulo RAG con Ollama.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configuración de CORS para permitir consumo desde frontends web y móviles
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de Routers
app.include_router(chat.router)
app.include_router(analytics.router)

# Ruta estática para la interfaz gráfica del Chatbot
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get(
    "/",
    tags=["Interfaz Gráfica"],
    summary="Interfaz web de UniMon Chatbot",
    description="Retorna la aplicación web interactiva para conversar con UniMon y probar soporte GLPI."
)
async def root():
    """
    Ruta raíz que sirve la interfaz gráfica de usuario interactiva.
    """
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "Bienvenido al Backend del Asistente Virtual de Soporte Técnico UniMon (USB)",
        "version": settings.app_version,
        "docs_url": "/docs",
        "health_check": "/health",
        "status": "online"
    }


@app.get(
    "/health",
    tags=["Salud y Monitoreo"],
    summary="Health Check del Servicio",
    description="Verifica el estado de disponibilidad del backend y sus configuraciones."
)
async def health_check():
    """
    Endpoint de chequeo de salud y configuración activa.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "glpi_endpoint_configured": bool(settings.glpi_base_url and settings.glpi_app_token),
        "ollama_endpoint": settings.ollama_base_url,
        "llm_model": settings.llm_model
    }
