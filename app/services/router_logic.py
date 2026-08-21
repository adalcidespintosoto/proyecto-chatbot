"""
Lógica de Enrutamiento, Clasificación de Intenciones y Chatbot Proactivo de Nivel 1 para UniMon.
Maneja el ciclo de diagnóstico de Nivel 1 y radicación por Slot-Filling dinámico en GLPI por sesión.
Distingue automáticamente entre solicitudes de SOFTWARE (solo Nombre y Correo) y HARDWARE (Nombre, Correo, Ubicación y Placa).
"""

import logging
import re
from typing import Dict, Any, Tuple, Optional
from enum import Enum
from pydantic import BaseModel, Field

from app.services.rag_service import rag_service, is_out_of_domain_response
from app.services.glpi_service import glpi_client, is_valid_email

logger = logging.getLogger("unimon.router_logic")


class EstadoTicket(str, Enum):
    IDLE = "IDLE"
    DIAGNOSTICO = "DIAGNOSTICO"
    PIDIENDO_NOMBRE = "PIDIENDO_NOMBRE"
    PIDIENDO_CORREO = "PIDIENDO_CORREO"
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
    intentos_diagnostico: int = 0  # Control de la Regla de 1 Descarte (Fail-Fast)
    falla: Optional[str] = None
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

# Respuestas positivas que confirman que el diagnóstico de Nivel 1 funcionó
SOLVED_PATTERNS = [
    r"\b(gracias|grasias|gracia|ya funcion[oó]|ya funsion[oó]|listo|se solucion[oó]|se solusion[oó]|qued[oó] bien|sirvi[oó]|cirvi[oó]|excelente|perfecto|resuelto|ya qued[oó]|muchas gracias|se arregl[oó]|ya sirve|ya prendi[oó]|ya conect[oó]|ya dio video)\b"
]

# Solicitud directa y explícita de técnico / radicación humana (aplica en IDLE y DIAGNOSTICO)
DIRECT_TECH_PATTERNS = [
    r"\b(crear ticket|abrir ticket|radicar( caso)?|necesito (a alguien|un t[eé]cnico|ayuda presencial|soporte presencial)|que (lo|la|los|las|el equipo) revisen|que venga un t[eé]cnico|que venga alguien|manda(r)? un t[eé]cnico|manda(r)? a alguien|alguien para que (lo|la) arregle|visita t[eé]cnica|t[eé]cnico presencial|soporte presencial|revisi[oó]n t[eé]cnica)\b"
]

# Respuestas en medio de diagnóstico que indican que la solución previa no funcionó o persiste la falla
PERSIST_PATTERNS = [
    r"\b(no sirvi[oó]|no sirbi[oó]|no cirvi[oó]|sigue igual|sige igual|no funcion[oó]|no funsion[oó]|sigue fallando|sige fallando|sigue bloquead[oa]|sigue el error|sigue sin funcionar|sigue sin servir|persiste|continua|contin[uú]a|sigue el problema|no se solucion[oó]|no se solusion[oó]|no se arregl[oó]|tampoco funcion[oó]|escalar)\b",
    r"\b(no me deja (entrar|ingresar|acceder|iniciar)|no pude (entrar|ingresar|acceder|iniciar)|no me funciona|no puedo solucionarlo|no pude solucionarlo)\b",
    r"^(no|nada|tampoco|sigue ca[ií]do)$"
]

# Expresiones afirmativas y de continuación ("sí", "claro", "dale", "ok", "por favor", "muéstramelos")
CONTINUATION_PATTERNS = [
    r"^(s[ií]|ok|dale|claro|por favor|porfa|mu[eé]strame|mu[eé]stramelo[s]?|mu[eé]stramela[s]?|adelante|de acuerdo|s[ií] por favor|s[ií] claro|s[ií] dale|s[ií] expl[ií]camelo|expl[ií]came|s[ií] porfa|dime|cu[eé]ntame|procede|ay[uú]dame con eso)\b"
]

# Palabras clave para identificar trámites de SOFTWARE / Cuentas / Accesos (con tolerancia tipográfica)
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


class RouterLogic:
    """
    Motor de análisis conversacional de Nivel 1 y orquestación dinámica de tickets.
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
    def is_solved_confirmation(cls, text: str) -> bool:
        """Detecta si el usuario indica que la sugerencia resolvió el problema."""
        msg_clean = text.strip().lower()
        if any(neg in msg_clean for neg in ["no funcion", "no sirv", "no se", "sigue", "no me deja"]):
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
        msg_clean = text.strip().lower()
        return any(re.search(pat, msg_clean) for pat in PERSIST_PATTERNS) or cls.is_direct_tech_request(text)

    @classmethod
    def is_continuation_affirmation(cls, text: str) -> bool:
        """Detecta si el usuario envía una afirmación corta o solicitud de continuar explicando."""
        msg_clean = re.sub(r"[^\w\s\?¿áéíóúÁÉÍÓÚñÑ]", "", text.strip().lower())
        words = msg_clean.split()
        if len(words) <= 5:
            return any(re.search(pat, msg_clean) for pat in CONTINUATION_PATTERNS)
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
        """Extrae heurísticamente el nombre completo del solicitante."""
        cleaned = text
        if email:
            cleaned = cleaned.replace(email, "")

        name_patterns = [
            r"(?:mi nombre es|me llamo|soy|nombre:)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]{2,}(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ]{2,})+)",
            r"^([A-Za-zÁÉÍÓÚáéíóúñÑ]{2,}(?:\s+[A-Za-zÁÉÍÓÚáéíóúñÑ]{2,})+)"
        ]

        for pat in name_patterns:
            m = re.search(pat, cleaned, re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                if not any(w in cand.lower() for w in ["un ticket", "soporte", "la falla", "el problema", "hola", "buenos dias"]):
                    return cand

        words = [w for w in cleaned.strip().split() if w.isalpha()]
        if 2 <= len(words) <= 4:
            cand = " ".join(words)
            if not any(w in cand.lower() for w in ["ticket", "falla", "problema", "soporte", "hola"]):
                return cand

        return None

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
    async def _radicar_ticket_en_glpi(cls, session_id: str, session: TicketSession) -> Dict[str, Any]:
        """
        Genera el ticket en GLPI según la categoría (SOFTWARE o HARDWARE) y limpia la sesión.
        """
        falla_desc = session.falla or "Requerimiento de soporte reportado por el usuario"
        nombre_sol = session.nombre or "Usuario Unisimon"
        correo_sol = session.correo or "solicitudcomputo@unisimon.edu.co"

        if session.categoria == CategoriaSolicitud.SOFTWARE:
            session.ubicacion = "Plataforma Digital / Remoto"
            session.activo = "N/A"
            asunto_ticket = f"[Soporte Software USB] {falla_desc[:50]}"
            contenido_ticket = (
                f"<b>REPORTE DE INCIDENTE TÉCNICO - MESA DE AYUDA UNISIMON (SOFTWARE / ACCESOS)</b><br><br>"
                f"<b>Solicitante:</b> {nombre_sol}<br>"
                f"<b>Correo Electrónico:</b> {correo_sol}<br>"
                f"<b>Tipo de Trámite:</b> Soporte de Software, Cuentas o Plataformas Digitales<br>"
                f"<b>Ubicación:</b> {session.ubicacion}<br>"
                f"<b>Placa / Activo:</b> {session.activo}<br>"
                f"<b>Nivel de Urgencia:</b> {session.urgency}/5<br><br>"
                f"<b>Descripción del Requerimiento:</b><br>{falla_desc}<br><br>"
                f"<i>Caso escalado y radicado tras descarte de Nivel 1 en UniMon Chatbot.</i>"
            )
            confirmacion_msg = (
                f"✅ Se ha radicado exitosamente tu solicitud de soporte técnico con el radicado **#{'{ticket_id}'}**. "
                f"Un técnico de la Dirección de TI revisará tu caso y se pondrá en contacto a través de tu correo institucional (**{correo_sol}**)."
            )
        else:
            ubicacion_sol = session.ubicacion or "Sede Unisimon"
            activo_sol = session.activo or "N/A"
            asunto_ticket = f"[Soporte TI Unisimon] {falla_desc[:45]} - {ubicacion_sol}"
            contenido_ticket = (
                f"<b>REPORTE DE INCIDENTE TÉCNICO - MESA DE AYUDA UNISIMON</b><br><br>"
                f"<b>Solicitante:</b> {nombre_sol}<br>"
                f"<b>Correo Electrónico:</b> {correo_sol}<br>"
                f"<b>Ubicación:</b> {ubicacion_sol}<br>"
                f"<b>Placa / Activo:</b> {activo_sol}<br>"
                f"<b>Nivel de Urgencia:</b> {session.urgency}/5<br><br>"
                f"<b>Descripción de la Falla Técnica:</b><br>{falla_desc}<br><br>"
                f"<i>Caso escalado y radicado tras descarte de Nivel 1 en UniMon Chatbot.</i>"
            )
            confirmacion_msg = (
                f"✅ Se ha radicado exitosamente tu solicitud de soporte técnico con el radicado **#{'{ticket_id}'}**. "
                f"Un técnico de la Dirección de TI revisará tu caso en **{ubicacion_sol}** y se pondrá en contacto a través de tu correo institucional (**{correo_sol}**)."
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
            category_name = session.category_name
            cls.reset_session(session_id)

            reply_final = confirmacion_msg.replace("{ticket_id}", str(ticket_id))

            return {
                "tipo": "TICKET_CREADO",
                "mensaje": reply_final,
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
                "mensaje": f"Ocurrió un inconveniente al radicar el ticket en GLPI ({exc}). Por favor contacta a solicitudcomputo@unisimon.edu.co.",
                "ticket_id": None,
                "source": "GLPI_ERROR"
            }

    @classmethod
    async def procesar_mensaje(cls, mensaje: str, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Procesa el mensaje del usuario de acuerdo a la máquina de estados conversacional de Nivel 1.
        Aplica Slot-Filling dinámico: solo Nombre y Correo para SOFTWARE; Nombre, Correo, Ubicación y Placa para HARDWARE.
        """
        texto = mensaje.strip()
        session = cls.get_session(session_id)
        estado_actual = session.estado

        logger.info(f"[Session: {session_id}] Estado actual: {estado_actual} | Categoría: {session.categoria} | Mensaje: '{texto[:50]}'")

        # -------------------------------------------------------------
        # ESTADO 1: PIDIENDO_ACTIVO (Último slot para HARDWARE)
        # -------------------------------------------------------------
        if estado_actual == EstadoTicket.PIDIENDO_ACTIVO:
            activo_resp = texto
            session.activo = activo_resp if activo_resp.lower() not in ["na", "n/a", "no", "ninguno", "ninguna", "no tiene"] else "N/A"
            return await cls._radicar_ticket_en_glpi(session_id, session)

        # -------------------------------------------------------------
        # ESTADO 2: PIDIENDO_UBICACION (Solo para HARDWARE)
        # -------------------------------------------------------------
        elif estado_actual == EstadoTicket.PIDIENDO_UBICACION:
            session.ubicacion = texto
            session.estado = EstadoTicket.PIDIENDO_ACTIVO
            return {
                "tipo": "RADICANDO_TICKET",
                "mensaje": "Por favor indícame el **número de activo o placa del equipo institucional** (si no aplica o no la conoces, puedes responder **N/A**):",
                "ticket_id": None,
                "source": "UniMon_SlotFilling"
            }

        # -------------------------------------------------------------
        # ESTADO 3: PIDIENDO_CORREO (Slot 2)
        # -------------------------------------------------------------
        elif estado_actual == EstadoTicket.PIDIENDO_CORREO:
            ext_email = cls.extract_email(texto)
            if ext_email and is_valid_email(ext_email):
                session.correo = ext_email

                # Si es trámite de SOFTWARE -> Radicación inmediata sin pedir ubicación ni placa
                if session.categoria == CategoriaSolicitud.SOFTWARE:
                    return await cls._radicar_ticket_en_glpi(session_id, session)

                # Si es HARDWARE -> Continuar pidiendo ubicación
                session.estado = EstadoTicket.PIDIENDO_UBICACION
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": "Entendido. Ahora por favor indícame tu **ubicación exacta** donde se presenta la falla (Sede, Bloque, Piso, Laboratorio o Sala):",
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
                }
            else:
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": "El correo ingresado no parece ser válido. Por favor ingresa un correo electrónico institucional o de contacto válido (ej: usuario@unisimon.edu.co):",
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
                }

        # -------------------------------------------------------------
        # ESTADO 4: PIDIENDO_NOMBRE (Slot 1)
        # -------------------------------------------------------------
        elif estado_actual == EstadoTicket.PIDIENDO_NOMBRE:
            ext_email = cls.extract_email(texto)
            ext_name = cls.extract_name(texto, ext_email)

            session.nombre = ext_name if ext_name else texto.strip()

            if ext_email and is_valid_email(ext_email):
                session.correo = ext_email
                # Si es SOFTWARE y ya tenemos correo -> Radicar de inmediato
                if session.categoria == CategoriaSolicitud.SOFTWARE:
                    return await cls._radicar_ticket_en_glpi(session_id, session)

                # Si es HARDWARE -> Pasar a ubicación
                session.estado = EstadoTicket.PIDIENDO_UBICACION
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": f"Gracias, **{session.nombre}**. Ahora por favor indícame tu **ubicación exacta** donde se presenta la falla (Sede, Bloque, Piso, Laboratorio o Sala):",
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
                }
            else:
                session.estado = EstadoTicket.PIDIENDO_CORREO
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": f"Gracias, **{session.nombre}**. Ahora por favor indícame tu **correo electrónico institucional** (ej: usuario@unisimon.edu.co):",
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
                }

        # -------------------------------------------------------------
        # ESTADO 5: DIAGNOSTICO (Evaluación de descarte de Nivel 1)
        # -------------------------------------------------------------
        # -------------------------------------------------------------
        # ESTADO 5: DIAGNOSTICO (Evaluación de descarte de Nivel 1)
        # -------------------------------------------------------------
        # -------------------------------------------------------------
        # ESTADO 5: DIAGNOSTICO (Evaluación de descarte de Nivel 1)
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

            # Caso B: El usuario confirma que funcionó
            elif cls.is_solved_confirmation(texto):
                cls.reset_session(session_id)
                solved_reply = (
                    "¡Excelente! Me alegra saber que pudiste resolver el inconveniente con estos pasos iniciales. "
                    "Quedo a tu disposición si requieres apoyo con algún otro procedimiento o servicio institucional de TI en la Universidad Simón Bolívar. ¡Que tengas un excelente día!"
                )
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", solved_reply)
                return {
                    "tipo": "SOLUCIONADO",
                    "mensaje": solved_reply,
                    "ticket_id": None,
                    "source": "UniMon_Nivel1_Resolved"
                }

            # Caso C: Afirmación corta o confirmación de continuar ("sí", "claro", "dale", "ok", "por favor", "muéstramelos")
            elif cls.is_continuation_affirmation(texto) and session.intentos_diagnostico <= 1:
                session.intentos_diagnostico += 1
                history = cls.get_history(session_id)
                last_assistant_msg = ""
                for m in reversed(history):
                    if m.get("role") == "assistant":
                        last_assistant_msg = m.get("content", "")
                        break

                falla_contexto = session.falla or last_assistant_msg or "procedimiento y soporte institucional Unisimon"
                query_contextualizada = (
                    f"El usuario responde afirmativamente ('{texto}') y solicita los pasos detallados o la explicación para: {falla_contexto}"
                )

                rag_res = await rag_service.consultar(
                    pregunta=query_contextualizada,
                    chat_history=history,
                    es_diagnostico=False
                )
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

            # Caso D: Regla de 1 Descarte (Fail-Fast)
            # Si el usuario indica que persiste, pide técnico, o envía cualquier duda tras el descarte inicial -> Radicación inmediata
            else:
                history = cls.get_history(session_id)
                rag_res = await rag_service.consultar(
                    pregunta=texto,
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

                # Radicación directa sin bucles repetitivos
                session.estado = EstadoTicket.PIDIENDO_NOMBRE
                prompt_msg = (
                    "Con gusto puedo ayudarte a radicar el caso con el equipo de soporte técnico. Para iniciar, por favor indícame tu **nombre completo**:"
                )
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", prompt_msg)
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": prompt_msg,
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
                }

        # -------------------------------------------------------------
        # ESTADO 6: IDLE (Mensaje Inicial)
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

            # 2. Solicitud directa de técnico / radicación en mensaje inicial
            if cls.is_direct_tech_request(texto):
                session.falla = texto
                cat, cat_name = cls.detect_category(texto)
                session.categoria = cat
                session.category_name = cat_name
                session.urgency, session.impact = cls.calculate_urgency_and_impact(texto)
                session.estado = EstadoTicket.PIDIENDO_NOMBRE
                prompt_msg = (
                    "Con gusto puedo ayudarte a radicar el caso con el equipo de soporte técnico. Para iniciar, por favor indícame tu **nombre completo**:"
                )
                cls.add_history(session_id, "user", texto)
                cls.add_history(session_id, "assistant", prompt_msg)
                return {
                    "tipo": "RADICANDO_TICKET",
                    "mensaje": prompt_msg,
                    "ticket_id": None,
                    "source": "UniMon_SlotFilling"
                }

            # 3. Consultar RAG con historial conversacional
            history = cls.get_history(session_id)
            rag_res = await rag_service.consultar(
                pregunta=texto,
                chat_history=history,
                es_diagnostico=False
            )
            resp_text = rag_res.get("response", "")

            # 4. Guardrail Fuera de Dominio (Out-of-Domain)
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

            # 5. Caso dentro de dominio: Iniciar Diagnóstico de Nivel 1 (1 intento)
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



