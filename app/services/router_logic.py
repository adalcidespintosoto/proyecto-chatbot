"""
Lógica de Enrutamiento y Clasificación de Intenciones para UniMon (USB).
Determina si la consulta del usuario requiere apertura de Ticket en GLPI (CREATE_TICKET)
o si debe ser respondida informativamente mediante la base de conocimientos RAG (RAG_QUERY).
Calcula la urgencia y tipología institucional de la falla.
"""

import re
from typing import Dict, Any, Tuple
from enum import Enum


class IntentType(str, Enum):
    CREATE_TICKET = "CREATE_TICKET"
    RAG_QUERY = "RAG_QUERY"


# Tipologías de incidentes comunes en la Universidad Simón Bolívar (USB)
USB_INCIDENT_CATEGORIES = {
    "CAMPUS_VIRTUAL": "Campus Virtual / Moodle USB",
    "WIFI_RED": "Red WiFi USB / Eduroam / Conectividad",
    "CORREO_INSTITUCIONAL": "Correo Institucional (@usb.ve / Google Workspace)",
    "CREDENCIALES": "Cuentas USB / Recuperación de Contraseñas / DTI",
    "HARDWARE_LABORATORIO": "Equipos de Computación / Laboratorios USB",
    "GENERAL": "Soporte Técnico General USB"
}

# Palabras clave asociadas a incidentes activos que ameritan ticket
TICKET_TRIGGERS = [
    r"no funciona", r"se cayó", r"crear ticket", r"abrir ticket", r"generar ticket",
    r"reportar falla", r"reportar problema", r"está caído", r"no tengo acceso",
    r"bloqueada", r"bloqueado", r"error 500", r"error 404", r"pantalla rota",
    r"dañado", r"dañada", r"no enciende", r"sin internet", r"no conecta",
    r"urgente", r"falla crítica", r"ticket de soporte", r"solicito soporte",
    r"no puedo ingresar", r"clave inválida", r"servidor caído"
]

# Palabras clave de urgencia alta o crítica
CRITICAL_TRIGGERS = [
    r"examen", r"evaluación", r"parcial", r"entrega final", r"urgente",
    r"emergencia", r"auditorio", r"laboratorio completo", r"toda la sede",
    r"inscripción", r"acto de grado"
]

# Palabras clave de urgencia media
MEDIUM_TRIGGERS = [
    r"clase", r"profesor", r"departamento", r"oficina", r"no puedo enviar",
    r"requiero hoy", r"lento"
]


class RouterLogic:
    """
    Motor de análisis de texto e intenciones para el flujo de atención de UniMon.
    """

    @classmethod
    def classify_intent(cls, message: str) -> IntentType:
        """
        Clasifica el mensaje del usuario entre CREATE_TICKET o RAG_QUERY.
        """
        msg_lower = message.lower()

        # Si coincide con disparadores explícitos de reporte o falla
        for pattern in TICKET_TRIGGERS:
            if re.search(pattern, msg_lower):
                return IntentType.CREATE_TICKET

        return IntentType.RAG_QUERY

    @classmethod
    def categorize_usb_incident(cls, message: str) -> Tuple[str, str]:
        """
        Identifica la categoría institucional USB y retorna (código_categoría, nombre_legible).
        """
        msg_lower = message.lower()

        if any(w in msg_lower for w in ["campus", "moodle", "aula virtual", "entrega", "tarea"]):
            return ("CAMPUS_VIRTUAL", USB_INCIDENT_CATEGORIES["CAMPUS_VIRTUAL"])
        elif any(w in msg_lower for w in ["wifi", "wi-fi", "eduroam", "red", "inalámbrica", "conexión", "ethernet"]):
            return ("WIFI_RED", USB_INCIDENT_CATEGORIES["WIFI_RED"])
        elif any(w in msg_lower for w in ["correo", "email", "gmail", "@usb.ve", "bandeja"]):
            return ("CORREO_INSTITUCIONAL", USB_INCIDENT_CATEGORIES["CORREO_INSTITUCIONAL"])
        elif any(w in msg_lower for w in ["clave", "contraseña", "usuario", "dti", "dst", "acceso", "login"]):
            return ("CREDENCIALES", USB_INCIDENT_CATEGORIES["CREDENCIALES"])
        elif any(w in msg_lower for w in ["computador", "pc", "monitor", "teclado", "laboratorio", "sala", "proyector"]):
            return ("HARDWARE_LABORATORIO", USB_INCIDENT_CATEGORIES["HARDWARE_LABORATORIO"])
        else:
            return ("GENERAL", USB_INCIDENT_CATEGORIES["GENERAL"])

    @classmethod
    def calculate_urgency_and_impact(cls, message: str) -> Tuple[int, int]:
        """
        Calcula la urgencia (1-5) e impacto (1-5) según el contexto del mensaje.
        1: Muy baja, 2: Baja, 3: Mediana, 4: Alta, 5: Muy alta (Crítica).
        """
        msg_lower = message.lower()

        urgency = 3  # Valor por defecto institucional (Mediana)
        impact = 3

        # Evaluación de urgencia crítica
        if any(re.search(pat, msg_lower) for pat in CRITICAL_TRIGGERS):
            urgency = 5
            impact = 4
        # Evaluación de urgencia media-alta
        elif any(re.search(pat, msg_lower) for pat in MEDIUM_TRIGGERS):
            urgency = 4
            impact = 3
        # Consultas de baja urgencia
        elif any(w in msg_lower for w in ["duda", "pregunta", "consulta", "cuando", "cómo"]):
            urgency = 2
            impact = 2

        return urgency, impact

    @classmethod
    def analyze_message(cls, message: str) -> Dict[str, Any]:
        """
        Realiza un análisis completo del mensaje del usuario.
        """
        intent = cls.classify_intent(message)
        category_code, category_name = cls.categorize_usb_incident(message)
        urgency, impact = cls.calculate_urgency_and_impact(message)

        return {
            "intent": intent,
            "category_code": category_code,
            "category_name": category_name,
            "urgency": urgency,
            "impact": impact
        }
