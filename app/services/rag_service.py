"""
Servicio RAG y Cliente LLM para Ollama con modelo llama3.1.
Provee respuestas asistidas con la base de conocimiento institucional
de la Universidad Simón Bolívar (USB), incluyendo DTI/DST, Campus Virtual, Redes WiFi y Cuentas.
"""

import logging
from typing import Dict, Any, Optional
import httpx
from app.config import get_settings

logger = logging.getLogger("unimon.rag_service")

# Base de conocimiento institucional de la Universidad Simón Bolívar (USB)
USB_KNOWLEDGE_BASE = """
[BASE DE CONOCIMIENTO INSTITUCIONAL - UNIVERSIDAD SIMÓN BOLÍVAR (USB)]

1. SERVICIOS DE TECNOLOGÍA E INFORMACIÓN (DTI / DST - Dirección de Servicios Telemáticos / Dirección de Tecnología):
   - Ubicación: Edificio de Comunicaciones / MEM, Sede Sartenejas y Sede del Litoral.
   - Correo de contacto y soporte: soporte-dti@usb.ve / dti@usb.ve.
   - Horario de atención presencial: Lunes a Viernes de 8:00 AM a 3:30 PM.

2. CAMPUS VIRTUAL USB (Plataforma Moodle):
   - URL de acceso: https://campusvirtual.usb.ve
   - Autenticación: Requiere usuario institucional USB (sin el @usb.ve) y contraseña única de acceso.
   - Fallas comunes:
     * Si no visualizas tus asignaturas inscritas: Recuerda que la sincronización con DACE se realiza 24-48 horas después del proceso de inscripción.
     * Error de carga en evaluaciones: Verifica tu conexión a internet o borra la caché del navegador. Si persiste, solicita soporte inmediato para no perder la entrega.

3. REDES WI-FI EN CAMPUS SARTENEJAS Y LITORAL:
   - Red Principal (Eduroam):
     * Permite conectividad académica global y segura.
     * Nombre de red (SSID): eduroam
     * Usuario: Tu correo institucional completo (ej: 18-10000@usb.ve o nombreusuario@usb.ve)
     * Contraseña: Tu clave de correo institucional USB.
     * Seguridad: WPA2/WPA3 Enterprise (EAP-PEAP, autenticación MSCHAPv2).
   - Red Visitantes (USB-Invitados):
     * Requiere registro temporal y validación mediante portal cautivo.

4. CORREO INSTITUCIONAL Y CUENTAS USB:
   - Servicio provisto bajo Google Workspace for Education.
   - Dominio: @usb.ve.
   - Recuperación de contraseña: Si olvidaste tu contraseña o tu cuenta está bloqueada, debes ingresar al portal de autoservicio de contraseñas de DTI o comunicarte con soporte-dti@usb.ve adjuntando tu carnet o cédula de identidad.

5. POLÍTICA DE ATENCIÓN DE TICKETS EN GLPI USB:
   - Los incidentes críticos (evaluaciones, servidores caídos, laboratorios de clase) se priorizan con urgencia Nivel 4 o 5.
   - Todo reporte genera un identificador de ticket GLPI que el usuario puede rastrear.
"""

SYSTEM_PROMPT_UNIMON = f"""
Eres "UniMon", el Asistente Virtual Oficial de Soporte Técnico de la Universidad Simón Bolívar (USB).
Tu objetivo es ayudar a estudiantes, profesores, personal administrativo y obrero de las sedes de Sartenejas y del Litoral con dudas y problemas técnicos institucionales.

Reglas de comportamiento:
1. Responde SIEMPRE en un tono profesional, empático, claro y en perfecto idioma español.
2. Utiliza la base de conocimiento institucional de la USB provista a continuación para dar instrucciones precisas y oficiales.
3. Si el usuario necesita reportar una falla técnica persistente o daño físico, explícale con amabilidad que puedes generar un ticket de soporte técnico en el sistema GLPI de la USB.
4. Mantén las respuestas estructuradas, con viñetas cuando corresponda para facilitar la lectura.

{USB_KNOWLEDGE_BASE}
"""


class RAGService:
    """
    Cliente para interactuar con Ollama y responder consultas de soporte técnico basadas en la USB.
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = settings.ollama_timeout

    async def query_llm(self, user_message: str, user_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía el mensaje a Ollama (`llama3.1`) con el prompt del sistema y la base de conocimiento de la USB.
        En caso de que Ollama no esté ejecutándose localmente, retorna una respuesta contextual de respaldo.
        """
        greeting_context = f"El usuario se llama {user_name}. " if user_name else ""
        full_user_prompt = f"{greeting_context}Consulta del usuario: {user_message}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_UNIMON},
                {"role": "user", "content": full_user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.3
            }
        }

        url = f"{self.base_url}/api/chat"

        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Enviando consulta a Ollama en {url} con modelo {self.model}...")
                response = await client.post(url, json=payload, timeout=self.timeout)

                if response.status_code == 200:
                    data = response.json()
                    bot_message = data.get("message", {}).get("content", "")
                    return {
                        "response": bot_message,
                        "source": "ollama_llama3.1",
                        "model": self.model
                    }
                else:
                    logger.warning(f"Ollama respondió con código {response.status_code}: {response.text}")
                    return self._generate_fallback_response(user_message, user_name)

        except Exception as exc:
            logger.warning(f"No se pudo conectar con el servidor Ollama ({exc}). Activando respuesta contextual institucional de respaldo.")
            return self._generate_fallback_response(user_message, user_name)

    def _generate_fallback_response(self, user_message: str, user_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generador de respuesta institucional de contingencia cuando Ollama no está disponible.
        """
        saludo = f"¡Hola {user_name}!" if user_name else "¡Hola!"
        msg_lower = user_message.lower()

        if "wifi" in msg_lower or "eduroam" in msg_lower or "red" in msg_lower:
            contenido = (
                f"{saludo} Para conectarte a la red Wi-Fi institucional de la Universidad Simón Bolívar:\n\n"
                "• **Red recomendada:** `eduroam`\n"
                "• **Usuario:** Tu correo institucional completo (ej: `tu_usuario@usb.ve`).\n"
                "• **Contraseña:** Tu clave de acceso institucional.\n"
                "• **Seguridad:** WPA2/WPA3 Enterprise (EAP-PEAP / MSCHAPv2).\n\n"
                "Si visitas el campus y no posees cuenta USB, puedes conectarte a `USB-Invitados` completando el portal cautivo."
            )
        elif "campus" in msg_lower or "moodle" in msg_lower:
            contenido = (
                f"{saludo} Para acceder al Campus Virtual USB:\n\n"
                "• **Enlace directo:** [https://campusvirtual.usb.ve](https://campusvirtual.usb.ve)\n"
                "• **Usuario:** Tu identificador USB (sin `@usb.ve`).\n"
                "• **Contraseña:** Tu clave única de acceso.\n\n"
                "Nota: Si acabas de inscribir materias, la sincronización con DACE toma entre 24 y 48 horas."
            )
        elif "correo" in msg_lower or "clave" in msg_lower or "contraseña" in msg_lower:
            contenido = (
                f"{saludo} Con respecto a tu cuenta y correo institucional USB (@usb.ve):\n\n"
                "• El correo opera bajo Google Workspace institucional.\n"
                "• Para recuperación de contraseñas o cuentas bloqueadas, comunícate con la DTI (Dirección de Servicios Telemáticos) a través de `soporte-dti@usb.ve` indicando tu cédula de identidad y carnet universitario."
            )
        else:
            contenido = (
                f"{saludo} Soy UniMon, el Asistente Virtual de Soporte Técnico de la Universidad Simón Bolívar (USB).\n\n"
                "Puedo ayudarte con información sobre:\n"
                "1. Conexión Wi-Fi institucional (`eduroam`).\n"
                "2. Acceso y problemas con el **Campus Virtual**.\n"
                "3. Soporte de cuentas y correo institucional USB (@usb.ve).\n"
                "4. Apertura y reporte de tickets de fallas técnicas en GLPI.\n\n"
                "¿En qué te puedo colaborar el día de hoy?"
            )

        return {
            "response": contenido,
            "source": "knowledge_base_fallback",
            "model": "rule_based_institutional_usb"
        }
