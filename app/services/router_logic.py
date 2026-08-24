"""
Lógica de Enrutamiento, Clasificación de Intenciones y Chatbot Proactivo de Nivel 1 para UniMon (USB).
Maneja el ciclo de diagnóstico multi-turno de Nivel 1 (hasta 3 intentos), detección inmediata de solicitudes
físicas y préstamos de equipos (sin bucles de diagnóstico ni consultas al LLM), flujo universal de cancelación,
entrega de canal oficial por correo con plantilla estructurada y radicación por Slot-Filling universal simplificado
en secuencia estricta de 3 pasos (Nombre Completo -> Correo Electrónico -> Descripción Detallada del Requerimiento/Problema).
"""

import logging
import re
from typing import Dict, Any, Tuple, Optional, List
from enum import Enum
from pydantic import BaseModel, Field

from app.services.rag_service import rag_service, is_out_of_domain_response
from app.services.glpi_service import glpi_client, is_valid_email

logger = logging.getLogger("unimon.router_logic")


class EstadoTicket(str, Enum):
    IDLE = "IDLE"
    DIAGNOSTICO = "DIAGNOSTICO"
    OFRECIENDO_RADICACION = "OFRECIENDO_RADICACION"
    PIDIENDO_NOMBRE = "PIDIENDO_NOMBRE"
    PIDIENDO_CORREO = "PIDIENDO_CORREO"
    PIDIENDO_DESCRIPCION = "PIDIENDO_DESCRIPCION"
    # Campos de compatibilidad hacia atrás
    PIDIENDO_UBICACION = "PIDIENDO_UBICACION"
    PIDIENDO_ACTIVO = "PIDIENDO_ACTIVO"


# Alias para compatibilidad hacia atrás
IntentType = EstadoTicket


class CategoriaSolicitud(str, Enum):
    SOFTWARE = "SOFTWARE"
    HARDWARE = "HARDWARE"


class TicketSession(BaseModel):
    """Estructura de la sesión conversacional de soporte y tickets."""
    session_id: str
    estado: EstadoTicket = EstadoTicket.IDLE
    categoria: CategoriaSolicitud = CategoriaSolicitud.HARDWARE
    intentos_diagnostico: int = 0
    max_intentos_diagnostico: int = 3  # Diagnóstico multi-turno (2 a 3 intentos)
    falla: Optional[str] = None
    descripcion: Optional[str] = None
    nombre: Optional[str] = None
    correo: Optional[str] = None
    ubicacion: Optional[str] = None
    activo: Optional[str] = None
    urgency: int = 3
    impact: int = 3
    category_name: Optional[str] = "Soporte Técnico y Gestión de TI Unisimon"


# Almacén de sesiones en memoria indexado por session_id
ticket_sessions: Dict[str, TicketSession] = {}

# Almacén de historial conversacional en memoria indexado por session_id (últimos mensajes)
session_history: Dict[str, List[Dict[str, str]]] = {}

# Saludos simples y cortesía
GREETING_PATTERNS = [
    r"^hola\b", r"^buenos d[ií]as\b", r"^buenas tardes\b", r"^buenas noches\b",
    r"^buenas\b", r"^hey\b", r"^saludos\b", r"^[¿?]?c[oó]mo est[aá]s\b",
    r"^[¿?]?qu[eé] tal\b", r"^buen d[ií]a\b", r"^hi\b", r"^hello\b"
]

# Patrones de Cancelación Universal durante el flujo de radicación
CANCEL_PATTERNS = [
    "cancelar", "cancela", "ya no", "no gracias", "olvidalo", "olvídalo",
    "dejalo asi", "déjalo así", "no quiero", "no deseo", "cancelar radicación",
    "cancelar radicacion", "cancelar ticket"
]

CANCEL_REGEX = [
    r"\b(cancelar|cancela|ya\s+no|no\s+gracias|olvidalo|olv[ií]dalo|dejalo\s+asi|d[eé]jalo\s+as[ií]|no\s+quiero|no\s+deseo|cancelar\s+ticket|cancelar\s+radicaci[oó]n)\b"
]

MENSAJE_CANCELACION = "Entendido, he cancelado el proceso de radicación. ¿Hay algo más sobre los procedimientos de TI en lo que te pueda colaborar?"

# Palabras clave para Requerimiento de Equipos y Préstamos
EQUIPMENT_REQUEST_PATTERNS = [
    "prestamo", "préstamo", "prestar", "solicitar", "microfono", "micrófono", 
    "tablet", "portatil", "portátil", "computador", "laptop", 
    "videobeam", "video beam", "proyector", "sala", "pantalla", "auditorio"
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
    "¿Deseas que radique este requerimiento de servicio directamente en GLPI por ti ahora mismo?"
)

# Respuestas de resolución / cierre ("no ya", "ya no", "ya no necesito", "ya pude", "ya funcionó", "listo", etc.)
SOLVED_PATTERNS = [
    r"\bno\s+ya\b",
    r"\bya\s+no\b",
    r"\bya\s+no\s+necesito\b",
    r"\bya\s+no\s+es\s+necesario\b",
    r"\bya\s+pude\b",
    r"\bya\s+pudo\b",
    r"\bya\s+funcion[oó]\b",
    r"\bya\s+funsion[oó]\b",
    r"\bya\s+sirve\b",
    r"\bya\s+sirvi[oó]\b",
    r"\bya\s+cirvi[oó]\b",
    r"\blisto\b",
    r"\bse\s+solucion[oó]\b",
    r"\bse\s+solusion[oó]\b",
    r"\bsolucionado\b",
    r"\bresuelto\b",
    r"\bqued[oó]\s+bien\b",
    r"\bya\s+qued[oó]\b",
    r"\bse\s+arregl[oó]\b",
    r"\bmuchas\s+gracias\b",
    r"\bgracias\b",
    r"\bgrasias\b",
    r"\bexcelente\b",
    r"\bperfecto\b",
    r"\bya\s+prendi[oó]\b",
    r"\bya\s+conect[oó]\b",
    r"\bya\s+dio\s+video\b",
    r"\btodo\s+bien\b",
    r"\btodo\s+en\s+orden\b",
    r"\bya\s+resolv[ií]\b",
    r"\bno\s+ya\s+resolv[ií]\b",
]

# Patrones explícitos de falla / persistencia
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

# Solicitud directa y explícita de técnico / radicación humana / soporte oficial
DIRECT_TECH_PATTERNS = [
    r"\b(crear(\s+un)?\s+ticket|abrir(\s+un)?\s+ticket|generar(\s+un)?\s+ticket|solicitar(\s+un)?\s+ticket|radicar(\s+un)?\s+ticket|radicar(\s+el)?(\s+caso)?|radicarlo|radicarla|necesito(\s+un|\s+a\s+un|\s+a\s+alguien|\s+ayuda|\s+soporte)?\s+(t[eé]cnico|presencial|soporte)|que\s+(lo|la|los|las|el\s+equipo|la\s+\w+|el\s+\w+|un\s+\w+)?\s*revisen|que\s+revisen|que\s+venga\s+un\s+t[eé]cnico|manda(r)?\s+un\s+t[eé]cnico|visita\s+t[eé]cnica|soporte\s+presencial|revisi[oó]n\s+t[eé]cnica|escalar(\s+el)?(\s+caso)?|atenci[oó]n\s+humana)\b"
]

# Trámites administrativos, cambios de permisos o compras (sin diagnóstico simulado)
ADMIN_PERMISSIONS_PATTERNS = [
    r"\b(cambio\s+de\s+permisos|autorizar\s+permisos|asignar\s+permisos|compra\s+de|adquisici[oó]n|inventario|revisi[oó]n\s+f[ií]sica|dar\s+de\s+baja|mantenimiento\s+preventivo\s+f[ií]sico)\b"
]

# Expresiones afirmativas y de confirmación de radicación / continuación
AFFIRMATIVE_PATTERNS = [
    r"^(s[ií]|ok|dale|claro|por favor|porfa|adelante|de acuerdo|s[ií] por favor|s[ií] claro|s[ií] dale|rad[ií]calo|radicar|hazlo|procede|ay[uú]dame|por ti|radicarlo|s[ií]\s+ay[uú]dame|bueno)\b"
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

# Regex estándar para extracción y validación de correo
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

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
    def reset_session(cls, session_id: str, keep_history: bool = False) -> None:
        """Limpia y resetea la sesión del usuario a IDLE."""
        if session_id in ticket_sessions:
            ticket_sessions[session_id] = TicketSession(session_id=session_id)
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
    def is_greeting(cls, text: str) -> bool:
        """Detecta si el mensaje es únicamente un saludo de cortesía."""
        msg_clean = re.sub(r"[^\w\s\?¿]", "", text.strip().lower())
        words = msg_clean.split()
        if len(words) <= 5:
            return any(re.search(pat, msg_clean) for pat in GREETING_PATTERNS)
        return False

    @classmethod
    def is_cancellation(cls, text: str) -> bool:
        """
        Detecta si el usuario solicita cancelar el proceso de radicación
        ('cancelar', 'cancela', 'ya no', 'no gracias', 'olvidalo', 'dejalo asi', 'no quiero').
        """
        msg_clean = re.sub(r"[^\w\s]", " ", text.strip().lower())
        msg_clean = re.sub(r"\s+", " ", msg_clean).strip()
        if any(msg_clean == pat for pat in CANCEL_PATTERNS):
            return True
        return any(re.search(pat, msg_clean) for pat in CANCEL_REGEX)

    @classmethod
    def is_equipment_request(cls, text: str) -> bool:
        """
        Detecta directamente si el mensaje corresponde a una solicitud de préstamo o asignación de equipos
        (micrófonos, tablets, portátiles, proyectores, videobeam, computadores, etc.).
        """
        msg_clean = text.strip().lower()

        # 1. Palabras explícitas de préstamo/asignación
        if any(p in msg_clean for p in ["prestamo", "préstamo", "prestar", "préstame", "prestame", "prestan", "alquiler", "alquilar"]):
            return True

        # 2. Combinación de verbos de solicitud con palabras clave de equipos físicos
        request_verbs = ["solicitar", "solicito", "solicitud", "pedir", "pido", "requiero", "necesito", "asignacion", "asignación", "reserva", "reservar", "quiero"]
        equipment_nouns = ["microfono", "micrófono", "tablet", "tablets", "portatil", "portátil", "portatiles", "portátiles", "computador", "computadores", "laptop", "laptops", "videobeam", "video beam", "proyector", "proyectores", "sala", "pantalla", "auditorio", "equipo", "equipos"]

        has_verb = any(v in msg_clean for v in request_verbs)
        has_equipment = any(eq in msg_clean for eq in equipment_nouns)

        if has_verb and has_equipment:
            # Descartar si se trata de un reporte de falla técnica para no interrumpir el diagnóstico
            failure_words = ["no prende", "no funciona", "no enciende", "parpadea", "dañado", "dañada", "roto", "rota", "fallando", "bloqueado", "bloqueada", "lento", "lenta", "error", "pantalla azul", "no da video", "se apaga"]
            if not any(f in msg_clean for f in failure_words):
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
        ("no ya", "ya no", "ya no necesito", "ya pude", "ya funcionó", "listo", etc.).
        """
        msg_clean = re.sub(r"[^\w\s]", " ", text.strip().lower())
        msg_clean = re.sub(r"\s+", " ", msg_clean).strip()

        # Comprobar si hay patrones explícitos de falla (ej: "no funcionó", "sigue igual", "no pude entrar")
        for pat in EXPLICIT_FAIL_PATTERNS:
            if re.search(pat, msg_clean):
                # A menos que sea explícitamente una frase de cierre positivo como "no ya", "ya funcionó", "ya pude"
                if not any(re.search(pos, msg_clean) for pos in [
                    r"\bno\s+ya\b", r"\bya\s+no\b", r"\bya\s+funcion[oó]\b", r"\bya\s+pude\b", r"\bya\s+sirvi[oó]\b"
                ]):
                    return False

        return any(re.search(pat, msg_clean) for pat in SOLVED_PATTERNS)

    @classmethod
    def is_direct_tech_request(cls, text: str) -> bool:
        """Detecta si el usuario pide explícitamente un técnico, visita o radicación directa."""
        msg_clean = text.strip().lower()
        return any(re.search(pat, msg_clean) for pat in DIRECT_TECH_PATTERNS)

    @classmethod
    def is_persisting_or_ticket_request(cls, text: str) -> bool:
        """Detecta si el usuario indica que la falla continúa tras el diagnóstico o pide técnico/ticket."""
        if cls.is_solved_confirmation(text) or cls.is_cancellation(text):
            return False
        msg_clean = re.sub(r"[^\w\s]", " ", text.strip().lower())
        msg_clean = re.sub(r"\s+", " ", msg_clean).strip()
        return any(re.search(pat, msg_clean) for pat in EXPLICIT_FAIL_PATTERNS) or cls.is_direct_tech_request(text)

    @classmethod
    def is_affirmative(cls, text: str) -> bool:
        """Detecta si el usuario envía una afirmación corta ('sí', 'claro', 'dale', 'por favor', 'radícalo', 'bueno', 'ayúdame')."""
        msg_clean = re.sub(r"[^\w\s\?¿áéíóúÁÉÍÓÚñÑ]", "", text.strip().lower())
        words = msg_clean.split()
        if len(words) <= 6:
            return any(re.search(pat, msg_clean) for pat in AFFIRMATIVE_PATTERNS)
        return False

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
        """Extrae el primer correo válido del texto."""
        match = EMAIL_REGEX.search(text)
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
        Genera el ticket en GLPI con el Slot-Filling universal simplificado
        (Nombre Completo, Correo Electrónico y Descripción Detallada del Requerimiento/Problema) y limpia la sesión.
        """
        falla_desc = session.descripcion or session.falla or "Requerimiento de soporte reportado por el usuario"
        nombre_sol = session.nombre or "Usuario Unisimon"
        correo_sol = session.correo or "solicitudcomputo@unisimon.edu.co"
        category_name = session.category_name or "Soporte Técnico y Gestión de TI Unisimon"

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
                "mensaje": f"Ocurrió un inconveniente al radicar el ticket en GLPI ({exc}). Por favor contacta a solicitudcomputo@unisimon.edu.co o helpdesk@unisimon.edu.co.",
                "ticket_id": None,
                "source": "GLPI_ERROR"
            }

    @classmethod
    async def procesar_mensaje(cls, mensaje: str, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Procesa el mensaje del usuario de acuerdo a la máquina de estados conversacional de Nivel 1.
        Aplica:
        1. Flujo de Cancelación Universal en cualquier estado de radicación.
        2. Detección inmediata de solicitudes de préstamos/asignación de equipos (sin bucles de diagnóstico ni consultas al LLM).
        3. Detección de cierre ("no ya", "ya no necesito", "ya pude", "ya funcionó", "listo").
        4. Diagnóstico multi-turno (hasta max_intentos_diagnostico = 3 intentos).
        5. Secuencia estricta de 3 pasos para Slot-Filling:
           Paso 1: Nombre Completo (Validación estricta, soporte cancelación)
           Paso 2: Correo Electrónico (Validación, soporte cancelación)
           Paso 3: Descripción Detallada del Requerimiento/Problema (Soporte cancelación)
           Paso 4: Radicación en GLPI (Ticket Creado)
        """
        texto = mensaje.strip()
        session = cls.get_session(session_id)
        estado_actual = session.estado

        logger.info(f"[Session: {session_id}] Estado: {estado_actual} | Intentos: {session.intentos_diagnostico}/{session.max_intentos_diagnostico} | Mensaje: '{texto[:50]}'")

        # -------------------------------------------------------------
        # REGLA GLOBAL 1: Flujo de Cancelación Universal
        # Si el usuario desea cancelar en cualquier estado de radicación
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
        # -------------------------------------------------------------
        if cls.is_solved_confirmation(texto):
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
        # ESTADO: PIDIENDO_DESCRIPCION (Paso 3 de Slot-Filling)
        # Recibe la descripción detallada del requerimiento o problema y guarda el texto exacto
        # -------------------------------------------------------------
        if estado_actual == EstadoTicket.PIDIENDO_DESCRIPCION:
            session.descripcion = texto
            session.falla = texto
            return await cls._radicar_ticket_en_glpi(session_id, session)

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
        # ESTADO: OFRECIENDO_RADICACION (Canal de Correo + Plantilla entregados)
        # -------------------------------------------------------------
        elif estado_actual == EstadoTicket.OFRECIENDO_RADICACION:
            # 1. Si el usuario confirma ("sí", "si ayudame", "por favor", "radícalo", "dale", "ayúdame"):
            # NUNCA guardar la afirmación como nombre; transicionar limpiamente a PIDIENDO_NOMBRE.
            if cls.is_affirmative(texto) or cls.is_direct_tech_request(texto):
                session.nombre = None
                session.correo = None
                session.descripcion = None
                session.estado = EstadoTicket.PIDIENDO_NOMBRE
                prompt_msg = "Con gusto te ayudo a radicar el caso. Para iniciar, por favor indícame tu **Nombre Completo**:"
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", prompt_msg)
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": prompt_msg,
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
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
                    "mensaje": greeting_reply,
                    "ticket_id": None,
                    "source": "UniMon_Assistant"
                }

            # 3. Cualquier otra respuesta en este estado: reiniciar diagnóstico para la nueva pregunta
            else:
                session.estado = EstadoTicket.DIAGNOSTICO
                session.intentos_diagnostico = 1
                session.falla = texto
                history = cls.get_history(session_id)
                rag_res = await rag_service.consultar(pregunta=texto, chat_history=history, es_diagnostico=False)
                resp_text = rag_res.get("response", "")
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", resp_text)
                return {
                    "tipo": "DIAGNOSTICO",
                    "mensaje": resp_text,
                    "ticket_id": None,
                    "sources": rag_res.get("sources"),
                    "source": rag_res.get("source", "ollama_rag")
                }

        # -------------------------------------------------------------
        # ESTADO: DIAGNOSTICO (Multi-turno: 2 a 3 intentos)
        # -------------------------------------------------------------
        elif estado_actual == EstadoTicket.DIAGNOSTICO:
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
                    "mensaje": greeting_reply,
                    "ticket_id": None,
                    "source": "UniMon_Assistant"
                }

            # Caso B: Solicitud de préstamo de equipos en medio de diagnóstico -> Mensaje directo estructurado
            if cls.is_equipment_request(texto):
                session.falla = texto
                session.estado = EstadoTicket.OFRECIENDO_RADICACION
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", MENSAJE_SOLICITUD_EQUIPOS)
                return {
                    "tipo": "OFRECIENDO_RADICACION",
                    "mensaje": MENSAJE_SOLICITUD_EQUIPOS,
                    "ticket_id": None,
                    "source": "UniMon_SolicitudEquipos"
                }

            # Caso C: Solicitud explícita de técnico / radicación directa o trámite administrativo durante diagnóstico
            if cls.is_direct_tech_request(texto) or cls.is_physical_or_admin_request(texto):
                session.estado = EstadoTicket.OFRECIENDO_RADICACION
                support_msg = cls.build_support_channel_message(session.falla or texto)
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", support_msg)
                return {
                    "tipo": "OFRECIENDO_RADICACION",
                    "mensaje": support_msg,
                    "ticket_id": None,
                    "source": "UniMon_CanalSoporte"
                }

            # Caso D: Evaluación de intentos multi-turno (hasta max_intentos_diagnostico = 3)
            if session.intentos_diagnostico < session.max_intentos_diagnostico:
                session.intentos_diagnostico += 1
                history = cls.get_history(session_id)

                # Contextualizar la consulta con la falla y el último turno si es afirmación o reporte de persistencia
                falla_ctx = session.falla or "soporte técnico institucional"
                if cls.is_affirmative(texto) or cls.is_persisting_or_ticket_request(texto):
                    query_ctx = f"El usuario indica sobre la falla '{falla_ctx}': '{texto}'. Proporciona el siguiente paso de diagnóstico o alternativa de solución técnica institucional."
                else:
                    query_ctx = texto

                rag_res = await rag_service.consultar(
                    pregunta=query_ctx,
                    chat_history=history,
                    es_diagnostico=False
                )
                resp_text = rag_res.get("response", "")

                # Si el usuario cambió a una pregunta fuera de dominio, liberar sesión
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

                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", resp_text)

                return {
                    "tipo": "DIAGNOSTICO",
                    "mensaje": resp_text,
                    "ticket_id": None,
                    "sources": rag_res.get("sources"),
                    "source": rag_res.get("source", "ollama_rag")
                }

            # Caso E: Intentos de diagnóstico agotados (>= 3 intentos) -> Ofrecer canal oficial de correo + plantilla + radicación directa
            else:
                session.estado = EstadoTicket.OFRECIENDO_RADICACION
                support_msg = cls.build_support_channel_message(session.falla or texto)
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", support_msg)
                return {
                    "tipo": "OFRECIENDO_RADICACION",
                    "mensaje": support_msg,
                    "ticket_id": None,
                    "source": "UniMon_CanalSoporte"
                }

        # -------------------------------------------------------------
        # ESTADO: IDLE (Mensaje Inicial)
        # -------------------------------------------------------------
        else:
            # 1. Saludo simple
            if cls.is_greeting(texto):
                greeting_reply = (
                    "¡Hola! 👋 Soy **UniMon**, el Asistente Virtual Oficial de Soporte Técnico y Gestión de TI de la Universidad Simón Bolívar. "
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

            # 2. Solicitud Directa de Préstamos / Asignación de Equipos (Sin consulta al RAG ni al LLM)
            if cls.is_equipment_request(texto):
                session.falla = texto
                session.categoria = CategoriaSolicitud.HARDWARE
                session.category_name = "Mantenimiento y Fallas de Cómputo (P-GT-01)"
                session.urgency, session.impact = cls.calculate_urgency_and_impact(texto)
                session.estado = EstadoTicket.OFRECIENDO_RADICACION

                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", MENSAJE_SOLICITUD_EQUIPOS)
                return {
                    "tipo": "OFRECIENDO_RADICACION",
                    "mensaje": MENSAJE_SOLICITUD_EQUIPOS,
                    "ticket_id": None,
                    "source": "UniMon_SolicitudEquipos"
                }

            # 3. Solicitud de Trámites Administrativos o Técnico Directo (Sin diagnóstico simulado)
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
                    "mensaje": support_msg,
                    "ticket_id": None,
                    "source": "UniMon_CanalSoporte"
                }

            # 4. Consultar RAG con historial conversacional
            history = cls.get_history(session_id)
            rag_res = await rag_service.consultar(
                pregunta=texto,
                chat_history=history,
                es_diagnostico=False
            )
            resp_text = rag_res.get("response", "")

            # 5. Guardrail Fuera de Dominio (Out-of-Domain)
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

            # 6. Caso dentro de dominio: Iniciar Diagnóstico Multi-Turno (Intento 1 de 3)
            session.falla = texto
            cat, cat_name = cls.detect_category(texto)
            session.categoria = cat
            session.category_name = cat_name
            session.urgency, session.impact = cls.calculate_urgency_and_impact(texto)
            session.intentos_diagnostico = 1
            session.estado = EstadoTicket.DIAGNOSTICO

            cls.add_history(session_id, "user", texto)
            cls.add_history(session_id, "assistant", resp_text)

            return {
                "tipo": "DIAGNOSTICO",
                "mensaje": resp_text,
                "ticket_id": None,
                "sources": rag_res.get("sources"),
                "source": rag_res.get("source", "ollama_rag")
            }


# Instancia por defecto
router_logic = RouterLogic()
