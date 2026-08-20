"""
Lógica de Enrutamiento y Clasificación de Intenciones para UniMon (Universidad Simón Bolívar - Colombia).
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


# Tipologías de incidentes comunes en la Universidad Simón Bolívar (Sedes Barranquilla y Cúcuta)
UNISIMON_INCIDENT_CATEGORIES = {
    "HARDWARE_EQUIPOS": "Mantenimiento y Fallas de Cómputo (P-GT-01)",
    "SEGURIDAD_ANTIMALWARE": "Protección Antimalware y Seguridad (P-GT-07)",
    "REDES_CONECTIVIDAD": "Aseguramiento de Redes y Conectividad (P-GT-08)",
    "BACKUPS_DATOS": "Generación y Restauración de Backups (P-GT-10)",
    "SISTEMAS_KACTUS_SEVEN": "Incidencias ERP Kactus / Seven (P-GT-11 / P-GT-12)",
    "REQUERIMIENTOS_TI": "Gestión de Requerimientos y Recursos TI (P-GT-13)",
    "GENERAL": "Soporte Técnico y Gestión de TI Unisimon"
}

# Palabras clave asociadas a incidentes activos, fallas físicas/operativas y solicitudes de ticket
TICKET_TRIGGERS = [
    # Solicitudes explícitas
    r"crear ticket", r"abrir ticket", r"generar ticket", r"hacer un ticket", r"abrir un ticket",
    r"quiero un ticket", r"generar radicado", r"radicar caso", r"radicar ticket", r"solicito soporte",
    r"reportar una falla", r"reportar falla", r"reportar problema", r"ticket de soporte",
    # Fallas físicas u operativas
    r"no enciende", r"no prende", r"dañado", r"dañada", r"pantalla azul", r"pantalla rota",
    r"sin internet", r"no tengo internet", r"se cayó la red", r"sin red", r"bloqueado", r"bloqueada",
    r"no funciona", r"está caído", r"no da imagen", r"humo", r"quemado", r"apagado",
    r"no conecta", r"error 500", r"servidor caído", r"infección de virus", r"pantalla negra"
]

# Palabras o frases que denotan preguntas informativas o de procedimiento (fuerzan RAG si hay duda)
INFO_QUERY_TRIGGERS = [
    r"cómo", r"como", r"cuáles", r"cuales", r"cuándo", r"cuando", r"qué es", r"que es",
    r"procedimiento", r"requisito", r"requisitos", r"canales de atención", r"canales de soporte",
    r"cada cuánto", r"cada cuanto", r"política", r"politica", r"guía", r"guia", r"manual"
]

# Palabras clave de urgencia alta o crítica
CRITICAL_TRIGGERS = [
    r"urgente", r"emergencia", r"auditorio", r"laboratorio completo", r"toda la sede",
    r"servidor principal", r"caída general", r"nómina", r"bloqueo total"
]

# Palabras clave de urgencia media
MEDIUM_TRIGGERS = [
    r"clase", r"docente", r"profesor", r"departamento", r"oficina", r"no puedo trabajar",
    r"requiero hoy", r"lento"
]


class RouterLogic:
    """
    Motor de análisis de texto e intenciones para el flujo de atención de UniMon.
    """

    @classmethod
    def classify_intent(cls, message: str) -> IntentType:
        """
        Clasifica semánticamente el mensaje del usuario entre CREATE_TICKET o RAG_QUERY.
        - CREATE_TICKET: Peticiones explícitas de apertura de ticket o reportes de fallas físicas/operativas.
        - RAG_QUERY: Preguntas informativas, procedimentales, canales de soporte o normativas.
        """
        msg_lower = message.strip().lower()

        # Si el usuario explícitamente pide ticket o describe una falla concreta
        for pattern in TICKET_TRIGGERS:
            if re.search(pattern, msg_lower):
                # Verificar si es una pregunta puramente teórica sobre cómo abrir tickets
                if any(re.search(info_pat, msg_lower) for info_pat in [r"cómo radicar", r"cómo abrir ticket", r"cuál es el proceso"]):
                    return IntentType.RAG_QUERY
                return IntentType.CREATE_TICKET

        return IntentType.RAG_QUERY

    @classmethod
    def categorize_usb_incident(cls, message: str) -> Tuple[str, str]:
        """
        Identifica la categoría institucional de Unisimon y retorna (código_categoría, nombre_legible).
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
        elif any(w in msg_lower for w in ["computador", "pc", "laptop", "monitor", "teclado", "mouse", "enciende", "pantalla", "laboratorio", "sala"]):
            return ("HARDWARE_EQUIPOS", UNISIMON_INCIDENT_CATEGORIES["HARDWARE_EQUIPOS"])
        elif any(w in msg_lower for w in ["licencia", "software", "instalación", "instalacion", "recurso", "requerimiento"]):
            return ("REQUERIMIENTOS_TI", UNISIMON_INCIDENT_CATEGORIES["REQUERIMIENTOS_TI"])
        else:
            return ("GENERAL", UNISIMON_INCIDENT_CATEGORIES["GENERAL"])

    @classmethod
    def calculate_urgency_and_impact(cls, message: str) -> Tuple[int, int]:
        """
        Calcula la urgencia (1-5) e impacto (1-5) según el contexto del mensaje.
        1: Muy baja, 2: Baja, 3: Mediana, 4: Alta, 5: Muy alta (Crítica).
        """
        msg_lower = message.lower()

        urgency = 3  # Valor institucional por defecto (Mediana)
        impact = 3

        # Evaluación de urgencia crítica
        if any(re.search(pat, msg_lower) for pat in CRITICAL_TRIGGERS):
            urgency = 5
            impact = 4
        # Evaluación de urgencia media-alta
        elif any(re.search(pat, msg_lower) for pat in MEDIUM_TRIGGERS):
            urgency = 4
            impact = 3
        # Consultas de baja urgencia / informativas
        elif any(w in msg_lower for w in ["duda", "pregunta", "consulta", "cuando", "cómo", "información"]):
            urgency = 2
            impact = 2

        return urgency, impact

    @classmethod
    def analyze_message(cls, message: str) -> Dict[str, Any]:
        """
        Realiza un análisis semántico completo del mensaje del usuario.
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

