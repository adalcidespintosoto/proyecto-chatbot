"""
Servicio de Clasificación de Intenciones y Feedback para UniMon.
Maneja la desambiguación de respuestas del usuario tras diagnósticos e instructivos (Nivel 1).
"""

import re
from typing import Optional, Dict, Any, Union

RESOLVED_INTENTS = [
    "resolved", "si", "sí", "si me sirvio", "sí me sirvió", "si me funciono", 
    "sí me funcionó", "gracias", "muchas gracias", "listo", "ya pude", 
    "ya quedo", "solucionado", "todo claro", "excelente"
]

TICKET_INTENTS = [
    "create_ticket", "no", "no me sirvio", "no me sirvió", "no me funciono", 
    "no me funcionó", "no funciona", "no pude", "radicar", "abrir ticket", 
    "crear ticket", "soporte"
]


def handle_feedback_transition(
    user_message: str, 
    current_state: str = "DIAGNOSTICO", 
    session: Optional[Union[dict, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Evalúa la respuesta del usuario tras recibir un instructivo/diagnóstico.
    
    1. Si el usuario confirma que la solución funcionó ("sí", "gracias", "RESOLVED"),
       transiciona al estado FINALIZADO con un mensaje cordial de cierre.
    2. Si el usuario indica que no funcionó o solicita ticket ("no", "CREATE_TICKET"),
       transiciona a RADICANDO_TICKET e inicia la captura del Nombre Completo.
    3. Si es una nueva consulta o pregunta técnica, retorna None para continuar el flujo RAG.
    """
    if session is None:
        session = {}

    msg = user_message.lower().strip()
    msg_clean = re.sub(r"[^\w\s\?¿áéíóúÁÉÍÓÚñÑ_]", " ", msg).strip()
    msg_clean = re.sub(r"\s+", " ", msg_clean)

    def _update_session(new_state: str):
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

    # 1. Caso resuelto satisfactoriamente
    is_resolved = any(
        msg == intent or msg.startswith(intent + " ") or msg.startswith(intent + ".") or msg.startswith(intent + "!") or
        msg_clean == intent or msg_clean.startswith(intent + " ")
        for intent in RESOLVED_INTENTS
    )
    if is_resolved:
        _update_session("FINALIZADO")
        return {
            "response": "¡Excelente! Me alegra haberte ayudado a resolverlo. Si necesitas soporte con otra plataforma o trámite institucional, aquí estaré. ¡Que tengas un excelente día! 👋",
            "mensaje": "¡Excelente! Me alegra haberte ayudado a resolverlo. Si necesitas soporte con otra plataforma o trámite institucional, aquí estaré. ¡Que tengas un excelente día! 👋",
            "state": "FINALIZADO",
            "tipo": "FINALIZADO",
            "source": "UniMon_Feedback_Success",
            "quick_replies": []
        }

    # 2. El usuario requiere escalado / no le sirvió
    is_ticket = any(
        msg == intent or msg.startswith(intent + " ") or msg.startswith(intent + ".") or msg.startswith(intent + "!") or
        msg_clean == intent or msg_clean.startswith(intent + " ")
        for intent in TICKET_INTENTS
    )
    if is_ticket:
        _update_session("RADICANDO_TICKET")
        return {
            "response": "Entendido. Vamos a radicar tu solicitud de soporte técnico en GLPI. Por favor, indícame tu **Nombre Completo**:",
            "mensaje": "Entendido. Vamos a radicar tu solicitud de soporte técnico en GLPI. Por favor, indícame tu **Nombre Completo**:",
            "state": "RADICANDO_TICKET",
            "tipo": "RADICANDO_TICKET",
            "source": "UniMon_SlotFilling",
            "quick_replies": []
        }

    # 3. Si el usuario realiza una nueva consulta o pregunta de seguimiento
    return None
