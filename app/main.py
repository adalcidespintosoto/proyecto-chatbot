"""
Punto de entrada principal para la aplicación FastAPI del Asistente Virtual UniMon (USB).
Configura middlewares de CORS, eventos de ciclo de vida (lifespan), endpoints de salud y documentación.
"""

import asyncio
import ipaddress
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.config import get_settings
from app.routers import chat, analytics, admin_router, whatsapp
from app.services.router_logic import RouterLogic
from app.services.telemetry_service import init_telemetry_db
from app.services.rag_service import rag_service, get_embedding_model, get_reranker_model
from app.services.golden_cache_service import init_golden_cache

# Configuración básica de logging estructurado. La captura a archivo es optativa
# (UNIMON_LOG_FILE) y se mantiene junto al proyecto para facilitar auditorías locales.
log_handlers = [logging.StreamHandler()]
log_file = os.getenv("UNIMON_LOG_FILE", "").strip()
if log_file:
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handlers.append(logging.FileHandler(log_path, encoding="utf-8"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=log_handlers,
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
    provider = settings.llm_provider.strip().lower()
    provider_models = {
        "openai": settings.openai_model,
        "gemini": settings.gemini_model,
        "ollama": settings.llm_model,
    }
    logger.info("Proveedor LLM: %s | Modelo: %s", provider, provider_models.get(provider, "no configurado"))
    logger.info("=============================================================")

    # Inicializar Base de Datos de Telemetría
    init_telemetry_db()

    # Precalienta los componentes locales de recuperación y la Golden Cache.
    try:
        logger.info("Pre-cargando modelos RAG y Golden Cache en RAM (Warmup)...")
        get_embedding_model()
        _ = rag_service.vector_store
        get_reranker_model()
        init_golden_cache()
        logger.info(
            "Embeddings, Cross-Encoder y Golden Cache locales listos; generación LLM configurada en %s (%s).",
            provider,
            provider_models.get(provider, "no configurado"),
        )
    except Exception as e:
        logger.warning(f"Aviso durante el pre-calentamiento de modelos: {e}")

    # Tarea en segundo plano para limpieza periódica de sesiones inactivas (TTL)
    async def cleanup_loop():
        while True:
            try:
                await asyncio.sleep(300)  # Cada 5 minutos
                cleaned = RouterLogic.clean_inactive_sessions(ttl_minutes=20)
                if cleaned > 0:
                    logger.info("[TTL Background] %s sesiones inactivas purgadas.", cleaned)
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


from slowapi import Limiter, _rate_limit_exceeded_handler
from starlette.requests import Request
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

def rate_limit_ip(request: Request) -> str:
    """Usa la IP de Cloudflare solo cuando el salto inmediato es el túnel local."""
    peer = request.client.host if request.client else "unknown"
    if peer in {"127.0.0.1", "::1"}:
        forwarded = request.headers.get("cf-connecting-ip", "")
        try:
            return str(ipaddress.ip_address(forwarded))
        except ValueError:
            pass
    return peer


limiter = Limiter(key_func=rate_limit_ip, default_limits=["30/minute"])

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend oficial del Asistente Virtual de Soporte Técnico para la Universidad Simón Bolívar (USB). Provee conexión con GLPI REST API y módulo RAG con proveedor LLM configurable.",
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc",
    openapi_url=None if settings.environment == "production" else "/openapi.json",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configuración de CORS para permitir consumo desde frontends web y móviles oficiales
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "https://www.unisimon.edu.co"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    """Agrega cabeceras de seguridad HTTP estándar a todas las respuestas."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Content-Security-Policy"] = "object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'"
    if request.url.path.startswith(("/api/analytics", "/api/admin", "/api/chat", "/admin")):
        response.headers["Cache-Control"] = "no-store"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response

# Inclusión de Routers
app.include_router(chat.router)
app.include_router(analytics.router)
app.include_router(admin_router.router)
app.include_router(whatsapp.router)

# Ruta estática para la interfaz gráfica del Chatbot
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
class PublicStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        if Path(path).name.lower() == "admin.html":
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return await super().get_response(path, scope)

if os.path.exists(STATIC_DIR):
    app.mount("/static", PublicStaticFiles(directory=STATIC_DIR), name="static")


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
    }
