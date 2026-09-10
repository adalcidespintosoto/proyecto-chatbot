"""
Router para los endpoints de Chat y Soporte Técnico de UniMon (USB).
Define los esquemas de validación Pydantic y procesa las peticiones de los usuarios.
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Request, UploadFile, File
from pydantic import BaseModel, Field

from app.security import require_admin_auth
from app.services.router_logic import router_logic, RouterLogic, EstadoTicket, IntentType
from app.services.glpi_service import glpi_client, GLPIService, GLPIException, is_valid_email
from app.services.rag_service import rag_service, RAGService

logger = logging.getLogger("unimon.chat_router")


router = APIRouter(
    prefix="/api",
    tags=["Chat & Soporte UniMon"]
)


# ==========================================
# Esquemas Pydantic para el Endpoint de Chat
# ==========================================

class ChatRequest(BaseModel):
    """
    Petición enviada al endpoint /api/chat.
    Admite tanto 'mensaje' como 'message' para máxima compatibilidad.
    """
    mensaje: Optional[str] = Field(default=None, description="Mensaje o consulta técnica enviada por el usuario", example="No enciende el computador de la sala 2.")
    message: Optional[str] = Field(default=None, description="Alias en inglés para el mensaje", example="No enciende el computador de la sala 2.")
    session_id: Optional[str] = Field(default="default_session", description="Identificador único de la sesión conversacional", example="sess_12345")

    def get_texto(self) -> str:
        """Obtiene el texto del mensaje asegurando no vacíos."""
        return (self.mensaje or self.message or "").strip()


class ChatResponse(BaseModel):
    """
    Respuesta generada por UniMon según la máquina de estados de Nivel 1 y GLPI.
    """
    tipo: str = Field(..., description="Tipo de respuesta (SALUDO, DIAGNOSTICO, SOLUCIONADO, FINALIZADO, RADICANDO_TICKET, TICKET_CREADO, ERROR)", example="DIAGNOSTICO")
    mensaje: str = Field(..., description="Mensaje de respuesta en lenguaje natural para el usuario en español")
    ticket_id: Optional[Any] = Field(default=None, description="ID del ticket en GLPI si fue generado", example=1042)

    # Campos de compatibilidad para clientes web y quick replies
    intent: Optional[str] = Field(default=None, description="Alias de compatibilidad para tipo")
    reply: Optional[str] = Field(default=None, description="Alias de compatibilidad para mensaje")
    state: Optional[str] = Field(default=None, description="Estado de la sesión conversacional")
    response: Optional[str] = Field(default=None, description="Alias de respuesta")
    quick_replies: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Botones de respuesta rápida")
    ticket_details: Optional[Dict[str, Any]] = Field(default=None, description="Detalles del ticket si fue generado")
    category: Optional[str] = Field(default=None, description="Categoría temática del problema")
    source: Optional[str] = Field(default=None, description="Fuente de la respuesta (GLPI, Ollama, Base de Conocimiento)", example="GLPI_REST_API")
    sources: Optional[List[str]] = Field(default=None, description="Fuentes documentales consultadas en RAG", example=["P-GT-01_Mantenimiento.pdf"])


# ==========================================
# Instancias de Servicios
# ==========================================

from app.services.router_logic import router_logic
from app.services.rag_service import rag_service


# ==========================================
# Rate Limiter & Sanitización
# ==========================================

import time
import re
from fastapi import Request
from app.services.telemetry_service import log_interaction, update_session_status

RATE_LIMIT_BUCKET: Dict[str, List[float]] = {}
MAX_REQUESTS_PER_MINUTE = 25
RATE_LIMIT_WINDOW = 60.0

INJECTION_PATTERNS = [
    r"(?i)\bignora\s+(tus|las|todas\s+las)?\s*instrucciones\b",
    r"(?i)\bolvida\s+(tu|el)?\s*sistema\b",
    r"(?i)\bignore\s+(all\s+)?(previous\s+)?instructions\b",
    r"(?i)\bignore\s+your\s+system\s+prompt\b",
    r"(?i)\bact[uú]a\s+como\s+dan\b",
]


def get_client_ip(request: Optional[Request]) -> str:
    """Extrae la dirección IP real del cliente soportando Cloudflare Tunnel, Nginx y Load Balancers."""
    if not request:
        return "127.0.0.1"
    # Encabezado Cloudflare Tunnel / CDN
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    # Encabezado estándar de proxy
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    # Encabezado X-Real-IP
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def check_rate_limit(key: str):
    """Verifica si la IP ha superado el límite de peticiones por minuto."""
    now = time.time()
    timestamps = RATE_LIMIT_BUCKET.get(key, [])
    # Limpiar marcas de tiempo fuera de la ventana de 60s
    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(timestamps) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes. Por favor espera un momento."
        )
    timestamps.append(now)
    RATE_LIMIT_BUCKET[key] = timestamps


def sanitize_input_text(text: str) -> str:
    """Sanitiza el texto eliminando etiquetas HTML, neutralizando inyecciones de prompt y limitando a 600 caracteres."""
    # 1. Limitar longitud máxima a 600 caracteres
    clean = text[:600].strip()
    # 2. Eliminar etiquetas HTML / script
    clean = re.sub(r'<[^>]*>', '', clean).strip()
    # 3. Neutralizar intentos de inyección de prompt
    for pat in INJECTION_PATTERNS:
        clean = re.sub(pat, "[consulta filtrada]", clean)
    return clean.strip()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesar mensaje del usuario con Chatbot de Nivel 1 y Router de Intención",
    description="Orquesta el diagnóstico proactivo de Nivel 1 con RAG (Llama 3.1) o la captura conversacional y radicación de tickets en GLPI."
)
async def process_chat(request: ChatRequest, raw_request: Request = None) -> ChatResponse:
    """
    Endpoint principal para interacción con el Asistente Virtual UniMon.
    Aplica limitación de tasa (25 req/min por IP), sanitización de entrada y registro de telemetría.
    """
    raw_texto = request.get_texto()
    if not raw_texto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El campo 'mensaje' no puede estar vacío."
        )

    session_id = request.session_id or "default_session"

    # Aplicar Rate Limiting estricto por IP real del cliente
    client_ip = get_client_ip(raw_request)
    check_rate_limit(client_ip)

    # Sanitizar y validar longitud del mensaje (máx 600 chars)
    texto = sanitize_input_text(raw_texto)
    if not texto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje ingresado no contiene texto válido tras la sanitización."
        )

    logger.info(f"Procesando mensaje para session_id '{session_id}' (longitud: {len(texto)} chars): '{texto}'")

    # Medir tiempo de procesamiento (latencia)
    t0 = time.time()
    resultado = await router_logic.procesar_mensaje(mensaje=texto, session_id=session_id)
    latency_ms = (time.time() - t0) * 1000

    tipo = resultado.get("tipo", "DIAGNOSTICO")
    state = resultado.get("state", tipo)
    mensaje_resp = resultado.get("mensaje", "")
    ticket_id = resultado.get("ticket_id")
    source = resultado.get("source", "UniMon")
    sources = resultado.get("sources") or []
    prompt_tokens = resultado.get("prompt_tokens", 0) or 0
    eval_tokens = resultado.get("eval_tokens", 0) or 0

    # Obtener rol del usuario registrado en la sesión
    session_obj = router_logic.get_session(session_id)
    user_role = getattr(session_obj, "user_role", "general") or "general"

    # Registrar telemetría de la interacción
    try:
        log_interaction(
            session_id=session_id,
            role=user_role,
            query=texto,
            bot_response=mensaje_resp,
            intent=tipo,
            source=source,
            docs=sources,
            latency_ms=round(latency_ms, 2),
            prompt_tokens=prompt_tokens,
            eval_tokens=eval_tokens,
            feedback=resultado.get("feedback", "NONE")
        )

        # Actualizar estado de resolución / escalado
        if tipo in ["FINALIZADO", "SOLUCIONADO"] or state in ["FINALIZADO", "SOLUCIONADO"]:
            update_session_status(session_id, "FINALIZADO", escalated=False)
        elif tipo in ["TICKET_CREADO"] or ticket_id is not None:
            update_session_status(session_id, "TICKET_CREADO", escalated=True)
        elif tipo in ["RADICANDO_TICKET"] or state in ["RADICANDO_TICKET", "PIDIENDO_NOMBRE"]:
            update_session_status(session_id, "RADICANDO_TICKET", escalated=True)
        elif tipo in ["CANCELADO"] or state in ["CANCELADO"]:
            update_session_status(session_id, "CANCELADO", escalated=False)
    except Exception as e:
        logger.warning(f"Error al registrar telemetría: {e}")

    return ChatResponse(
        tipo=tipo,
        mensaje=mensaje_resp,
        ticket_id=ticket_id,
        intent=tipo,
        reply=mensaje_resp,
        state=state,
        response=mensaje_resp,
        quick_replies=resultado.get("quick_replies", []),
        ticket_details=resultado.get("ticket_details"),
        category=resultado.get("category"),
        source=source,
        sources=sources
    )





# ==========================================
# Endpoints de Administración de Documentos RAG
# ==========================================

from fastapi import UploadFile, File
from pathlib import Path
from app.config import get_settings
from scripts.ingest_multimodal_docs import ingest_multimodal


@router.post(
    "/admin/upload",
    tags=["Administración RAG"],
    dependencies=[Depends(require_admin_auth)],
    summary="Subir documento PDF o PPTX e indexar automáticamente",
    description="Recibe un archivo PDF o PPTX, lo almacena en ./data/docs/ y ejecuta la reindexación multimodal automática inmediata en ChromaDB (con interpretación visual de imágenes si el Vision-LLM está disponible)."
)
async def upload_document(
    file: UploadFile = File(..., description="Archivo PDF o PPTX institucional a incorporar")
):
    """
    Guarda el archivo subido y dispara la reindexación multimodal y recarga automática del vector store.
    Soporta archivos PDF (.pdf) y PowerPoint (.pptx).
    """
    allowed_extensions = (".pdf", ".pptx")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo se admiten documentos en formato PDF (.pdf) o PowerPoint (.pptx)."
        )

    settings = get_settings()
    docs_dir = Path(settings.docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    target_path = docs_dir / Path(file.filename).name

    # Guardar archivo en disco validando tamaño máximo
    try:
        content = await file.read()
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"El archivo excede el tamaño máximo permitido de {settings.max_upload_size_mb} MB."
            )

        with open(target_path, "wb") as f:
            f.write(content)
        logger.info(f"Nuevo documento guardado en: {target_path} ({len(content) / 1024:.1f} KB)")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error al escribir archivo en disco: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo guardar el archivo: {str(exc)}"
        )

    # Indexar únicamente el nuevo archivo con pipeline multimodal incremental
    success = ingest_multimodal(file_path=str(target_path))
    if success:
        rag_service.reload_vector_store()
        return {
            "status": "success",
            "message": f"Documento '{file.filename}' subido e indexado exitosamente en ChromaDB (pipeline incremental multimodal).",
            "filename": file.filename,
            "size_kb": round(len(content) / 1024, 2)
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El archivo se guardó, pero ocurrió un error durante la indexación vectorial."
        )


@router.post(
    "/admin/reindex",
    tags=["Administración RAG"],
    dependencies=[Depends(require_admin_auth)],
    summary="Forzar reindexación multimodal completa de documentos",
    description="Ejecuta la limpieza y reindexación multimodal de todos los PDFs y PPTX en ./data/docs/ con interpretación visual de imágenes y recarga ChromaDB en memoria."
)
async def trigger_reindex():
    """
    Dispara manualmente el pipeline de ingesta multimodal completa y actualiza la base vectorial activa.
    """
    success = ingest_multimodal(wipe_db=True)
    if success:
        rag_service.reload_vector_store()
        return {
            "status": "success",
            "message": "Base vectorial ChromaDB reindexada con pipeline multimodal y recargada exitosamente."
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al procesar la reindexación multimodal de documentos."
        )


