"""
Lógica de Enrutamiento, Clasificación de Intenciones y Chatbot Proactivo de Nivel 1 para UniMon (USB).
Maneja el ciclo de diagnóstico multi-turno de Nivel 1 (hasta 3 intentos), discriminación estricta de fallas técnicas
vs. solicitudes de préstamos de equipos físicos, detección y asignación de rol del usuario (Estudiante / Docente / Funcionario),
cero alucinaciones con transición forzada a OFRECIENDO_RADICACION ante falta de documentación relevante, flujo universal de
cancelación y rechazo explícito ("no", "cancelar"), entrega de canal oficial por correo con plantilla estructurada y
radicación por Slot-Filling universal simplificado en secuencia estricta de 3 pasos (Nombre -> Correo -> Descripción).
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List
from enum import Enum
from pydantic import BaseModel, Field

from app.services.rag_service import (
    rag_service,
    is_out_of_domain_response,
    is_out_of_domain_query,
    MENSAJE_NO_DOCUMENTADO,
    MENSAJE_FUERA_DE_DOMINIO
)
from app.services.glpi_service import glpi_client, is_valid_email
from app.services.router_service import (
    handle_feedback_transition, 
    RESOLVED_INTENTS, 
    RETRY_INTENTS, 
    TICKET_EXPLICIT_INTENTS, 
    TICKET_INTENTS,
    PROMPT_HARDWARE_DIRECT,
    HARDWARE_QUICK_REPLIES,
    classify_request_intent,
    classify_request_intent_async,
    is_physical_hardware_request,
    is_informative_procedure_query,
    ROLE_QUICK_REPLIES,
    ROLE_SYNONYMS,
    normalize_role
)
from app.services.golden_cache_service import search_golden_case, save_golden_case, invalidate_golden_cache_entry

logger = logging.getLogger("unimon.router_logic")


class EstadoTicket(str, Enum):
    IDLE = "IDLE"
    PIDIENDO_ROL = "PIDIENDO_ROL"
    DIAGNOSTICO = "DIAGNOSTICO"
    OFRECIENDO_RADICACION = "OFRECIENDO_RADICACION"
    PIDIENDO_NOMBRE = "PIDIENDO_NOMBRE"
    PIDIENDO_CORREO = "PIDIENDO_CORREO"
    PIDIENDO_DESCRIPCION = "PIDIENDO_DESCRIPCION"
    CONFIRMANDO_SEGUIMIENTO = "CONFIRMANDO_SEGUIMIENTO"
    SOLUCIONADO = "SOLUCIONADO"
    CANCELADO = "CANCELADO"
    TICKET_CREADO = "TICKET_CREADO"
    ERROR = "ERROR"
    FINALIZADO = "FINALIZADO"
    # Campos de compatibilidad hacia atrás
    PIDIENDO_UBICACION = "PIDIENDO_UBICACION"
    PIDIENDO_ACTIVO = "PIDIENDO_ACTIVO"


class IntentType(str, Enum):
    SALUDO = "SALUDO"
    DIAGNOSTICO = "DIAGNOSTICO"
    PIDIENDO_ROL = "PIDIENDO_ROL"
    OFRECIENDO_RADICACION = "OFRECIENDO_RADICACION"
    RADICANDO_TICKET = "RADICANDO_TICKET"
    SOLUCIONADO = "SOLUCIONADO"
    CANCELADO = "CANCELADO"
    TICKET_CREADO = "TICKET_CREADO"
    ERROR = "ERROR"
    FUERA_DE_DOMINIO = "FUERA_DE_DOMINIO"
    FINALIZADO = "FINALIZADO"


class CategoriaSolicitud(str, Enum):
    SOFTWARE = "Software"
    HARDWARE = "Hardware"
    REDES = "Redes"
    OTRO = "Otro"


class TicketSession(BaseModel):
    session_id: str
    estado: EstadoTicket = EstadoTicket.IDLE
    falla: Optional[str] = None
    descripcion: Optional[str] = None
    nombre: Optional[str] = None
    correo: Optional[str] = None
    categoria: CategoriaSolicitud = CategoriaSolicitud.SOFTWARE
    category_name: Optional[str] = "Soporte Técnico y Gestión de TI Unisimon"
    urgency: int = 3
    impact: int = 3
    intentos_diagnostico: int = 0
    diagnosis_attempts: int = 1
    max_intentos_diagnostico: int = 4
    intentos_fallback: int = 0
    intentos_fallidos: int = 0
    ticket_id: Optional[int] = None
    existing_ticket_id_today: Optional[int] = None
    decision_mismo_o_nuevo: bool = False
    last_interaction: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_role: Optional[str] = None
    pending_query: Optional[str] = None
    last_user_query: Optional[str] = None
    last_bot_response: Optional[str] = None
    ubicacion: Optional[str] = None
    activo: Optional[str] = None


# Almacén de sesiones en memoria indexado por session_id
ticket_sessions: Dict[str, TicketSession] = {}

# Almacén de historial conversacional en memoria indexado por session_id (últimos mensajes)
session_history: Dict[str, List[Dict[str, str]]] = {}

# Mensaje de Calificación de Rol Obligatoria (Gating Estricto)
MENSAJE_PIDIENDO_ROL = (
    "⚠️ Para brindarte el procedimiento exacto según tu perfil y sede, primero debes seleccionar tu rol institucional:"
)

# Saludos simples y cortesía
GREETING_PATTERNS = [
    r"^hola\b", r"^buenos d[ií]as\b", r"^buenas tardes\b", r"^buenas noches\b",
    r"^buenas\b", r"^hey\b", r"^saludos\b", r"^[¿?]?c[oó]mo est[aá]s\b",
    r"^[¿?]?qu[eé] tal\b", r"^buen d[ií]a\b", r"^hi\b", r"^hello\b"
]

# Patrones de Cancelación Universal y Rechazo durante el flujo de radicación
CANCEL_PATTERNS = [
    "cancelar", "cancela", "ya no", "no gracias", "olvidalo", "olvídalo",
    "dejalo asi", "déjalo así", "no quiero", "no deseo", "no", "nop", "noup",
    "cancelar radicación", "cancelar radicacion", "cancelar ticket", "rechazar"
]

CANCEL_REGEX = [
    r"\b(cancelar|cancela|ya\s+no|no\s+gracias|olvidalo|olv[ií]dalo|dejalo\s+asi|d[eé]jalo\s+as[ií]|no\s+quiero|no\s+deseo|cancelar\s+ticket|cancelar\s+radicaci[oó]n|no\s+lo\s+radiques|no\s+radiques)\b"
]

MENSAJE_CANCELACION = (
    "Entendido, he cancelado el proceso. Si prefieres comunicarte directamente con los canales oficiales de soporte técnico TI:\n\n"
    "📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | Tel: `(605) 3444333` Ext. 8003/8004\n"
    "📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | Tel: `(607) 5827070` Ext. 129\n\n"
    "Si necesitas ayuda con otro procedimiento o falla técnica, aquí estaré. 👋"
)

# Términos que identifican fallas técnicas, daños o problemas de soporte (NUNCA deben tratarse como préstamos)
FAILURE_AND_SUPPORT_TERMS = [
    "problema", "dañado", "dañada", "daño", "falla", "fallando", "solucionar",
    "ayuda", "no prende", "no funciona", "no enciende", "lento", "lenta",
    "pantalla azul", "bloqueado", "bloqueada", "parpadea", "error",
    "no da video", "se apaga", "se reinicia", "reparar", "reparacion", "reparación",
    "revisar", "arreglo", "arreglar", "soporte", "descompuesto", "descompuesta",
    "intermitente", "luz roja", "desconectado", "desconectada", "sin internet",
    "sin red", "sin sonido", "no escucha", "no suena", "no proyecta", "se trabó",
    "se congela", "se cuelga", "pantalla negra", "no da señal", "mal contacto",
    "no carga", "mover el cable", "moverle el cable", "se traba", "datos incorrectos",
    "clave incorrecta", "no me deja entrar", "no entra", "clave invalida",
    "datos invalidos", "no me coge la clave", "se cierra solo", "bota error",
    "arroja error", "suspendido", "no sincroniza", "esta caido", "está caído",
    "sin wifi", "cable pelado", "no arranca", "muerto"
]

# Verbos y raíces de solicitud o reserva de préstamo físico
LOAN_REQUEST_VERBS = [
    r"\b(prest\w+|pr[eé]st\w+|solicit\w+|asign\w+|apart\w+|reserv\w+|alquil\w+|pedir|pido|necesito\s+que\s+me\s+den|requiero\s+que\s+me\s+presten|como\s+hago\s+para\s+tener|quiero\s+solicitar|donde\s+me\s+comunico\s+para|d[oó]nde\s+me\s+comunico\s+para|a\s+donde\s+escribo\s+para|a\s+d[oó]nde\s+escribo\s+para)\b"
]

# Nombres de recursos y equipos físicos institucionales
EQUIPMENT_NOUNS = [
    r"\b(equipo[s]?(\s+de\s+c[oó]mputo)?|recurso[s]?\s+f[ií]sico[s]?|pc|pcs|compu|computador|computadores|computadora|computadoras|port[aá]til|port[aá]tiles|laptop|laptops|ordenador|torre|pantalla|pantallas|monitor|monitores|display|micr[oó]fono|micr[oó]fonos|diadema|diademas|aud[ií]fonos|auriculares|parlante|parlantes|altavoz|altavoces|tablet|tablets|tableta|tabletas|ipad|ipads|video\s*beam|videobeam|proyector|proyectores|beamer|canon|cañ[oó]n|sala|sala\s+de\s+c[oó]mputo|auditorio|laboratorio|cargador|fuente|cable\s+de\s+poder)\b"
]

# Mensaje estructurado directo para solicitudes de préstamo / asignación de equipos
MENSAJE_SOLICITUD_EQUIPOS = (
    "Para solicitar préstamos o asignación de equipos de cómputo y recursos físicos (micrófonos, tablets, portátiles, proyectores), debes tramitar la solicitud con la Dirección de TI a través de los canales oficiales:\n\n"
    "📧 **Canales de Atención:**\n"
    "• **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | PBX: (605) 3444333 Ext. 8003 / 8004\n"
    "• **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129\n\n"
    "📋 **Plantilla sugerida para tu correo:**\n"
    "• **Asunto:** Solicitud de Préstamo de [Equipo] - [Tu Nombre]\n"
    "• **Cuerpo del mensaje:**\n"
    "  - **Equipo solicitado y cantidad:** [Ej: 1 Micrófono inalámbrico]\n"
    "  - **Motivo / Evento académico:** [Descripción breve]\n"
    "  - **Fecha y Horario requerido:** [Fecha y rango de horas]\n"
    "  - **Ubicación / Aula:** [Sede, Bloque, Salón]\n\n"
    "¿Deseas que radique este requerimiento de servicio directamente por ti ahora mismo?"
)

# Respuestas de resolución / cierre ("ya no necesito", "ya pude", "ya funcionó", "listo", etc.)
SOLVED_PATTERNS = [
    r"\bya\s+no\s+(?:necesito|requiero|es\s+necesario)\b",
    r"^(?:no\s+)?ya\s+gracias$",
    r"^(?:no\s+)?ya\s+qued[oó]$",
    r"^(?:no\s+)?ya\s+resolv[ií]$",
    r"\bya\s+pude\b",
    r"\bya\s+pudo\b",
    r"\bya\s+funcion[oó]\b",
    r"\bya\s+funsion[oó]\b",
    r"\bya\s+sirve\b",
    r"\bya\s+sirvi[oó]\b",
    r"\bya\s+cirvi[oó]\b",
    r"^listo(?:,\s*gracias)?$",
    r"\bse\s+solucion[oó]\b",
    r"\bse\s+solusion[oó]\b",
    r"\bsolucionado\b",
    r"\bresuelto\b",
    r"\bqued[oó]\s+bien\b",
    r"\bya\s+qued[oó]\b",
    r"\bse\s+arregl[oó]\b",
    r"\bmuchas\s+gracias\b",
    r"^gracias$",
    r"^grasias$",
    r"^excelente(?:,\s*gracias)?$",
    r"^perfecto(?:,\s*gracias)?$",
    r"\bya\s+prendi[oó]\b",
    r"\bya\s+conect[oó]\b",
    r"\bya\s+dio\s+video\b",
    r"\btodo\s+bien\b",
    r"\btodo\s+en\s+orden\b",
    r"\bya\s+resolv[ií]\b",
]

# Patrones explícitos de persistencia de fallas en diagnóstico
EXPLICIT_FAIL_PATTERNS = [
    r"\bno\s+(me\s+)?(funcion[oó]|funsion[oó]|sirvi[oó]|sirbi[oó]|cirvi[oó]|sirve|sirbe|cirve|vale)\b",
    r"\bno\s+se\s+(solucion[oó]|solusion[oó]|arregl[oó]|pudo)\b",
    r"\b(sigue|sige)\s+(igual|fallando|bloquead[oa]|el\s+error|sin\s+funcionar|sin\s+servir|el\s+problema|ca[ií]do)\b",
    r"\bno\s+me\s+deja\b",
    r"\bno\s+pude\s+(entrar|ingresar|acceder|iniciar|solucionarlo)\b",
    r"\bno\s+puedo\s+(entrar|ingresar|acceder|iniciar|solucionarlo|arreglarlo)\b",
    r"\b(persiste|continua|contin[uú]a)\b",
    r"\btampoco\s+(funcion[oó]|sirvi[oó]|sirve)\b",
    r"^(no|nada|tampoco|sigue ca[ií]do)$"
]

# Intenciones explícitas e inequívocas de creación de caso / ticket o solicitud presencial
EXPLICIT_TICKET_INTENTS = [
    r"^(crear|abrir|generar|radicar|vamos\s+a\s+radicar|solicito\s+radicar)\s+(un\s+|el\s+)?(ticket|caso|reporte|incidente)$",
    r"^(solicito|necesito)\s+(un\s+)?(soporte\s+presencial|t[eé]cnico\s+en\s+sitio)$",
    r"^create_ticket$"
]

# Trámites administrativos, cambios de permisos o compras (sin diagnóstico simulado)
ADMIN_PERMISSIONS_PATTERNS = [
    r"\b(cambio\s+de\s+permisos|autorizar\s+permisos|asignar\s+permisos|compra\s+de|adquisici[oó]n|inventario|revisi[oó]n\s+f[ií]sica|dar\s+de\s+baja|mantenimiento\s+preventivo\s+f[ií]sico)\b"
]

# Palabras de control/afirmación que NUNCA deben aceptarse como partes de un nombre
NON_NAME_WORDS = {

    "si", "sí", "claro", "ok", "ayudame", "ayúdame", "dale", "bueno", "por", "favor",
    "porfa", "procede", "radica", "radicar", "radícalo", "radícala", "radicarlo", "radicarla",
    "ticket", "tickets", "caso", "casos", "hola", "buenas", "buenos", "dias", "días",
    "tardes", "noches", "soporte", "falla", "problema", "hazlo", "gracias", "grasias",
    "necesito", "ayuda", "tecnico", "técnico", "un", "una", "el", "la", "los", "las",
    "crear", "abrir", "generar", "solicitar", "mi", "correo", "es", "para", "que", "y",
    "cancelar", "cancela", "olvidalo", "olvídalo", "dejalo", "déjalo", "no"
}

# Palabras clave para identificar trámites de SOFTWARE / Cuentas / Accesos
SOFTWARE_KEYWORDS = [
    r"\b(kactus|katuc|kaktu|caktus|katu)\b", r"\b(seven|seben)\b", r"\bpermiso[s]?\b", r"\bpermizo[s]?\b",
    r"\bacceso[s]?\b", r"\baccezo[s]?\b", r"\bcuenta[s]?\b", r"\bcuanta[s]?\b",
    r"\bcontrase[ñn]a[s]?\b", r"\bcontrace[ñn]a[s]?\b", r"\bclave[s]?\b", r"\bclabe[s]?\b",
    r"\bcorreo[s]?\b", r"\bcoreo[s]?\b", r"\bemail\b", r"\bteams\b", r"\btims\b",
    r"\bplataforma[s]?\b", r"\bportal\b", r"\baula\b", r"\b(moodle|modle|mudle)\b",
    r"\b(office|ofis|ofice)\b", r"\blicencia[s]?\b", r"\bbloqueo\b", r"\bbloqeo\b",
    r"\bdesbloquear\b", r"\bdesbloqear\b", r"\busuario[s]?\b", r"\bperfil\b",
    r"\bcredenciales\b", r"\bsoftware\b", r"\baplicativo[s]?\b", r"\bsistema[s]?\b",
    r"\berp\b", r"\bn[oó]mina\b", r"\bautenticaci[oó]n\b", r"\brestablecer\b",
    r"\brestableser\b", r"\bolvid[eé]\b", r"\blogin\b", r"\bsesi[oó]n\b", r"\bceci[oó]n\b"
]

# Regex estándar para extracción y validación de correo con soporte para caracteres latinos y Unicode
EMAIL_REGEX = re.compile(r"[\w\.\+-]+@[\w\.-]+\.\w+", re.UNICODE)


def extract_email_address(text: str) -> str:
    """Soporte para normalización de caracteres latinos antes de validar estructura de correo."""
    clean_text = text.strip()
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', clean_text, re.UNICODE)
    if match:
        return match.group(0).lower()
    return clean_text.lower()


# Disparadores de urgencia crítica
CRITICAL_TRIGGERS = [
    r"urgente", r"emergencia", r"auditorio", r"laboratorio completo", r"toda la sede",
    r"servidor principal", r"caída general", r"nómina", r"bloqueo total"
]

MEDIUM_TRIGGERS = [
    r"clase", r"docente", r"profesor", r"departamento", r"oficina", r"no puedo trabajar",
    r"requiero hoy", r"lento"
]

DESPEDIDA_INSTITUCIONAL = (
    "¡Excelente! Me alegra saber que pudiste resolver el inconveniente. "
    "Quedo a tu disposición si requieres apoyo con algún otro procedimiento o servicio institucional de TI en la Universidad Simón Bolívar. ¡Que tengas un excelente día! 🎓"
)


class RouterLogic:
    """
    Motor de análisis conversacional de Nivel 1 y orquestación de tickets para UniMon.
    """

    @classmethod
    def get_session(cls, session_id: str) -> TicketSession:
        """Obtiene o crea una nueva sesión conversacional."""
        if session_id not in ticket_sessions:
            ticket_sessions[session_id] = TicketSession(session_id=session_id)
        return ticket_sessions[session_id]

    @classmethod
    def reset_session(cls, session_id: str, keep_history: bool = False, preserve_role: bool = True) -> None:
        """Limpia y resetea la sesión del usuario a IDLE, preservando el rol si ya fue asignado."""
        saved_role = None
        if session_id in ticket_sessions and preserve_role:
            saved_role = ticket_sessions[session_id].user_role
        ticket_sessions[session_id] = TicketSession(session_id=session_id, user_role=saved_role)
        if not keep_history and session_id in session_history:
            session_history[session_id] = []

    @classmethod
    def get_history(cls, session_id: str) -> List[Dict[str, str]]:
        """Obtiene el historial de conversación de la sesión."""
        if session_id not in session_history:
            session_history[session_id] = []
        return session_history[session_id]

    @classmethod
    def add_history(cls, session_id: str, role: str, content: str) -> None:
        """Agrega un mensaje al historial de la sesión (máximo 10 mensajes en buffer)."""
        if session_id not in session_history:
            session_history[session_id] = []
        session_history[session_id].append({"role": role, "content": content})
        if len(session_history[session_id]) > 10:
            session_history[session_id] = session_history[session_id][-10:]

    @classmethod
    def clear_history(cls, session_id: str) -> None:
        """Limpia el historial de conversación de la sesión."""
        if session_id in session_history:
            session_history[session_id] = []

    @classmethod
    def clean_inactive_sessions(cls, ttl_minutes: int = 20) -> int:
        """Reinicia a IDLE o purga las sesiones inactivas que superen el TTL."""
        now = datetime.now(timezone.utc)
        cleaned_count = 0
        for session_id, session in list(ticket_sessions.items()):
            inactive_seconds = (now - session.last_interaction).total_seconds()
            if inactive_seconds > (ttl_minutes * 60):
                if session.estado != EstadoTicket.IDLE or session.pending_query is not None:
                    session.estado = EstadoTicket.IDLE
                    session.pending_query = None
                    session.intentos_fallidos = 0
                    session.falla = None
                    session.descripcion = None
                    session.nombre = None
                    session.correo = None
                    cleaned_count += 1
                    logger.info(f"Sesión {session_id} expirada por TTL ({ttl_minutes} min). Reiniciada a IDLE.")
        return cleaned_count

    @classmethod
    def detect_user_role(cls, text: str) -> Optional[str]:
        """
        Detecta si el usuario menciona o selecciona su rol en la comunidad universitaria.
        Maneja desambiguación contextual (ej. 'mis alumnos', 'subo notas' -> profesor).
        Retorna 'estudiante', 'profesor', 'administrativo' u 'otros'.
        """
        msg_lower = text.lower().strip()

        # 1. Patrones contextuales prioritarios de profesor / docente
        if any(re.search(pat, msg_lower) for pat in [
            r"\bmis\s+(alumnos|alumnas|estudiantes)\b",
            r"\b(de|a)\s+mis\s+(alumnos|alumnas|estudiantes)\b",
            r"\b(subir|subo|cargar|cargo|ingresar|ingreso|digitar|digito)\s+(las\s+)?(notas|calificaciones|fallas|inasistencias)\b",
            r"\b(reportar|reporte\s+de)\s+(fallas|inasistencias)\b",
            r"\bcalificar\s+(alumnos|estudiantes|grupo|curso|planillas)\b",
            r"\b(soy|como)\s+(profesor|profesora|docente|catedr[aá]tico|catedr[aá]tica)\b"
        ]):
            return "profesor"

        # 2. Búsqueda directa por sinónimos estándar
        for key, role_val in ROLE_SYNONYMS.items():
            if re.search(rf"\b{key}\b", msg_lower):
                return role_val
        return None

    @classmethod
    def is_greeting(cls, text: str) -> bool:
        """Detecta si el mensaje es únicamente un saludo de cortesía."""
        msg_clean = re.sub(r"[^\w\s\?¿]", "", text.strip().lower())
        words = msg_clean.split()
        if len(words) <= 5:
            return any(re.search(pat, msg_clean) for pat in GREETING_PATTERNS)
        return False

    @classmethod
    async def classify_intent(cls, text: str, role: str = "general") -> str:
        """
        Clasifica semánticamente la intención con LLM ('AUTOSERVICIO' vs 'SOPORTE_FISICO').
        """
        return await classify_request_intent_async(text, role)

    @classmethod
    def is_physical_hardware_request(cls, text: str, role: str = "general") -> bool:
        """
        Determina semánticamente si el mensaje corresponde a una falla física, daño de hardware,
        cableado, punto de red, revisión en sitio o mantenimiento de equipos.
        """
        if is_informative_procedure_query(text):
            return False
        return is_physical_hardware_request(text, role)

    @classmethod
    def is_cancellation(cls, text: str) -> bool:
        """
        Detecta si el usuario solicita cancelar el proceso de radicación o rechaza la oferta
        ('cancelar', 'cancela', 'ya no', 'no gracias', 'olvidalo', 'dejalo asi', 'no quiero', 'no', 'nop').
        """
        msg_clean = re.sub(r"[^\w\s]", " ", text.strip().lower())
        msg_clean = re.sub(r"\s+", " ", msg_clean).strip()
        words = msg_clean.split()
        if msg_clean in CANCEL_PATTERNS or (len(words) == 1 and words[0] in ["no", "nop", "noup", "none"]):
            return True
        return any(re.search(pat, msg_clean) for pat in CANCEL_REGEX)

    @classmethod
    def is_equipment_request(cls, text: str) -> bool:
        """
        Detecta si el mensaje corresponde estrictamente a una solicitud o reserva de préstamo físico
        de equipos (micrófonos, tablets, portátiles, proyectores, salas, etc.).

        Reglas estrictas de discriminación:
        1. Si contiene cualquier término de falla técnica, daño o soporte ('problema', 'dañado', 'falla', 'lento', etc.),
           retorna FALSE para dar paso al diagnóstico técnico de Nivel 1 / RAG.
        2. Requiere la presencia obligatoria de un verbo de préstamo/reserva COMBINADO con un sustantivo de equipo físico.
        """
        msg_clean = text.strip().lower()

        # Regla 1: Si describe falla técnica, daño, error o petición de soporte, NUNCA es préstamo
        if any(term in msg_clean for term in FAILURE_AND_SUPPORT_TERMS):
            return False

        # Regla 2: Intención explícita de préstamo/reserva + equipo físico
        has_loan_verb = any(re.search(pat, msg_clean) for pat in LOAN_REQUEST_VERBS)
        has_equipment_noun = any(re.search(pat, msg_clean) for pat in EQUIPMENT_NOUNS)

        if has_loan_verb and has_equipment_noun:
            return True

        return False

    @classmethod
    def is_physical_or_admin_request(cls, text: str) -> bool:
        """
        Detecta si la consulta involucra trámites administrativos, cambios de permisos, compras o inventario.
        """
        msg_clean = text.strip().lower()
        return any(re.search(pat, msg_clean) for pat in ADMIN_PERMISSIONS_PATTERNS)

    @classmethod
    def is_solved_confirmation(cls, text: str) -> bool:
        """
        Detecta si el usuario indica que la sugerencia resolvió el problema o da cierre al caso
        ("ya pude", "ya funcionó", "muchas gracias ya quedó", "listo gracias", etc.).
        NUNCA debe dispararse si el mensaje contiene preguntas, dudas o describe problemas ('pero', 'donde', 'cómo', '?').
        """
        if not text:
            return False

        # Si el texto contiene signos de interrogación o palabras interrogativas/contraste, es una consulta
        if any(q in text for q in ["?", "¿"]):
            return False

        text_lower = text.strip().lower()
        if any(w in text_lower for w in ["pero", "dónde", "donde", "cómo", "como", "cuándo", "cuando", "cuál", "cual", "actualizo", "actualizar", "cambio", "cambiar", "por qué", "porque"]):
            return False

        msg_clean = re.sub(r"[^\w\s]", " ", text_lower)
        msg_clean = re.sub(r"\s+", " ", msg_clean).strip()
        words = msg_clean.split()

        # Comprobar si hay patrones explícitos de falla (ej: "no funcionó", "sigue igual", "no pude entrar")
        for pat in EXPLICIT_FAIL_PATTERNS:
            if re.search(pat, msg_clean):
                return False

        # Si el mensaje es largo (> 7 palabras) y no es una confirmación inequívoca, no es cierre
        if len(words) > 7 and not any(re.search(pos, msg_clean) for pos in [
            r"\bya\s+funcion[oó]\b", r"\bya\s+pude\b", r"\bya\s+sirvi[oó]\b", r"\bse\s+solucion[oó]\b", r"\bse\s+arregl[oó]\b"
        ]):
            return False

        return any(re.search(pat, msg_clean) for pat in SOLVED_PATTERNS)

    @classmethod
    def is_explicit_ticket_request(cls, text: str) -> bool:
        """
        Detecta si el usuario formula una frase compuesta e inequívoca de solicitud de ticket o técnico en sitio.
        No coincide con palabras sueltas como 'falla', 'problema', 'daño', 'ayuda' o 'soporte'.
        """
        msg_clean = text.strip().lower()
        msg_clean = re.sub(r"[^\w\s]", " ", msg_clean)
        msg_clean = re.sub(r"\s+", " ", msg_clean).strip()
        return any(re.match(pat, msg_clean) for pat in EXPLICIT_TICKET_INTENTS)

    @classmethod
    def is_direct_tech_request(cls, text: str) -> bool:
        """Detecta si el usuario formula una frase inequívoca de solicitud de técnico o radicación directa."""
        return cls.is_explicit_ticket_request(text)

    @classmethod
    def is_report_request(cls, text: str) -> bool:
        """Alias para compatibilidad: evalúa intención explícita de ticket."""
        return cls.is_explicit_ticket_request(text)

    @classmethod
    def is_persisting_or_ticket_request(cls, text: str) -> bool:
        """Detecta si el usuario indica que la falla continúa tras el diagnóstico."""
        if cls.is_solved_confirmation(text) or cls.is_cancellation(text):
            return False
        msg_clean = re.sub(r"[^\w\s]", " ", text.strip().lower())
        msg_clean = re.sub(r"\s+", " ", msg_clean).strip()
        return any(re.search(pat, msg_clean) for pat in EXPLICIT_FAIL_PATTERNS) or cls.is_explicit_ticket_request(text)

    @classmethod
    def is_affirmative(cls, text: str) -> bool:
        """Detecta si el usuario confirma expresamente la acción ofrecida."""
        msg_clean = re.sub(r"[^\w\s\?¿áéíóúÁÉÍÓÚñÑ]", " ", text.strip().lower())
        msg_clean = re.sub(r"\s+", " ", msg_clean).strip()
        return msg_clean in ["si", "sí", "claro", "por favor", "de acuerdo", "procede", "adelante", "dale"]


    @classmethod
    def detect_category(cls, text: str) -> Tuple[CategoriaSolicitud, str]:
        """
        Detecta si la solicitud pertenece a SOFTWARE (cuentas, permisos, apps) o a HARDWARE (equipos físicos).
        Retorna (CategoriaSolicitud, nombre_categoria_legible).
        """
        text_lower = text.lower()
        if any(re.search(pat, text_lower) for pat in SOFTWARE_KEYWORDS):
            return CategoriaSolicitud.SOFTWARE, "Sistemas de Información, Cuentas y Software (P-GT-11 / P-GT-13)"
        return CategoriaSolicitud.HARDWARE, "Mantenimiento y Fallas de Cómputo (P-GT-01)"

    @classmethod
    def extract_email(cls, text: str) -> Optional[str]:
        """Extrae el primer correo válido del texto soportando caracteres especiales y latinos."""
        clean_text = text.strip()
        match = EMAIL_REGEX.search(clean_text)
        if match:
            return match.group(0).strip().lower()
        return None

    @classmethod
    def extract_name(cls, text: str, email: Optional[str] = None) -> Optional[str]:
        """
        Extrae y valida estrictamente el nombre completo del solicitante.
        Requiere al menos 2 palabras válidas y descarta palabras afirmativas, de control o de cancelación.
        """
        cleaned = text
        if email:
            cleaned = cleaned.replace(email, "")

        cleaned_no_punct = re.sub(r"[^\w\sÁÉÍÓÚáéíóúñÑ]", " ", cleaned).strip()

        # Si todo el mensaje es una frase afirmativa o de cancelación
        if cls.is_affirmative(cleaned_no_punct) or cls.is_cancellation(cleaned_no_punct):
            return None

        # Patrones con prefijo "Mi nombre es...", "Me llamo...", "Soy..."
        name_prefix_patterns = [
            r"(?:mi nombre es|me llamo|soy|nombre:)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]{2,}(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ]{2,})+)"
        ]

        for pat in name_prefix_patterns:
            m = re.search(pat, cleaned, re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                cand_words = [w.lower() for w in cand.split() if w.isalpha()]
                if len(cand_words) >= 2 and not any(w in NON_NAME_WORDS for w in cand_words):
                    return " ".join([w.capitalize() for w in cand.split()])

        # Evaluación directa de tokens
        words = [w for w in cleaned_no_punct.split() if w.isalpha()]

        # Debe tener al menos 2 palabras (Nombre y Apellido) y máximo 6
        if len(words) < 2 or len(words) > 6:
            return None

        words_lower = [w.lower() for w in words]

        # Ninguna palabra puede ser una palabra de control/afirmación/cancelación
        if any(w in NON_NAME_WORDS for w in words_lower):
            return None

        # Cada palabra debe tener al menos 2 caracteres
        if any(len(w) < 2 for w in words):
            return None

        return " ".join(words).title()

    @classmethod
    def calculate_urgency_and_impact(cls, message: str) -> Tuple[int, int]:
        """Calcula la urgencia e impacto institucional."""
        msg_lower = message.lower()
        urgency, impact = 3, 3

        if any(re.search(pat, msg_lower) for pat in CRITICAL_TRIGGERS):
            urgency, impact = 5, 4
        elif any(re.search(pat, msg_lower) for pat in MEDIUM_TRIGGERS):
            urgency, impact = 4, 3

        return urgency, impact

    @classmethod
    def build_support_channel_message(cls, falla: Optional[str] = None) -> str:
        """
        Construye la plantilla estructurada tipo formulario guiado para el correo de soporte
        y la pregunta de radicación directa.
        """
        asunto_sugerido = (falla[:50].strip() if falla and len(falla.strip()) > 5 else "Reporte de falla técnica o requerimiento")

        return (
            "Si el inconveniente persiste o requiere un trámite administrativo/físico, puedes comunicarte directamente con los canales oficiales de soporte técnico de la Universidad Simón Bolívar:\n\n"
            "📧 **Canales Oficiales de Atención TI:**\n"
            "- **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | Tel: (605) 3444333 Ext. 8003/8004\n"
            "- **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | Tel: (607) 5827070 Ext. 129\n\n"
            "📋 **Plantilla guiada para redactar tu correo:**\n"
            f"- **Asunto:** [Soporte TI] {asunto_sugerido}\n"
            "- **Cuerpo del mensaje:**\n"
            "  • **Nombre del Solicitante:** [Tu nombre completo]\n"
            "  • **Ubicación:** [Sede, Bloque, Piso, Oficina o Laboratorio]\n"
            "  • **Equipo / Servicio Afectado:** [Computador, Red, Plataforma, etc.]\n"
            "  • **Descripción Detallada:** [Indica paso a paso qué ocurre, mensajes de error y qué pruebas realizaste]\n\n"
            "¿O prefieres que radique el caso directamente por ti ahora mismo?"
        )

    @classmethod
    async def _radicar_ticket_en_glpi(cls, session_id: str, session: TicketSession) -> Dict[str, Any]:
        """
        Genera el ticket en GLPI aplicando las reglas de negocio (máximo 2 por día, opción de seguimiento)
        y registra telemetría en SQLite (analytics.db).
        """
        falla_desc = session.descripcion or session.falla or "Requerimiento de soporte reportado por el usuario"
        nombre_sol = session.nombre or "Usuario Unisimon"
        correo_sol = session.correo or "solicitudcomputo@unisimon.edu.co"
        category_name = session.category_name or "Soporte Técnico y Gestión de TI Unisimon"

        # -------------------------------------------------------------
        # REGLAS DE NEGOCIO GLPI (Máximo 2 al día)
        # -------------------------------------------------------------
        tickets_today = await glpi_client.get_tickets_today_for_email(correo_sol)

        # REGLA A: Si ya tiene >= 2 tickets radicados hoy -> Bloquear creación
        if len(tickets_today) >= 2 and not session.decision_mismo_o_nuevo:
            cls.reset_session(session_id)
            block_msg = (
                f"Has alcanzado el límite máximo de 2 solicitudes radicadas por día en GLPI para el correo **{correo_sol}**. "
                f"Para casos urgentes adicionales, comunícate directamente con la Mesa de Ayuda (Barranquilla: Ext. 8003/8004 | Cúcuta: Ext. 129)."
            )
            return {
                "tipo": "ERROR",
                "state": "FINALIZADO",
                "mensaje": block_msg,
                "response": block_msg,
                "ticket_id": None,
                "source": "GLPI_Limit_Exceeded",
                "quick_replies": []
            }

        # REGLA B: Si tiene exactamente 1 ticket radicado hoy -> Preguntar si es seguimiento o nuevo reporte
        if len(tickets_today) == 1 and not session.decision_mismo_o_nuevo:
            existing_id = tickets_today[0]["ticket_id"]
            session.existing_ticket_id_today = existing_id
            session.estado = EstadoTicket.CONFIRMANDO_SEGUIMIENTO
            ask_msg = (
                f"Detectamos que ya tienes el Ticket **#{existing_id}** abierto hoy en GLPI. "
                f"¿Deseas agregar esta información como seguimiento a ese mismo caso o necesitas radicar un reporte independiente?"
            )
            return {
                "tipo": "RADICANDO_TICKET",
                "state": "CONFIRMANDO_SEGUIMIENTO",
                "mensaje": ask_msg,
                "response": ask_msg,
                "ticket_id": None,
                "source": "GLPI_Followup_Disambiguation",
                "quick_replies": [
                    {"label": "📌 Mismo caso (Seguimiento)", "payload": "FOLLOWUP_SAME_TICKET"},
                    {"label": "🆕 Nuevo reporte", "payload": "CREATE_NEW_TICKET"}
                ]
            }

        # REGLA C: 0 tickets hoy (o usuario eligió 'Nuevo reporte') -> Crear nuevo ticket
        asunto_ticket = f"[Soporte TI Unisimon] {falla_desc[:50]}"
        contenido_ticket = (
            f"<b>REPORTE DE INCIDENTE / REQUERIMIENTO TÉCNICO - MESA DE AYUDA UNISIMON</b><br><br>"
            f"<b>Solicitante:</b> {nombre_sol}<br>"
            f"<b>Correo Electrónico:</b> {correo_sol}<br>"
            f"<b>Categoría:</b> {category_name}<br>"
            f"<b>Nivel de Urgencia:</b> {session.urgency}/5<br><br>"
            f"<b>Detalle del Requerimiento / Problema:</b><br>{falla_desc}<br><br>"
            f"<i>Caso escalado y radicado tras descarte de Nivel 1 en UniMon Chatbot.</i>"
        )

        try:
            ticket_res = await glpi_client.crear_ticket(
                name=asunto_ticket,
                content=contenido_ticket,
                urgency=session.urgency,
                impact=session.impact,
                requester_email=correo_sol
            )

            ticket_id = ticket_res.get("ticket_id")

            # Registrar actividad en SQLite
            from app.services.telemetry_service import log_ticket_activity
            log_ticket_activity(session_id=session_id, email=correo_sol, ticket_id=ticket_id, action="NUEVO")

            cls.reset_session(session_id)

            confirmacion_msg = (
                f"✅ Se ha radicado exitosamente tu solicitud de soporte técnico con el radicado **#{ticket_id}**.\n\n"
                f"📋 **Resumen del Caso:**\n"
                f"- **Solicitante:** {nombre_sol}\n"
                f"- **Correo:** {correo_sol}\n"
                f"- **Descripción:** {falla_desc}\n\n"
                f"Un técnico de la Dirección de TI revisará tu caso y se pondrá en contacto a través de tu correo institucional (**{correo_sol}**)."
            )

            return {
                "tipo": "TICKET_CREADO",
                "mensaje": confirmacion_msg,
                "ticket_id": ticket_id,
                "ticket_details": {
                    "ticket_id": ticket_id,
                    "category": category_name,
                    "urgency": session.urgency,
                    "impact": session.impact,
                    "status": "success"
                },
                "category": category_name,
                "source": "GLPI_REST_API"
            }

        except Exception as exc:
            logger.error(f"Error al crear ticket en GLPI: {exc}")
            cls.reset_session(session_id)
            return {
                "tipo": "ERROR",
                "mensaje": f"Ocurrió un inconveniente al procesar la solicitud ({exc}). Por favor contacta a solicitudcomputo@unisimon.edu.co o helpdesk@unisimon.edu.co.",
                "ticket_id": None,
                "source": "GLPI_ERROR"
            }

    @classmethod
    async def procesar_mensaje(cls, mensaje: str, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Procesa el mensaje del usuario de acuerdo a la máquina de estados conversacional de Nivel 1.
        Aplica:
        1. Detección y propagación del rol del usuario (Estudiante / Docente / Funcionario).
        2. Flujo de Cancelación Universal y Rechazo ("no", "cancelar") en cualquier estado de radicación.
        3. Discriminación estricta de solicitudes de préstamos/asignación de equipos físicos vs. fallas técnicas.
        4. Cero alucinaciones con transición forzada a OFRECIENDO_RADICACION cuando no hay documentación relevante.
        5. Detección de cierre ("no ya", "ya no necesito", "ya pude", "ya funcionó", "listo").
        6. Diagnóstico multi-turno (hasta max_intentos_diagnostico = 3 intentos) con RAG filtrado por rol.
        7. Secuencia estricta de 3 pasos para Slot-Filling:
           Paso 1: Nombre Completo (Validación estricta, soporte cancelación)
           Paso 2: Correo Electrónico (Validación, soporte cancelación)
           Paso 3: Descripción Detallada del Requerimiento/Problema (Soporte cancelación)
           Paso 4: Radicación en GLPI (Ticket Creado)
        """
        texto = mensaje.strip()
        session = cls.get_session(session_id)
        now = datetime.now(timezone.utc)

        # -------------------------------------------------------------
        # CONTROL TEMPORAL (TTL): Expiración de sesión por inactividad (>20 min)
        # -------------------------------------------------------------
        inactive_seconds = (now - session.last_interaction).total_seconds()
        if inactive_seconds > (20 * 60):
            if session.estado != EstadoTicket.IDLE or session.pending_query is not None:
                logger.info(f"[Session: {session_id}] Sesión expirada por inactividad ({inactive_seconds:.0f}s > 1200s). Reiniciando a IDLE.")
                session.estado = EstadoTicket.IDLE
                session.pending_query = None
                session.intentos_fallidos = 0
                session.falla = None
                session.descripcion = None
                session.nombre = None
                session.correo = None

        session.last_interaction = now
        estado_actual = session.estado

        # -------------------------------------------------------------
        # DETECCIÓN DE ROL DEL USUARIO
        # El rol se asigna únicamente cuando el usuario responde a PIDIENDO_ROL
        # o cuando en IDLE su mensaje es exclusivamente una declaración de rol.
        # -------------------------------------------------------------
        if session.user_role is None and estado_actual == EstadoTicket.PIDIENDO_ROL:
            detected_role = cls.detect_user_role(texto) or normalize_role(texto)
            if detected_role:
                session.user_role = detected_role
                logger.info(f"[Session: {session_id}] Rol confirmado en PIDIENDO_ROL: '{session.user_role}'")

        logger.info(f"[Session: {session_id}] Estado: {estado_actual} | Rol: {session.user_role} | Intentos: {session.intentos_diagnostico}/{session.max_intentos_diagnostico} | Mensaje ({len(texto)} chars): '{texto}'")

        # -------------------------------------------------------------
        # REGLA GLOBAL 1: Flujo de Cancelación Universal y Rechazo ("no", "cancelar")
        # Si el usuario rechaza la oferta o desea cancelar en cualquier estado de radicación
        # -------------------------------------------------------------
        if estado_actual in [
            EstadoTicket.OFRECIENDO_RADICACION,
            EstadoTicket.PIDIENDO_NOMBRE,
            EstadoTicket.PIDIENDO_CORREO,
            EstadoTicket.PIDIENDO_DESCRIPCION
        ] and cls.is_cancellation(texto):
            cls.reset_session(session_id)
            cls.add_history(session_id, "user", texto)
            cls.add_history(session_id, "assistant", MENSAJE_CANCELACION)
            return {
                "tipo": "CANCELADO",
                "mensaje": MENSAJE_CANCELACION,
                "ticket_id": None,
                "source": "UniMon_Cancelacion"
            }

        # -------------------------------------------------------------
        # REGLA GLOBAL 2: Detección de Cierre / Solucionado en IDLE/DIAGNOSTICO
        # Responder de inmediato con despedida institucional y NUNCA activar radicación.
        # Golden Cache: guardar el caso resuelto para reutilización futura.
        # -------------------------------------------------------------
        if cls.is_solved_confirmation(texto):
            # Guardar en Golden Cache si hay consulta y respuesta previas
            if session.last_user_query and session.last_bot_response:
                try:
                    save_golden_case(
                        session_id=session_id,
                        user_query=session.last_user_query,
                        bot_response=session.last_bot_response,
                        role=session.user_role or "general"
                    )
                except Exception as e:
                    logger.warning(f"[GoldenCache] Error al guardar caso en cierre global: {e}")
            cls.reset_session(session_id)
            cls.add_history(session_id, "user", texto)
            cls.add_history(session_id, "assistant", DESPEDIDA_INSTITUCIONAL)
            return {
                "tipo": "SOLUCIONADO",
                "mensaje": DESPEDIDA_INSTITUCIONAL,
                "ticket_id": None,
                "source": "UniMon_Nivel1_Resolved"
            }

        # -------------------------------------------------------------
        # REGLA GLOBAL 3: Respuesta Determinista Instantánea para Directorio y Canales de Atención TI
        # -------------------------------------------------------------
        if estado_actual in [EstadoTicket.IDLE, EstadoTicket.DIAGNOSTICO]:
            texto_lower = texto.lower().strip()
            is_direct_contact_query = bool(re.search(
                r"\b(canales\s+de\s+atenci[oó]n|canales\s+de\s+atencion|canales\s+de\s+soporte|canales|cual\s+es\s+el\s+wasap|cuál\s+es\s+el\s+wasap|cual\s+es\s+el\s+whatsapp|cuál\s+es\s+el\s+whatsapp|wasap\s+soporte|whatsapp\s+soporte|directorio\s+ti|tel[eé]fonos?\s+soporte|correo\s+soporte|escribir\s+a\s+los\s+canales)\b",
                texto_lower
            )) and not any(w in texto_lower for w in ["no me sirve", "no funciona", "error", "falla", "dañado", "ticket", "radicar"])
            
            if is_direct_contact_query:
                msg_directorio = (
                    "Los canales oficiales de atención y soporte técnico TI de la **Universidad Simón Bolívar (Colombia)** son:\n\n"
                    "• **Sede Barranquilla:**\n"
                    "  - Correo: `solicitudcomputo@unisimon.edu.co`\n"
                    "  - WhatsApp: `3172683922`\n"
                    "  - Teléfono: `(605) 3444333` Ext. `8003` y `8004`\n\n"
                    "• **Sede Cúcuta:**\n"
                    "  - Correo: `helpdesk@unisimon.edu.co`\n"
                    "  - Teléfono: `(607) 5827070` Ext. `129`\n\n"
                    "¿Pudiste resolver tu problema con estos pasos?\n"
                    "- Selecciona o escribe **Sí** si te funcionó.\n"
                    "- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte."
                )
                session.estado = EstadoTicket.DIAGNOSTICO
                session.last_user_query = texto
                session.last_bot_response = msg_directorio
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", msg_directorio)
                return {
                    "tipo": "DIAGNOSTICO",
                    "mensaje": msg_directorio,
                    "response": msg_directorio,
                    "sources": ["Directorio_Institucional_TI"],
                    "source": "UniMon_Directorio_Direct",
                    "quick_replies": [
                        {"label": "✅ Sí, me funcionó", "payload": "RESOLVED"},
                        {"label": "🎫 Generar reporte", "payload": "CREATE_TICKET"}
                    ]
                }

        # -------------------------------------------------------------
        # REGLA GLOBAL 4: Guardrail Estricto Fuera de Dominio (Out-of-Domain)
        # Intercepta antes de cualquier llamada a RAG temas no institucionales
        # (programación general, investigaciones, ensayos, cultura general, recetas, etc.)
        # -------------------------------------------------------------
        if estado_actual in [EstadoTicket.IDLE, EstadoTicket.DIAGNOSTICO, EstadoTicket.PIDIENDO_ROL]:
            if is_out_of_domain_query(texto):
                cls.reset_session(session_id)
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", MENSAJE_FUERA_DE_DOMINIO)
                return {
                    "tipo": "FUERA_DE_DOMINIO",
                    "state": "FUERA_DE_DOMINIO",
                    "mensaje": MENSAJE_FUERA_DE_DOMINIO,
                    "response": MENSAJE_FUERA_DE_DOMINIO,
                    "ticket_id": None,
                    "source": "UniMon_Guardrail",
                    "quick_replies": []
                }

        # -------------------------------------------------------------
        # ESTADO: PIDIENDO_DESCRIPCION (Paso 3 de Slot-Filling)
        # Recibe la descripción detallada del requerimiento o problema y guarda el texto exacto
        # -------------------------------------------------------------
        if estado_actual == EstadoTicket.PIDIENDO_DESCRIPCION:
            session.descripcion = texto
            session.falla = texto
            return await cls._radicar_ticket_en_glpi(session_id, session)

        # -------------------------------------------------------------
        # ESTADO: CONFIRMANDO_SEGUIMIENTO (Desambiguación de Regla B)
        # -------------------------------------------------------------
        elif estado_actual == EstadoTicket.CONFIRMANDO_SEGUIMIENTO:
            texto_upper = texto.upper()
            is_followup = (
                "FOLLOWUP" in texto_upper or "MISMO" in texto_upper or "SEGUIMIENTO" in texto_upper or
                "mismo caso" in texto.lower() or "seguimiento" in texto.lower()
            )
            is_new = (
                "NEW" in texto_upper or "NUEVO" in texto_upper or "INDEPENDIENTE" in texto_upper or
                "nuevo reporte" in texto.lower() or "otro ticket" in texto.lower()
            )

            if is_followup:
                existing_id = session.existing_ticket_id_today or 1000
                falla_desc = session.descripcion or session.falla or "Seguimiento de usuario"
                correo_sol = session.correo or "solicitudcomputo@unisimon.edu.co"
                from app.services.telemetry_service import log_ticket_activity
                await glpi_client.add_ticket_followup(ticket_id=existing_id, content=falla_desc, email=correo_sol)
                log_ticket_activity(session_id=session_id, email=correo_sol, ticket_id=existing_id, action="FOLLOWUP")
                cls.reset_session(session_id)
                confirm_followup = (
                    f"✅ Se ha registrado exitosamente el seguimiento en tu Ticket **#{existing_id}** en GLPI.\n\n"
                    f"El equipo de Mesa de Ayuda TI revisará la nueva información agregada a tu caso."
                )
                return {
                    "tipo": "TICKET_CREADO",
                    "state": "FINALIZADO",
                    "mensaje": confirm_followup,
                    "response": confirm_followup,
                    "ticket_id": existing_id,
                    "source": "GLPI_Followup_Success",
                    "quick_replies": []
                }
            elif is_new:
                session.decision_mismo_o_nuevo = True
                return await cls._radicar_ticket_en_glpi(session_id, session)
            else:
                ask_msg = (
                    f"Por favor selecciona si deseas agregar esta información como seguimiento al Ticket **#{session.existing_ticket_id_today}** o crear un nuevo reporte:"
                )
                return {
                    "tipo": "RADICANDO_TICKET",
                    "state": "CONFIRMANDO_SEGUIMIENTO",
                    "mensaje": ask_msg,
                    "response": ask_msg,
                    "ticket_id": None,
                    "source": "GLPI_Followup_Disambiguation",
                    "quick_replies": [
                        {"label": "📌 Mismo caso (Seguimiento)", "payload": "FOLLOWUP_SAME_TICKET"},
                        {"label": "🆕 Nuevo reporte", "payload": "CREATE_NEW_TICKET"}
                    ]
                }

        # -------------------------------------------------------------
        # ESTADO: PIDIENDO_CORREO (Paso 2 de Slot-Filling)
        # Valida el correo y transiciona SIEMPRE a PIDIENDO_DESCRIPCION
        # -------------------------------------------------------------
        elif estado_actual == EstadoTicket.PIDIENDO_CORREO:
            ext_email = cls.extract_email(texto)
            if ext_email and is_valid_email(ext_email):
                session.correo = ext_email
                session.estado = EstadoTicket.PIDIENDO_DESCRIPCION
                prompt_desc = "Por favor describe detalladamente la situación o requerimiento que presentas:"
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", prompt_desc)
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": prompt_desc,
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
                }
            else:
                prompt_err = "El correo ingresado no parece ser válido. Por favor ingresa un correo electrónico institucional o de contacto válido (ej: usuario@unisimon.edu.co):"
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": prompt_err,
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
                }

        # -------------------------------------------------------------
        # ESTADO: PIDIENDO_NOMBRE (Paso 1 de Slot-Filling)
        # Validación estricta: mínimo 2 palabras, sin afirmaciones ni stopwords
        # -------------------------------------------------------------
        elif estado_actual == EstadoTicket.PIDIENDO_NOMBRE:
            ext_email = cls.extract_email(texto)
            ext_name = cls.extract_name(texto, ext_email)

            if not ext_name:
                prompt_invalido = "Por favor indícame tu **nombre y apellido completos** (ej: Juan Pérez):"
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": prompt_invalido,
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
                }

            session.nombre = ext_name

            if ext_email and is_valid_email(ext_email):
                session.correo = ext_email
                session.estado = EstadoTicket.PIDIENDO_DESCRIPCION
                prompt_desc = f"Gracias, **{session.nombre}**. Por favor describe detalladamente la situación o requerimiento que presentas:"
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", prompt_desc)
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": prompt_desc,
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
                }
            else:
                session.estado = EstadoTicket.PIDIENDO_CORREO
                prompt_correo = f"Gracias, **{session.nombre}**. Ahora por favor indícame tu **correo electrónico institucional o de contacto** (ej: usuario@unisimon.edu.co):"
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", prompt_correo)
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": prompt_correo,
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
                }

        # -------------------------------------------------------------
        # ESTADO: PIDIENDO_ROL (Calificación Previa Obligatoria de Perfil)
        # -------------------------------------------------------------
        elif estado_actual == EstadoTicket.PIDIENDO_ROL:
            detected = cls.detect_user_role(texto)
            if not detected:
                detected = normalize_role(texto)

            if not detected:
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", MENSAJE_PIDIENDO_ROL)
                return {
                    "tipo": "PIDIENDO_ROL",
                    "state": "PIDIENDO_ROL",
                    "mensaje": MENSAJE_PIDIENDO_ROL,
                    "response": MENSAJE_PIDIENDO_ROL,
                    "reply": MENSAJE_PIDIENDO_ROL,
                    "ticket_id": None,
                    "source": "UniMon_PidiendoRol",
                    "quick_replies": ROLE_QUICK_REPLIES
                }

            session.user_role = detected
            logger.info(f"[Session: {session_id}] Rol confirmado en PIDIENDO_ROL: '{session.user_role}'")

            # Si la consulta previa retenida era fuera de dominio, purgarla inmediatamente para evitar contaminación
            if session.pending_query and is_out_of_domain_query(session.pending_query):
                session.pending_query = None

            # Verificar si existía una pregunta técnica previa válida retenida
            has_valid_query = bool(
                session.pending_query 
                and not cls.is_greeting(session.pending_query)
                and len(session.pending_query.strip()) > 3
                and not (cls.detect_user_role(session.pending_query) and len(session.pending_query.split()) <= 3)
                and not is_out_of_domain_query(session.pending_query)
            )

            # Si el usuario formuló una pregunta técnica real antes de calificar su rol:
            if has_valid_query:
                query_to_run = session.pending_query
                session.pending_query = None

                # ENRUTAMIENTO SEMÁNTICO: Fallas físicas / Hardware / Soporte en sitio
                intent_cat = await cls.classify_intent(query_to_run, session.user_role or "general")
                if intent_cat == "SOPORTE_FISICO":
                    session.falla = query_to_run
                    session.descripcion = query_to_run
                    session.categoria = CategoriaSolicitud.HARDWARE
                    session.category_name = "Mantenimiento Preventivo y Correctivo de Equipos y Redes"
                    session.urgency, session.impact = cls.calculate_urgency_and_impact(query_to_run)
                    session.estado = EstadoTicket.OFRECIENDO_RADICACION
                    session.nombre = None
                    session.correo = None
                    cls.add_history(session_id, "user", texto)
                    cls.add_history(session_id, "assistant", PROMPT_HARDWARE_DIRECT)
                    return {
                        "tipo": "OFRECIENDO_RADICACION",
                        "state": "OFRECIENDO_RADICACION",
                        "mensaje": PROMPT_HARDWARE_DIRECT,
                        "response": PROMPT_HARDWARE_DIRECT,
                        "reply": PROMPT_HARDWARE_DIRECT,
                        "ticket_id": None,
                        "source": "UniMon_SemanticRouter_Hardware",
                        "quick_replies": HARDWARE_QUICK_REPLIES
                    }

                # Consultar RAG con el rol confirmado y filtrar chunks
                # Golden Cache: buscar coincidencia previa
                golden_context = ""
                golden_hit = search_golden_case(query_to_run)
                if golden_hit:
                    prev_q, prev_ans, sim = golden_hit
                    golden_context = (
                        f"Ejemplo institucional de referencia:\n"
                        f"- Consulta similar: {prev_q}\n"
                        f"- Solución validada:\n{prev_ans}\n"
                    )
                    logger.info(f"[GoldenCache] Inyectando few-shot golden (sim={sim:.2f}) en PIDIENDO_ROL.")

                history = cls.get_history(session_id)
                rag_res = await rag_service.answer_query(
                    query=query_to_run,
                    user_role=session.user_role,
                    chat_history=history,
                    golden_context=golden_context
                )
                resp_text = rag_res.get("response", "")

                # Guardrail Fuera de Dominio
                if is_out_of_domain_response(resp_text):
                    cls.reset_session(session_id)
                    cls.add_history(session_id, "user", texto)
                    cls.add_history(session_id, "assistant", resp_text)
                    return {
                        "tipo": "FUERA_DE_DOMINIO",
                        "state": "FUERA_DE_DOMINIO",
                        "mensaje": resp_text,
                        "response": resp_text,
                        "reply": resp_text,
                        "ticket_id": None,
                        "sources": rag_res.get("sources"),
                        "source": rag_res.get("source", "ollama_rag"),
                        "quick_replies": []
                    }

                # Cero Alucinaciones / Sin Documentación
                if rag_res.get("has_context") is False or \
                   resp_text == MENSAJE_NO_DOCUMENTADO or \
                   "No dispongo de un procedimiento documentado" in resp_text or \
                   "No dispongo de un instructivo" in resp_text:
                    session.falla = query_to_run
                    cat, cat_name = cls.detect_category(query_to_run)
                    session.categoria = cat
                    session.category_name = cat_name
                    session.urgency, session.impact = cls.calculate_urgency_and_impact(query_to_run)
                    session.estado = EstadoTicket.OFRECIENDO_RADICACION
                    cls.add_history(session_id, "user", texto)
                    cls.add_history(session_id, "assistant", resp_text)
                    return {
                        "tipo": "OFRECIENDO_RADICACION",
                        "state": "OFRECIENDO_RADICACION",
                        "mensaje": resp_text,
                        "response": resp_text,
                        "reply": resp_text,
                        "ticket_id": None,
                        "sources": rag_res.get("sources", []),
                        "source": "UniMon_SinDocumentacion",
                        "quick_replies": [
                            {"label": "🎫 Generar reporte", "payload": "CREATE_TICKET"}
                        ]
                    }

                # Respuesta técnica documentada -> DIAGNOSTICO
                session.falla = query_to_run
                cat, cat_name = cls.detect_category(query_to_run)
                session.categoria = cat
                session.category_name = cat_name
                session.urgency, session.impact = cls.calculate_urgency_and_impact(query_to_run)
                session.intentos_diagnostico = 1
                session.diagnosis_attempts = 1
                session.estado = EstadoTicket.DIAGNOSTICO
                session.last_user_query = query_to_run
                session.last_bot_response = resp_text

                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", resp_text)
                return {
                    "tipo": "DIAGNOSTICO",
                    "state": "DIAGNOSTICO",
                    "mensaje": resp_text,
                    "response": resp_text,
                    "reply": resp_text,
                    "ticket_id": None,
                    "sources": rag_res.get("sources"),
                    "source": rag_res.get("source", "ollama_rag"),
                    "prompt_tokens": rag_res.get("prompt_tokens", 0),
                    "eval_tokens": rag_res.get("eval_tokens", 0),
                    "quick_replies": rag_res.get("quick_replies", [
                        {"label": "✅ Sí, me funcionó", "payload": "RESOLVED"},
                        {"label": "🔄 No me funcionó", "payload": "RETRY_DIAGNOSIS"},
                        {"label": "🎫 Generar reporte", "payload": "CREATE_TICKET"}
                    ])
                }
            else:
                # No había pregunta previa (saludo inicial o calificación limpia de rol)
                session.pending_query = None
                session.estado = EstadoTicket.DIAGNOSTICO
                session.diagnosis_attempts = 1
                session.intentos_diagnostico = 1
                ready_msg = "¡Entendido! ¿En qué procedimiento institucional o falla técnica te puedo colaborar hoy?"
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", ready_msg)
                return {
                    "tipo": "DIAGNOSTICO",
                    "state": "DIAGNOSTICO",
                    "mensaje": ready_msg,
                    "response": ready_msg,
                    "reply": ready_msg,
                    "ticket_id": None,
                    "source": "UniMon_Assistant",
                    "quick_replies": []
                }

        # -------------------------------------------------------------
        # ESTADO: OFRECIENDO_RADICACION (Canal de Correo + Plantilla entregados)
        # -------------------------------------------------------------
        elif estado_actual == EstadoTicket.OFRECIENDO_RADICACION:
            # 0. Si el usuario envía payload de feedback
            if texto.upper() in ["RESOLVED", "CREATE_TICKET"]:
                feedback_res = handle_feedback_transition(texto, "OFRECIENDO_RADICACION", session)
                if feedback_res:
                    if feedback_res.get("state") == "FINALIZADO":
                        cls.reset_session(session_id)
                        cls.add_history(session_id, "user", texto)
                        cls.add_history(session_id, "assistant", feedback_res["response"])
                        return {
                            "tipo": "FINALIZADO",
                            "state": "FINALIZADO",
                            "mensaje": feedback_res["response"],
                            "response": feedback_res["response"],
                            "reply": feedback_res["response"],
                            "ticket_id": None,
                            "source": "UniMon_Feedback_Success",
                            "quick_replies": []
                        }
                    elif feedback_res.get("state") == "RADICANDO_TICKET":
                        session.nombre = None
                        session.correo = None
                        session.descripcion = None
                        session.estado = EstadoTicket.PIDIENDO_NOMBRE
                        cls.add_history(session_id, "user", texto)
                        cls.add_history(session_id, "assistant", feedback_res["response"])
                        return {
                            "tipo": "RADICANDO_TICKET",
                            "state": "RADICANDO_TICKET",
                            "mensaje": feedback_res["response"],
                            "response": feedback_res["response"],
                            "reply": feedback_res["response"],
                            "ticket_id": None,
                            "source": "UniMon_SlotFilling",
                            "quick_replies": []
                        }

            # 1. Si el usuario confirma o pide reportar ("sí", "vamos a reportar", "radicar", "por favor", "ayúdame", etc.):
            # NUNCA guardar la afirmación como nombre; transicionar limpiamente a PIDIENDO_NOMBRE.
            if cls.is_report_request(texto):
                session.nombre = None
                session.correo = None
                session.descripcion = None
                session.estado = EstadoTicket.PIDIENDO_NOMBRE
                prompt_msg = "Con gusto te ayudo a radicar el caso. Para iniciar, por favor indícame tu **Nombre Completo**:"
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", prompt_msg)
                return {
                    "tipo": "RADICANDO_TICKET",
                    "state": "RADICANDO_TICKET",
                    "mensaje": prompt_msg,
                    "response": prompt_msg,
                    "reply": prompt_msg,
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling",
                    "quick_replies": []
                }

            # 2. Si el usuario responde con un saludo de cortesía
            elif cls.is_greeting(texto):
                cls.reset_session(session_id)
                greeting_reply = (
                    "¡Hola! 👋 Soy **UniMon**, el Asistente Virtual Oficial de Soporte Técnico y Gestión de TI de la Universidad Simón Bolívar. "
                    "¿En qué te puedo colaborar hoy?"
                )
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", greeting_reply)
                return {
                    "tipo": "SALUDO",
                    "state": "SALUDO",
                    "mensaje": greeting_reply,
                    "response": greeting_reply,
                    "reply": greeting_reply,
                    "ticket_id": None,
                    "source": "UniMon_Assistant",
                    "quick_replies": []
                }

            # 3. Cualquier otra respuesta en este estado: evaluar nueva pregunta
            else:
                history = cls.get_history(session_id)
                rag_res = await rag_service.answer_query(
                    query=texto,
                    user_role=session.user_role,
                    chat_history=history
                )
                resp_text = rag_res.get("response", "")

                # Si no hay documentación para la nueva pregunta, forzar permanencia en OFRECIENDO_RADICACION
                if rag_res.get("has_context") is False or \
                   resp_text == MENSAJE_NO_DOCUMENTADO or \
                   "No dispongo de un procedimiento documentado" in resp_text or \
                   "No dispongo de un instructivo" in resp_text:
                    session.falla = texto
                    session.estado = EstadoTicket.OFRECIENDO_RADICACION
                    cls.add_history(session_id, "user", texto)
                    cls.add_history(session_id, "assistant", resp_text)
                    return {
                        "tipo": "OFRECIENDO_RADICACION",
                        "state": "OFRECIENDO_RADICACION",
                        "mensaje": resp_text,
                        "response": resp_text,
                        "reply": resp_text,
                        "ticket_id": None,
                        "sources": [],
                        "source": "UniMon_SinDocumentacion",
                        "quick_replies": []
                    }

                session.estado = EstadoTicket.DIAGNOSTICO
                session.intentos_diagnostico = 1
                session.falla = texto
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", resp_text)
                return {
                    "tipo": "DIAGNOSTICO",
                    "state": "DIAGNOSTICO",
                    "mensaje": resp_text,
                    "response": resp_text,
                    "reply": resp_text,
                    "ticket_id": None,
                    "sources": rag_res.get("sources"),
                    "source": rag_res.get("source", "ollama_rag"),
                    "quick_replies": rag_res.get("quick_replies", [
                        {"label": "✅ Sí, me funcionó", "payload": "RESOLVED"},
                        {"label": "🎫 No, radicar ticket", "payload": "CREATE_TICKET"}
                    ])
                }

        # -------------------------------------------------------------
        # ESTADO: DIAGNOSTICO (Diagnóstico continuo e ilimitado)
        # -------------------------------------------------------------
        elif estado_actual == EstadoTicket.DIAGNOSTICO:
            # Caso 0: Desambiguación de Feedback del usuario (Sí funcionó / No funcionó / Ticket)
            feedback_res = handle_feedback_transition(texto, "DIAGNOSTICO", session)
            if feedback_res:
                if feedback_res.get("state") == "FINALIZADO" or feedback_res.get("tipo") == "FINALIZADO":
                    # Golden Cache: guardar caso resuelto con feedback positivo
                    if session.last_user_query and session.last_bot_response:
                        try:
                            save_golden_case(
                                session_id=session_id,
                                user_query=session.last_user_query,
                                bot_response=session.last_bot_response,
                                role=session.user_role or "general"
                            )
                        except Exception as e:
                            logger.warning(f"[GoldenCache] Error al guardar caso resuelto: {e}")
                    cls.reset_session(session_id)
                    cls.add_history(session_id, "user", texto)
                    cls.add_history(session_id, "assistant", feedback_res["response"])
                    return {
                        "tipo": "FINALIZADO",
                        "state": "FINALIZADO",
                        "mensaje": feedback_res["response"],
                        "response": feedback_res["response"],
                        "reply": feedback_res["response"],
                        "ticket_id": None,
                        "source": feedback_res.get("source", "UniMon_Feedback_Success"),
                        "quick_replies": []
                    }
                elif feedback_res.get("state") == "DIAGNOSTICO" or feedback_res.get("tipo") == "DIAGNOSTICO":
                    # Invalidar caso previo en Golden Cache si el usuario reporta que no le funcionó (RETRY_DIAGNOSIS)
                    if session.last_user_query:
                        try:
                            invalidate_golden_cache_entry(session.last_user_query, session.user_role or "general")
                        except Exception as e:
                            logger.warning(f"[GoldenCache] Error al auto-invalidar entrada en retry: {e}")
                    session.estado = EstadoTicket.DIAGNOSTICO
                    cls.add_history(session_id, "user", texto)
                    cls.add_history(session_id, "assistant", feedback_res["response"])
                    return {
                        "tipo": "DIAGNOSTICO",
                        "state": "DIAGNOSTICO",
                        "mensaje": feedback_res["response"],
                        "response": feedback_res["response"],
                        "reply": feedback_res["response"],
                        "ticket_id": None,
                        "source": feedback_res.get("source", "UniMon_Diagnostico_Retry"),
                        "quick_replies": feedback_res.get("quick_replies", [
                            {"label": "🎫 Generar reporte a soporte", "payload": "CREATE_TICKET"}
                        ])
                    }
                elif feedback_res.get("state") == "RADICANDO_TICKET" or feedback_res.get("tipo") == "RADICANDO_TICKET":
                    # Invalidar caso previo en Golden Cache si el usuario decide escalar a ticket por falla
                    if session.last_user_query:
                        try:
                            invalidate_golden_cache_entry(session.last_user_query, session.user_role or "general")
                        except Exception as e:
                            logger.warning(f"[GoldenCache] Error al auto-invalidar entrada en escalación a ticket: {e}")
                    session.nombre = None
                    session.correo = None
                    session.descripcion = None
                    session.estado = EstadoTicket.PIDIENDO_NOMBRE
                    cls.add_history(session_id, "user", texto)
                    cls.add_history(session_id, "assistant", feedback_res["response"])
                    return {
                        "tipo": "RADICANDO_TICKET",
                        "state": "RADICANDO_TICKET",
                        "mensaje": feedback_res["response"],
                        "response": feedback_res["response"],
                        "reply": feedback_res["response"],
                        "ticket_id": None,
                        "source": feedback_res.get("source", "UniMon_SlotFilling"),
                        "quick_replies": []
                    }

            # Caso A: Saludo en medio de diagnóstico -> Saludar y resetear
            if cls.is_greeting(texto):
                cls.reset_session(session_id)
                greeting_reply = (
                    "¡Hola! 👋 Soy **UniMon**, el Asistente Virtual Oficial de Soporte Técnico y Gestión de TI de la Universidad Simón Bolívar. "
                    "¿En qué te puedo colaborar hoy? Puedes consultarme sobre procedimientos institucionales (backups, cuentas, antimalware, Seven/Kactus) "
                    "o indicarme si presentas alguna falla con tus equipos o servicios para ayudarte."
                )
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", greeting_reply)
                return {
                    "tipo": "SALUDO",
                    "state": "SALUDO",
                    "mensaje": greeting_reply,
                    "response": greeting_reply,
                    "reply": greeting_reply,
                    "ticket_id": None,
                    "source": "UniMon_Assistant",
                    "quick_replies": []
                }

            # Caso B: Solicitud explícita e inequívoca de radicación de ticket ("crear ticket", "radicar caso")
            if cls.is_explicit_ticket_request(texto):
                session.nombre = None
                session.correo = None
                session.descripcion = None
                session.estado = EstadoTicket.PIDIENDO_NOMBRE
                prompt_msg = "Con gusto te ayudo a radicar el caso. Para iniciar, por favor indícame tu **Nombre Completo**:"
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", prompt_msg)
                return {
                    "tipo": "RADICANDO_TICKET",
                    "state": "RADICANDO_TICKET",
                    "mensaje": prompt_msg,
                    "response": prompt_msg,
                    "reply": prompt_msg,
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling",
                    "quick_replies": []
                }

            # Caso C: Diagnóstico continuo e ilimitado mediante RAG contextual
            session.intentos_diagnostico += 1
            history = cls.get_history(session_id)
            query_ctx = texto

            # Golden Cache: buscar coincidencia previa antes del RAG completo
            golden_context = ""
            golden_hit = search_golden_case(query_ctx)
            if golden_hit:
                prev_q, prev_ans, sim = golden_hit
                golden_context = (
                    f"Ejemplo institucional de referencia:\n"
                    f"- Consulta similar: {prev_q}\n"
                    f"- Solución validada:\n{prev_ans}\n"
                )
                logger.info(f"[GoldenCache] Inyectando few-shot golden (sim={sim:.2f}) en diagnóstico.")


            rag_res = await rag_service.answer_query(
                query=query_ctx,
                user_role=session.user_role,
                chat_history=history,
                golden_context=golden_context
            )
            resp_text = rag_res.get("response", "")

            # Si el RAG confiesa no tener documentación relevante, forzar de inmediato OFRECIENDO_RADICACION
            if rag_res.get("has_context") is False or \
               resp_text == MENSAJE_NO_DOCUMENTADO or \
               "No dispongo de un procedimiento documentado" in resp_text or \
               "No dispongo de un instructivo" in resp_text:
                session.estado = EstadoTicket.OFRECIENDO_RADICACION
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", resp_text)
                return {
                    "tipo": "OFRECIENDO_RADICACION",
                    "state": "OFRECIENDO_RADICACION",
                    "mensaje": resp_text,
                    "response": resp_text,
                    "reply": resp_text,
                    "ticket_id": None,
                    "sources": rag_res.get("sources", []),
                    "source": "UniMon_SinDocumentacion",
                    "quick_replies": []
                }

            # Si el usuario cambió a una pregunta fuera de dominio, liberar sesión
            if is_out_of_domain_response(resp_text):
                cls.reset_session(session_id)
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", resp_text)
                return {
                    "tipo": "FUERA_DE_DOMINIO",
                    "state": "FUERA_DE_DOMINIO",
                    "mensaje": resp_text,
                    "response": resp_text,
                    "reply": resp_text,
                    "ticket_id": None,
                    "sources": rag_res.get("sources"),
                    "source": rag_res.get("source", "ollama_rag"),
                    "quick_replies": []
                }

            # Rastrear consulta y respuesta para Golden Cache
            session.last_user_query = query_ctx
            session.last_bot_response = resp_text

            cls.add_history(session_id, "user", texto)
            cls.add_history(session_id, "assistant", resp_text)

            return {
                "tipo": "DIAGNOSTICO",
                "state": "DIAGNOSTICO",
                "mensaje": resp_text,
                "response": resp_text,
                "reply": resp_text,
                "ticket_id": None,
                "sources": rag_res.get("sources"),
                "source": rag_res.get("source", "ollama_rag"),
                "prompt_tokens": rag_res.get("prompt_tokens", 0),
                "eval_tokens": rag_res.get("eval_tokens", 0),
                "quick_replies": rag_res.get("quick_replies", [
                    {"label": "✅ Sí, me funcionó", "payload": "RESOLVED"},
                    {"label": "🎫 No, radicar ticket", "payload": "CREATE_TICKET"}
                ])
            }

        # -------------------------------------------------------------
        # ESTADO: IDLE (Mensaje Inicial / Nueva Conversación)
        # -------------------------------------------------------------
        else:
            # 1. Guardrail rápido de Fuera de Dominio (Out-of-Domain)
            if is_out_of_domain_query(texto):
                cls.reset_session(session_id)
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", MENSAJE_FUERA_DE_DOMINIO)
                return {
                    "tipo": "FUERA_DE_DOMINIO",
                    "mensaje": MENSAJE_FUERA_DE_DOMINIO,
                    "ticket_id": None,
                    "source": "UniMon_Guardrail"
                }

            # 2. Si el usuario NO tiene rol asignado en la sesión:
            if not session.user_role:
                detected_role = cls.detect_user_role(texto) or normalize_role(texto)
                has_question_keywords = any(w in texto.lower() for w in [
                    "?", "¿", "dónde", "donde", "cómo", "como", "por qué", "porque", 
                    "por dónde", "por donde", "subo", "puedo", "quiero", "necesito", 
                    "ayuda", "autoevaluacion", "autoevaluación", "clave", "contraseña", 
                    "portal", "fallas", "problema", "error", "calificaciones", "promedio"
                ])
                is_just_role_declaration = bool(detected_role and len(texto.split()) <= 4 and not has_question_keywords)

                if is_just_role_declaration:
                    # El usuario envió únicamente su rol (ej: "estudiante", "profesor", "soy docente", "administrativo")
                    session.user_role = detected_role
                    logger.info(f"[Session: {session_id}] Rol identificado en primer mensaje: '{session.user_role}'")
                    session.estado = EstadoTicket.DIAGNOSTICO
                    session.diagnosis_attempts = 1
                    session.intentos_diagnostico = 1
                    greeting_reply = (
                        "¡Hola! 👋 Soy **UniMon**, el Asistente Virtual Oficial de TI de la Universidad Simón Bolívar. "
                        "¿En qué procedimiento institucional o falla técnica te puedo colaborar hoy?"
                    )
                    cls.add_history(session_id, "user", texto)
                    cls.add_history(session_id, "assistant", greeting_reply)
                    return {
                        "tipo": "DIAGNOSTICO",
                        "state": "DIAGNOSTICO",
                        "mensaje": greeting_reply,
                        "response": greeting_reply,
                        "reply": greeting_reply,
                        "ticket_id": None,
                        "source": "UniMon_Assistant",
                        "quick_replies": []
                    }
                else:
                    # El usuario formuló una pregunta o saludo sin haber seleccionado su rol previamente.
                    # Retener la consulta y solicitar OBLIGATORIAMENTE la selección de rol.
                    if not cls.is_greeting(texto) and len(texto.split()) > 1 and not cls.is_cancellation(texto) and not is_out_of_domain_query(texto):
                        session.pending_query = texto
                    else:
                        session.pending_query = None
                    session.estado = EstadoTicket.PIDIENDO_ROL
                    cls.add_history(session_id, "user", texto)
                    cls.add_history(session_id, "assistant", MENSAJE_PIDIENDO_ROL)
                    return {
                        "tipo": "PIDIENDO_ROL",
                        "state": "PIDIENDO_ROL",
                        "mensaje": MENSAJE_PIDIENDO_ROL,
                        "response": MENSAJE_PIDIENDO_ROL,
                        "reply": MENSAJE_PIDIENDO_ROL,
                        "ticket_id": None,
                        "source": "UniMon_Assistant",
                        "quick_replies": ROLE_QUICK_REPLIES
                    }

            # Si ya tiene rol en la sesión:
            # 3. Saludo simple
            if cls.is_greeting(texto):
                greeting_reply = (
                    "¡Hola! 👋 Soy **UniMon**, el Asistente Virtual Oficial de TI de la Universidad Simón Bolívar. "
                    "¿En qué te puedo colaborar hoy? Puedes consultarme sobre procedimientos institucionales (backups, cuentas, antimalware, Seven/Kactus) "
                    "o indicarme si presentas alguna falla con tus equipos o servicios para ayudarte."
                )
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", greeting_reply)
                return {
                    "tipo": "SALUDO",
                    "mensaje": greeting_reply,
                    "ticket_id": None,
                    "source": "UniMon_Assistant"
                }

            # 4. ENRUTAMIENTO SEMÁNTICO: Fallas físicas / Hardware / Soporte en sitio
            intent_cat = await cls.classify_intent(texto, session.user_role or "general")
            if intent_cat == "SOPORTE_FISICO":
                session.falla = texto
                session.descripcion = texto
                session.categoria = CategoriaSolicitud.HARDWARE
                session.category_name = "Mantenimiento Preventivo y Correctivo de Equipos y Redes"
                session.urgency, session.impact = cls.calculate_urgency_and_impact(texto)
                session.estado = EstadoTicket.OFRECIENDO_RADICACION
                session.nombre = None
                session.correo = None
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", PROMPT_HARDWARE_DIRECT)
                return {
                    "tipo": "OFRECIENDO_RADICACION",
                    "state": "OFRECIENDO_RADICACION",
                    "mensaje": PROMPT_HARDWARE_DIRECT,
                    "response": PROMPT_HARDWARE_DIRECT,
                    "reply": PROMPT_HARDWARE_DIRECT,
                    "ticket_id": None,
                    "source": "UniMon_SemanticRouter_Hardware",
                    "quick_replies": HARDWARE_QUICK_REPLIES
                }

            # 6. Solicitud de Trámites Administrativos o Técnico Directo (Sin diagnóstico simulado)
            if cls.is_physical_or_admin_request(texto) or cls.is_direct_tech_request(texto):
                session.falla = texto
                cat, cat_name = cls.detect_category(texto)
                session.categoria = cat
                session.category_name = cat_name
                session.urgency, session.impact = cls.calculate_urgency_and_impact(texto)
                session.estado = EstadoTicket.OFRECIENDO_RADICACION
                support_msg = cls.build_support_channel_message(session.falla)
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", support_msg)
                return {
                    "tipo": "OFRECIENDO_RADICACION",
                    "state": "OFRECIENDO_RADICACION",
                    "mensaje": support_msg,
                    "response": support_msg,
                    "reply": support_msg,
                    "ticket_id": None,
                    "source": "UniMon_CanalSoporte",
                    "quick_replies": []
                }

            # 7. Consultar RAG con historial conversacional y rol de usuario
            # Golden Cache: buscar coincidencia previa
            golden_context = ""
            golden_hit = search_golden_case(texto)
            if golden_hit:
                prev_q, prev_ans, sim = golden_hit
                golden_context = (
                    f"Ejemplo institucional de referencia:\n"
                    f"- Consulta similar: {prev_q}\n"
                    f"- Solución validada:\n{prev_ans}\n"
                )
                logger.info(f"[GoldenCache] Inyectando few-shot golden (sim={sim:.2f}) en IDLE.")

            history = cls.get_history(session_id)
            rag_res = await rag_service.answer_query(
                query=texto,
                user_role=session.user_role,
                chat_history=history,
                golden_context=golden_context
            )
            resp_text = rag_res.get("response", "")

            # 7. Guardrail Fuera de Dominio según respuesta generada
            if is_out_of_domain_response(resp_text):
                cls.reset_session(session_id)
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", resp_text)
                return {
                    "tipo": "FUERA_DE_DOMINIO",
                    "mensaje": resp_text,
                    "ticket_id": None,
                    "sources": rag_res.get("sources"),
                    "source": rag_res.get("source", "ollama_rag")
                }

            # 8. Cero Alucinaciones / Falta de Documentación: Forzar OFRECIENDO_RADICACION
            if rag_res.get("has_context") is False or \
               resp_text == MENSAJE_NO_DOCUMENTADO or \
               "No dispongo de un procedimiento documentado" in resp_text or \
               "No dispongo de un instructivo" in resp_text:
                session.falla = texto
                cat, cat_name = cls.detect_category(texto)
                session.categoria = cat
                session.category_name = cat_name
                session.urgency, session.impact = cls.calculate_urgency_and_impact(texto)
                session.estado = EstadoTicket.OFRECIENDO_RADICACION
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", resp_text)
                return {
                    "tipo": "OFRECIENDO_RADICACION",
                    "mensaje": resp_text,
                    "ticket_id": None,
                    "sources": rag_res.get("sources", []),
                    "source": "UniMon_SinDocumentacion"
                }

            # 9. Caso dentro de dominio con contexto documentado: Iniciar Diagnóstico Multi-Turno (Intento 1 de 3)
            session.falla = texto
            cat, cat_name = cls.detect_category(texto)
            session.categoria = cat
            session.category_name = cat_name
            session.urgency, session.impact = cls.calculate_urgency_and_impact(texto)
            session.intentos_diagnostico = 1
            session.estado = EstadoTicket.DIAGNOSTICO
            session.last_user_query = texto
            session.last_bot_response = resp_text

            cls.add_history(session_id, "user", texto)
            cls.add_history(session_id, "assistant", resp_text)

            return {
                "tipo": "DIAGNOSTICO",
                "state": "DIAGNOSTICO",
                "mensaje": resp_text,
                "response": resp_text,
                "reply": resp_text,
                "ticket_id": None,
                "sources": rag_res.get("sources"),
                "source": rag_res.get("source", "ollama_rag"),
                "prompt_tokens": rag_res.get("prompt_tokens", 0),
                "eval_tokens": rag_res.get("eval_tokens", 0),
                "quick_replies": rag_res.get("quick_replies", [
                    {"label": "✅ Sí, me funcionó", "payload": "RESOLVED"},
                    {"label": "🎫 No, radicar ticket", "payload": "CREATE_TICKET"}
                ])
            }


# Instancia por defecto
router_logic = RouterLogic()
