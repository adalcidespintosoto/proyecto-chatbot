"""
Lógica de Enrutamiento, Clasificación de Intenciones y Máquina de Estados Conversacional para UniMon.
Gestiona el ciclo de recolección de datos por sesión para tickets de GLPI y consultas RAG.
"""

import re
from typing import Dict, Any, Tuple, Optional
from enum import Enum
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    GREETING = "GREETING"
    CREATE_TICKET = "CREATE_TICKET"
    RAG_QUERY = "RAG_QUERY"


class ConversationState(str, Enum):
    IDLE = "IDLE"
    AWAITING_DESCRIPTION = "AWAITING_DESCRIPTION"
    AWAITING_CONTACT_INFO = "AWAITING_CONTACT_INFO"


# Tipologías de incidentes comunes en la Universidad Simón Bolívar
UNISIMON_INCIDENT_CATEGORIES = {
    "HARDWARE_EQUIPOS": "Mantenimiento y Fallas de Cómputo (P-GT-01)",
    "SEGURIDAD_ANTIMALWARE": "Protección Antimalware y Seguridad (P-GT-07)",
    "REDES_CONECTIVIDAD": "Aseguramiento de Redes y Conectividad (P-GT-08)",
    "BACKUPS_DATOS": "Generación y Restauración de Backups (P-GT-10)",
    "SISTEMAS_KACTUS_SEVEN": "Incidencias ERP Kactus / Seven (P-GT-11 / P-GT-12)",
    "REQUERIMIENTOS_TI": "Gestión de Requerimientos y Recursos TI (P-GT-13)",
    "GENERAL": "Soporte Técnico y Gestión de TI Unisimon"
}

# Saludos o aperturas de conversación de cortesía
GREETING_PATTERNS = [
    r"^hola\b", r"^buenos d[ií]as\b", r"^buenas tardes\b", r"^buenas noches\b",
    r"^buenas\b", r"^hey\b", r"^saludos\b", r"^[¿?]?c[oó]mo est[aá]s\b",
    r"^[¿?]?qu[eé] tal\b", r"^buen d[ií]a\b", r"^hi\b", r"^hello\b"
]

# Disparadores de ticket: peticiones explícitas o descripción de fallas físicas/operativas
TICKET_TRIGGERS = [
    # Solicitudes explícitas
    r"crear ticket", r"abrir ticket", r"generar ticket", r"hacer un ticket", r"abrir un ticket",
    r"quiero un ticket", r"generar radicado", r"radicar caso", r"radicar ticket", r"solicito soporte",
    r"reportar una falla", r"reportar falla", r"reportar problema", r"ticket de soporte",
    r"necesito un ticket", r"crear un caso", r"abrir un caso", r"radicar un caso", r"ayuda soporte",
    # Fallas físicas u operativas
    r"no enciende", r"no prende", r"dañado", r"dañada", r"pantalla azul", r"pantalla rota",
    r"sin internet", r"no tengo internet", r"se cayó la red", r"sin red", r"bloqueado", r"bloqueada",
    r"no funciona", r"está caído", r"no da imagen", r"humo", r"quemado", r"apagado",
    r"no conecta", r"error 500", r"servidor caído", r"infección de virus", r"pantalla negra",
    r"se dañó", r"está roto", r"no sirve", r"falla en", r"problema con el equipo", r"computador dañado"
]

# Frases explícitamente informativas/teóricas que no deben abrir ticket
INFO_QUERY_EXCLUSIONS = [
    r"cómo radicar", r"como radicar", r"cómo abrir ticket", r"como abrir ticket",
    r"cuál es el proceso", r"cual es el proceso", r"cómo crear un ticket", r"como crear un ticket",
    r"cuáles son los canales", r"cuales son los canales", r"horario de atención"
]

# Regex estándar para extracción y validación de correo electrónico
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# Disparadores de urgencia crítica
CRITICAL_TRIGGERS = [
    r"urgente", r"emergencia", r"auditorio", r"laboratorio completo", r"toda la sede",
    r"servidor principal", r"caída general", r"nómina", r"bloqueo total"
]

# Disparadores de urgencia media
MEDIUM_TRIGGERS = [
    r"clase", r"docente", r"profesor", r"departamento", r"oficina", r"no puedo trabajar",
    r"requiero hoy", r"lento"
]


class SessionData(BaseModel):
    """
    Estructura de memoria conversacional por sesión.
    """
    state: ConversationState = ConversationState.IDLE
    description: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    category_name: Optional[str] = None
    urgency: int = 3
    impact: int = 3


# Almacén en memoria indexado por session_id
_SESSION_STORE: Dict[str, SessionData] = {}


class RouterLogic:
    """
    Motor de análisis de texto, máquina de estados y enrutamiento de UniMon.
    """

    @classmethod
    def get_session(cls, session_id: str) -> SessionData:
        """Obtiene o inicializa la sesión en memoria."""
        if session_id not in _SESSION_STORE:
            _SESSION_STORE[session_id] = SessionData()
        return _SESSION_STORE[session_id]

    @classmethod
    def reset_session(cls, session_id: str) -> None:
        """Reinicia el estado de la sesión a IDLE y borra datos recolectados."""
        if session_id in _SESSION_STORE:
            _SESSION_STORE[session_id] = SessionData()

    @classmethod
    def extract_email(cls, text: str) -> Optional[str]:
        """Extrae el primer correo electrónico válido encontrado en el texto."""
        match = EMAIL_REGEX.search(text)
        if match:
            return match.group(0).strip().lower()
        return None

    @classmethod
    def extract_name(cls, text: str, email: Optional[str] = None) -> Optional[str]:
        """
        Extrae heurísticamente el nombre del usuario a partir del texto.
        """
        cleaned = text
        if email:
            cleaned = cleaned.replace(email, "")

        # Patrones comunes: "Soy Juan Perez", "Mi nombre es Juan Perez", "Me llamo Juan Perez"
        name_patterns = [
            r"(?:mi nombre es|me llamo|soy|nombre:)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]{2,}(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ]{2,})+)",
            r"^([A-Za-zÁÉÍÓÚáéíóúñÑ]{2,}(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ]{2,})+)"
        ]

        for pat in name_patterns:
            m = re.search(pat, cleaned, re.IGNORECASE)
            if m:
                extracted = m.group(1).strip()
                # Filtrar si coincide con palabras comunes que no son nombres
                if not any(w in extracted.lower() for w in ["un ticket", "soporte", "la falla", "el problema", "hola", "buenos dias", "buenas tardes"]):
                    return extracted

        # Si el texto es corto y parece ser solo un nombre de 2 o 3 palabras
        words = [w for w in cleaned.strip().split() if w.isalpha()]
        if 2 <= len(words) <= 4:
            candidate = " ".join(words)
            if not any(w in candidate.lower() for w in ["ticket", "falla", "problema", "soporte", "hola", "buenos"]):
                return candidate

        return None

    @classmethod
    def is_greeting(cls, message: str) -> bool:
        """
        Verifica si el mensaje es únicamente un saludo o apertura de cortesía sin contenido técnico.
        """
        msg_clean = re.sub(r"[^\w\s\?¿]", "", message.strip().lower())
        # Si tiene pocas palabras y coincide con saludo
        words = msg_clean.split()
        if len(words) <= 5:
            return any(re.search(pat, msg_clean) for pat in GREETING_PATTERNS)
        return False

    @classmethod
    def classify_intent(cls, message: str) -> IntentType:
        """
        Clasifica semánticamente el mensaje del usuario:
        - GREETING: Saludos de cortesía simples ("hola", "buenos días", etc.).
        - RAG_QUERY: Preguntas sobre procedimientos, reglamentos, manuales o canales.
        - CREATE_TICKET: Reportes de fallas técnicas o peticiones explícitas de soporte/ticket.
        """
        msg_lower = message.strip().lower()

        # 1. Saludo simple
        if cls.is_greeting(message):
            return IntentType.GREETING

        # 2. Consultas procedimentales teóricas
        if any(re.search(info_pat, msg_lower) for info_pat in INFO_QUERY_EXCLUSIONS):
            return IntentType.RAG_QUERY

        # 3. Disparadores de ticket o fallas operativas
        for pattern in TICKET_TRIGGERS:
            if re.search(pattern, msg_lower):
                return IntentType.CREATE_TICKET

        return IntentType.RAG_QUERY


    @classmethod
    def generate_ticket_title(cls, description: str) -> str:
        """
        Genera automáticamente el título conciso del ticket:
        `[Soporte Técnico USB] Reporte: {description[:60]}...`
        """
        clean_desc = description.strip().replace("\n", " ")
        if len(clean_desc) > 60:
            return f"[Soporte Técnico USB] Reporte: {clean_desc[:60]}..."
        return f"[Soporte Técnico USB] Reporte: {clean_desc}"

    @classmethod
    def categorize_usb_incident(cls, message: str) -> Tuple[str, str]:
        """
        Identifica la categoría institucional y retorna (código_categoría, nombre_legible).
        """
        msg_lower = message.lower()

        if any(w in msg_lower for w in ["kactus", "seven", "erp", "módulo", "modulo", "nómina", "nomina"]):
            return ("SISTEMAS_KACTUS_SEVEN", UNISIMON_INCIDENT_CATEGORIES["SISTEMAS_KACTUS_SEVEN"])
        elif any(w in msg_lower for w in ["wifi", "wi-fi", "red", "inalámbrica", "inalambrica", "conexión", "conexion", "ethernet", "cable", "switch"]):
            return ("REDES_CONECTIVIDAD", UNISIMON_INCIDENT_CATEGORIES["REDES_CONECTIVIDAD"])
        elif any(w in msg_lower for w in ["virus", "malware", "troyano", "antivirus", "infección", "infeccion", "seguridad"]):
            return ("SEGURIDAD_ANTIMALWARE", UNISIMON_INCIDENT_CATEGORIES["SEGURIDAD_ANTIMALWARE"])
        elif any(w in msg_lower for w in ["backup", "copia", "respaldo", "restaurar", "restauración"]):
            return ("BACKUPS_DATOS", UNISIMON_INCIDENT_CATEGORIES["BACKUPS_DATOS"])
        elif any(w in msg_lower for w in ["computador", "pc", "laptop", "monitor", "teclado", "mouse", "enciende", "pantalla", "laboratorio", "sala", "proyector"]):
            return ("HARDWARE_EQUIPOS", UNISIMON_INCIDENT_CATEGORIES["HARDWARE_EQUIPOS"])
        elif any(w in msg_lower for w in ["licencia", "software", "instalación", "instalacion", "recurso", "requerimiento"]):
            return ("REQUERIMIENTOS_TI", UNISIMON_INCIDENT_CATEGORIES["REQUERIMIENTOS_TI"])
        else:
            return ("GENERAL", UNISIMON_INCIDENT_CATEGORIES["GENERAL"])

    @classmethod
    def calculate_urgency_and_impact(cls, message: str) -> Tuple[int, int]:
        """
        Calcula la urgencia (1-5) e impacto (1-5) según el contexto del mensaje.
        """
        msg_lower = message.lower()

        urgency = 3
        impact = 3

        if any(re.search(pat, msg_lower) for pat in CRITICAL_TRIGGERS):
            urgency = 5
            impact = 4
        elif any(re.search(pat, msg_lower) for pat in MEDIUM_TRIGGERS):
            urgency = 4
            impact = 3
        elif any(w in msg_lower for w in ["duda", "pregunta", "consulta", "cuando", "cómo", "información"]):
            urgency = 2
            impact = 2

        return urgency, impact

    @classmethod
    def is_only_ticket_request_without_details(cls, message: str) -> bool:
        """
        Determina si el usuario solo dijo que quiere un ticket pero no describió la falla.
        Ej: "quiero abrir un ticket", "generar ticket", "reportar una falla", "necesito soporte".
        """
        msg_lower = message.strip().lower()
        # Si tiene menos de 40 caracteres y coincide con solicitudes genéricas
        generic_phrases = [
            "quiero hacer un ticket", "quiero un ticket", "abrir ticket", "crear ticket",
            "generar ticket", "hacer un ticket", "abrir un ticket", "reportar una falla",
            "reportar un problema", "necesito un ticket", "solicito soporte", "radicar caso",
            "radicar ticket", "quiero radicar un caso", "ayuda con soporte"
        ]
        return any(msg_lower == phrase or msg_lower == f"{phrase} por favor" for phrase in generic_phrases)


