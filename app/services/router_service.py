"""
Servicio de Clasificación de Intenciones, Enrutamiento Semántico y Feedback para UniMon.
Maneja la clasificación semántica con LLM (AUTOSERVICIO vs SOPORTE_FISICO),
la desambiguación de respuestas del usuario tras diagnósticos e instructivos (Nivel 1),
ciclos de reintento/aclaración antes de escalar y transición a toma de datos para reporte.
"""

import re
import json
import logging
import httpx
from typing import Optional, Dict, Any, Union

from app.config import Settings

logger = logging.getLogger("unimon.router_service")

# Configuración de Ollama para el Router Semántico
try:
    _settings = Settings()
    OLLAMA_URL = f"{_settings.ollama_base_url.rstrip('/')}/api/generate"
    MODEL_NAME = _settings.llm_model
except Exception:
    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL_NAME = "unimon:8b"

SYSTEM_ROUTER_PROMPT = """Eres el clasificador de intenciones de soporte de TI de la Universidad Simón Bolívar.
Tu labor es clasificar el mensaje del usuario en UNA de dos categorías:

1. AUTOSERVICIO: Trámites en plataformas web, SIAAF, Teams, Portal Estudiantes, Kactus, Seven, subida de notas, registro de inasistencias ("fallas a clase"), consulta de calificaciones, restablecimiento de contraseñas, certificados, solicitudes de préstamos/asignación de equipos de cómputo o preguntas sobre canales de atención/contacto.
2. SOPORTE_FISICO: Averías de hardware, periféricos rotos (mouse, teclado, monitor), cables de red dañados, puntos de red sin servicio, computadores que no prenden/sin video, impresoras atascadas o solicitudes explícitas de revisión técnica presencial por daño físico en oficina/laboratorio.

REGLAS CLAVE:
- "Fallas a clase", "reportar fallas", "subir notas" o "calificaciones" son SIEMPRE de tipo AUTOSERVICIO.
- Preguntas sobre canales de atención, contactos, o cómo solicitar/prestar equipos de cómputo son SIEMPRE de tipo AUTOSERVICIO.

Responde ÚNICAMENTE un objeto JSON válido con la clave 'categoria':
{"categoria": "AUTOSERVICIO"} o {"categoria": "SOPORTE_FISICO"}"""

PROMPT_HARDWARE_DIRECT = (
    "Para fallas físicas, averías de hardware, puntos de red o problemas con torniquetes y equipos de cómputo, "
    "el personal técnico de la Dirección de TI realiza la revisión y atención presencial en sitio.\n\n"
    "📞 **Canales Directos de Soporte TI:**\n"
    "• **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. `8003 / 8004`\n"
    "• **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. `129`\n\n"
    "¿Deseas que radique una solicitud de soporte técnico en GLPI para que un técnico atienda tu caso en sitio?"
)

HARDWARE_QUICK_REPLIES = [
    {"label": "🎫 Radicar Ticket en GLPI", "payload": "CREATE_TICKET"},
    {"label": "✅ Tengo la información", "payload": "RESOLVED"}
]

# =============================================================================
# DEFINICIÓN DE ROLES INSTITUCIONALES Y BOTONES INTERACTIVOS (QUICK REPLIES)
# =============================================================================

ROLE_QUICK_REPLIES = [
    {"label": "🎓 Estudiante", "payload": "estudiante"},
    {"label": "👨‍🏫 Profesor", "payload": "profesor"},
    {"label": "💼 Administrativo", "payload": "administrativo"},
    {"label": "🌐 Otros / Visitante", "payload": "otros"}
]

ROLE_SYNONYMS = {
    "estudiante": "estudiante",
    "alumno": "estudiante",
    "alumna": "estudiante",
    "alumnos": "estudiante",
    "alumnas": "estudiante",
    "pregrado": "estudiante",
    "posgrado": "estudiante",
    "profesor": "profesor",
    "profesora": "profesor",
    "profesores": "profesor",
    "profesoras": "profesor",
    "docente": "profesor",
    "docentes": "profesor",
    "catedratico": "profesor",
    "catedrático": "profesor",
    "catedraticos": "profesor",
    "catedráticos": "profesor",
    "administrativo": "administrativo",
    "administrativa": "administrativo",
    "administrativos": "administrativo",
    "administrativas": "administrativo",
    "funcionario": "administrativo",
    "funcionaria": "administrativo",
    "funcionarios": "administrativo",
    "funcionarias": "administrativo",
    "colaborador": "administrativo",
    "colaboradora": "administrativo",
    "colaboradores": "administrativo",
    "empleado": "administrativo",
    "empleada": "administrativo",
    "empleados": "administrativo",
    "trabajador": "administrativo",
    "trabajadora": "administrativo",
    "otros": "otros",
    "otro": "otros",
    "visitante": "otros",
    "visitantes": "otros",
    "aspirante": "otros",
    "aspirantes": "otros",
    "egresado": "otros",
    "egresada": "otros",
    "egresados": "otros",
    "externo": "otros",
    "externa": "otros",
    "externos": "otros"
}


def normalize_role(user_input: str) -> str:
    """Normaliza el rol ingresado por el usuario usando ROLE_SYNONYMS."""
    msg = user_input.lower().strip()
    for key, role_val in ROLE_SYNONYMS.items():
        if re.search(rf"\b{key}\b", msg):
            return role_val
    return "otros"


async def classify_request_intent_async(user_message: str, user_role: str = "general") -> str:
    """
    Clasificador semántico asíncrono con LLM local para determinar AUTOSERVICIO vs SOPORTE_FISICO.
    """
    prompt = f"Rol de usuario: {user_role}\nConsulta del usuario: \"{user_message}\"\nClasificación JSON:"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "system": SYSTEM_ROUTER_PROMPT,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 20
                    },
                    "format": "json"
                },
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                raw_resp = data.get("response", "{}")
                result = json.loads(raw_resp)
                categoria = result.get("categoria", "AUTOSERVICIO").strip().upper()
                if categoria in ["AUTOSERVICIO", "SOPORTE_FISICO"]:
                    return categoria
    except Exception as e:
        logger.warning(f"Error en clasificador semántico LLM async ({e}). Fallback por defecto a AUTOSERVICIO.")
        
    return "AUTOSERVICIO"


def classify_request_intent(user_message: str, user_role: str = "general") -> str:
    """
    Clasificador semántico síncrono con LLM local para determinar AUTOSERVICIO vs SOPORTE_FISICO.
    """
    prompt = f"Rol de usuario: {user_role}\nConsulta del usuario: \"{user_message}\"\nClasificación JSON:"
    
    try:
        response = httpx.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "system": SYSTEM_ROUTER_PROMPT,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 20
                },
                "format": "json"
            },
            timeout=5.0
        )
        if response.status_code == 200:
            data = response.json()
            raw_resp = data.get("response", "{}")
            result = json.loads(raw_resp)
            categoria = result.get("categoria", "AUTOSERVICIO").strip().upper()
            if categoria in ["AUTOSERVICIO", "SOPORTE_FISICO"]:
                return categoria
    except Exception as e:
        logger.warning(f"Error en clasificador semántico LLM ({e}). Fallback por defecto a AUTOSERVICIO.")
        
    return "AUTOSERVICIO"


def is_physical_hardware_request(user_message: str, user_role: str = "general") -> bool:
    """
    Determina si la solicitud del usuario es de soporte físico/hardware usando el clasificador semántico.
    """
    return classify_request_intent(user_message, user_role) == "SOPORTE_FISICO"


RESOLVED_INTENTS = ["RESOLVED", "resolved"]
RETRY_INTENTS = ["RETRY_DIAGNOSIS", "retry_diagnosis", "RETRY", "retry"]
TICKET_EXPLICIT_INTENTS = ["CREATE_TICKET", "create_ticket", "TICKET", "ticket"]

# Alias de compatibilidad hacia atrás
TICKET_INTENTS = TICKET_EXPLICIT_INTENTS + RETRY_INTENTS


def handle_feedback_transition(
    user_message: str, 
    current_state: str = "DIAGNOSTICO", 
    session: Optional[Union[dict, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Evalúa la retroalimentación del usuario de forma EXCLUSIVA a través de los payloads exactos de los botones:
    - 'RESOLVED': Éxito -> FINALIZADO
    - 'RETRY_DIAGNOSIS': Reintento -> DIAGNOSTICO (pregunta por error/paso)
    - 'CREATE_TICKET': Radicación -> RADICANDO_TICKET (solicita Nombre Completo)
    
    Cualquier otro texto libre de lenguaje natural retorna None para continuar fluidamente en el pipeline RAG.
    """
    if session is None:
        session = {}

    msg_raw = (user_message or "").strip()
    msg_upper = msg_raw.upper()

    # Obtener contador de intentos
    if isinstance(session, dict):
        attempts = session.get("diagnosis_attempts", 1)
    else:
        attempts = getattr(session, "diagnosis_attempts", getattr(session, "intentos_diagnostico", 1)) or 1

    def _set_attempts(val: int):
        if isinstance(session, dict):
            session["diagnosis_attempts"] = val
        else:
            if hasattr(session, "diagnosis_attempts"):
                session.diagnosis_attempts = val
            if hasattr(session, "intentos_diagnostico"):
                session.intentos_diagnostico = val

    def _update_session_state(new_state: str):
        if isinstance(session, dict):
            session["state"] = new_state
            if new_state == "RADICANDO_TICKET":
                session["ticket_data"] = {}
        elif hasattr(session, "estado"):
            from app.services.router_logic import EstadoTicket
            if new_state == "FINALIZADO":
                session.estado = EstadoTicket.FINALIZADO
            elif new_state == "RADICANDO_TICKET":
                session.estado = EstadoTicket.PIDIENDO_NOMBRE
                session.nombre = None
                session.correo = None
                session.descripcion = None
            elif new_state == "DIAGNOSTICO":
                session.estado = EstadoTicket.DIAGNOSTICO

    # 1. Caso resuelto satisfactoriamente (exclusivo por payload)
    if msg_upper in ["RESOLVED"]:
        _update_session_state("FINALIZADO")
        _set_attempts(0)
        return {
            "response": "¡Excelente! Me alegra haberte ayudado a resolverlo. Si necesitas ayuda con otra plataforma o trámite institucional, aquí estaré. ¡Que tengas un excelente día! 👋",
            "mensaje": "¡Excelente! Me alegra haberte ayudado a resolverlo. Si necesitas ayuda con otra plataforma o trámite institucional, aquí estaré. ¡Que tengas un excelente día! 👋",
            "state": "FINALIZADO",
            "tipo": "FINALIZADO",
            "source": "UniMon_Feedback_Success",
            "quick_replies": []
        }

    # 2. Solicitud directa de reporte (exclusivo por payload)
    if msg_upper in ["CREATE_TICKET", "TICKET"]:
        _update_session_state("RADICANDO_TICKET")
        return {
            "response": "Con gusto te ayudo a radicar el caso. Para iniciar, por favor indícame tu **Nombre Completo**:",
            "mensaje": "Con gusto te ayudo a radicar el caso. Para iniciar, por favor indícame tu **Nombre Completo**:",
            "state": "RADICANDO_TICKET",
            "tipo": "RADICANDO_TICKET",
            "source": "UniMon_Escalacion_Ticket",
            "quick_replies": []
        }

    # 3. No funcionó / Reintento (exclusivo por payload) - Escala al segundo intento
    if msg_upper in ["RETRY_DIAGNOSIS", "RETRY"]:
        if attempts < 2:
            _set_attempts(attempts + 1)
            _update_session_state("DIAGNOSTICO")
            return {
                "response": "Lamento que no haya funcionado. ¿Podrías indicarme qué mensaje de error te aparece en pantalla o en qué paso exacto te detuviste para orientarte mejor?",
                "mensaje": "Lamento que no haya funcionado. ¿Podrías indicarme qué mensaje de error te aparece en pantalla o en qué paso exacto te detuviste para orientarte mejor?",
                "state": "DIAGNOSTICO",
                "tipo": "DIAGNOSTICO",
                "source": "UniMon_Diagnostico_Retry",
                "quick_replies": [
                    {"label": "🎫 Generar reporte a soporte", "payload": "CREATE_TICKET"}
                ]
            }
        else:
            # Si ya intentó 4 veces, ofrecer directamente la toma de datos
            _update_session_state("RADICANDO_TICKET")
            return {
                "response": "Con gusto te ayudo a radicar el caso. Para iniciar, por favor indícame tu **Nombre Completo**:",
                "mensaje": "Con gusto te ayudo a radicar el caso. Para iniciar, por favor indícame tu **Nombre Completo**:",
                "state": "RADICANDO_TICKET",
                "tipo": "RADICANDO_TICKET",
                "source": "UniMon_Escalacion_Ticket",
                "quick_replies": []
            }

    # 4. Cualquier otro mensaje de texto no es feedback por payload -> Flujo libre RAG
    return None
