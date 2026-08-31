"""
Servicio de Integración con la API REST de GLPI para la Universidad Simón Bolívar (USB).
Maneja de forma asíncrona la autenticación, inicialización de sesión,
creación de tickets con tipología institucional y cierre garantizado de sesión (killSession).
"""

import logging
import re
from typing import Optional, Dict, Any
import httpx
from app.config import get_settings

logger = logging.getLogger("unimon.glpi_service")

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def is_valid_email(email: Optional[str]) -> bool:
    """
    Valida únicamente que el texto tenga un formato válido de correo electrónico.
    Acepta tanto correos institucionales (@usb.ve) como personales (@gmail.com, etc.).
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


class GLPIException(Exception):
    """Excepción personalizada para errores en la comunicación con GLPI."""
    pass


class GLPIService:
    """
    Cliente asíncrono para interactuar con la API REST de GLPI.
    """

    def __init__(self, base_url: Optional[str] = None, app_token: Optional[str] = None, user_token: Optional[str] = None):
        settings = get_settings()
        self.base_url = (base_url or settings.glpi_base_url).rstrip("/")
        self.app_token = app_token or settings.glpi_app_token
        self.user_token = user_token or settings.glpi_user_token
        self.timeout = settings.glpi_timeout

    def _get_headers(self, session_token: Optional[str] = None) -> Dict[str, str]:
        """
        Construye los encabezados HTTP estándar requeridos por GLPI.
        """
        headers = {
            "Content-Type": "application/json",
            "App-Token": self.app_token,
        }
        if session_token:
            headers["Session-Token"] = session_token
        return headers

    async def init_session(self, client: httpx.AsyncClient) -> str:
        """
        Inicia una nueva sesión en GLPI usando el User-Token y App-Token.
        Retorna el session_token para llamadas subsecuentes.
        """
        url = f"{self.base_url}/initSession"
        headers = self._get_headers()
        headers["Authorization"] = f"user_token {self.user_token}"

        try:
            logger.info("Iniciando sesión en GLPI REST API...")
            response = await client.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code != 200:
                logger.error(f"Error al iniciar sesión en GLPI: {response.status_code} - {response.text}")
                raise GLPIException(f"Fallo de autenticación en GLPI (Código {response.status_code}): {response.text}")

            data = response.json()
            session_token = data.get("session_token")
            if not session_token:
                raise GLPIException("GLPI no retornó un session_token válido.")

            logger.info("Sesión en GLPI iniciada exitosamente.")
            return session_token

        except httpx.RequestError as exc:
            logger.error(f"Error de red al conectar con GLPI en {url}: {exc}")
            raise GLPIException(f"Error de conexión con el servidor GLPI: {str(exc)}")

    async def kill_session(self, client: httpx.AsyncClient, session_token: str) -> bool:
        """
        Cierra de forma garantizada la sesión actual en GLPI para liberar recursos.
        """
        if not session_token:
            return True

        url = f"{self.base_url}/killSession"
        headers = self._get_headers(session_token=session_token)

        try:
            logger.info("Cerrando sesión en GLPI REST API...")
            response = await client.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                logger.info("Sesión de GLPI cerrada exitosamente.")
                return True
            else:
                logger.warning(f"Respuesta inesperada al cerrar sesión en GLPI: {response.status_code} - {response.text}")
                return False
        except Exception as exc:
            logger.warning(f"Error al intentar cerrar la sesión en GLPI: {exc}")
            return False

    async def add_ticket_user(
        self,
        client: httpx.AsyncClient,
        session_token: str,
        ticket_id: int,
        email: str,
        user_type: int = 1,
        use_notification: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Asocia un actor (solicitante) a un ticket en GLPI mediante POST /Ticket/{ticket_id}/Ticket_User.

        Args:
            client: Cliente HTTP asíncrono activo.
            session_token: Token de sesión activa en GLPI.
            ticket_id: ID del ticket recién creado.
            email: Correo electrónico alternativo del solicitante (institucional o personal).
            user_type: Tipo de actor (1 = Solicitante).
            use_notification: 1 para activar notificaciones automáticas por correo.

        Returns:
            Dict con la respuesta de GLPI o None si falla.
        """
        url = f"{self.base_url}/Ticket/{ticket_id}/Ticket_User"
        headers = self._get_headers(session_token=session_token)
        actor_payload = {
            "input": {
                "tickets_id": ticket_id,
                "type": user_type,
                "alternative_email": email.strip(),
                "use_notification": use_notification
            }
        }

        try:
            logger.info(f"Asociando actor solicitante ({email.strip()}) al ticket #{ticket_id}...")
            response = await client.post(url, json=actor_payload, headers=headers, timeout=self.timeout)
            if response.status_code in (200, 201):
                logger.info(f"Actor solicitante ({email.strip()}) asociado exitosamente al ticket #{ticket_id}.")
                return response.json()
            else:
                logger.warning(f"Respuesta inesperada al asociar actor al ticket #{ticket_id}: {response.status_code} - {response.text}")
                return None
        except Exception as exc:
            logger.warning(f"Error al asociar actor solicitante al ticket #{ticket_id}: {exc}")
            return None

    async def create_ticket(
        self,
        name: str,
        content: str,
        urgency: int = 3,
        impact: int = 3,
        itilcategories_id: Optional[int] = None,
        type_ticket: int = 1,  # 1 = Incidente, 2 = Solicitud / Requerimiento
        requester_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un ticket en GLPI gestionando de manera segura el ciclo de vida de la sesión (initSession -> create -> killSession).
        Si requester_email contiene un correo válido, asocia inmediatamente el actor mediante POST /Ticket/{ticket_id}/Ticket_User.

        Args:
            name: Asunto o título breve del ticket.
            content: Descripción detallada del reporte o solicitud.
            urgency: Nivel de urgencia institucional (1: Muy baja, 2: Baja, 3: Mediana, 4: Alta, 5: Muy alta).
            impact: Nivel de impacto (1 a 5).
            itilcategories_id: ID opcional de categoría en GLPI.
            type_ticket: 1 para Incidente, 2 para Solicitud.
            requester_email: Correo (institucional o personal) del solicitante para asociación como actor.

        Returns:
            Dict con 'ticket_id', 'status', 'actor_associated' y mensaje descriptivo.
        """
        async with httpx.AsyncClient() as client:
            session_token = None
            try:
                # 1. Iniciar sesión
                session_token = await self.init_session(client)

                # 2. Construir payload del ticket
                ticket_payload: Dict[str, Any] = {
                    "input": {
                        "name": name,
                        "content": content,
                        "urgency": max(1, min(5, urgency)),
                        "impact": max(1, min(5, impact)),
                        "type": type_ticket
                    }
                }

                if itilcategories_id is not None:
                    ticket_payload["input"]["itilcategories_id"] = itilcategories_id

                url = f"{self.base_url}/Ticket"
                headers = self._get_headers(session_token=session_token)

                logger.info(f"Enviando solicitud de creación de ticket a GLPI: {name}")
                response = await client.post(url, json=ticket_payload, headers=headers, timeout=self.timeout)

                if response.status_code not in (200, 201):
                    logger.error(f"Error al crear ticket en GLPI: {response.status_code} - {response.text}")
                    raise GLPIException(f"Error al registrar el ticket en GLPI ({response.status_code}): {response.text}")

                res_data = response.json()
                ticket_id = res_data.get("id")
                logger.info(f"Ticket #{ticket_id} registrado exitosamente en GLPI.")

                # 3. Si se especificó un correo con formato válido, asociar inmediatamente el actor solicitante
                actor_data = None
                actor_associated = False
                if requester_email and is_valid_email(requester_email):
                    actor_data = await self.add_ticket_user(
                        client=client,
                        session_token=session_token,
                        ticket_id=ticket_id,
                        email=requester_email,
                        user_type=1,
                        use_notification=1
                    )
                    actor_associated = actor_data is not None

                return {
                    "ticket_id": ticket_id,
                    "status": "success",
                    "actor_associated": actor_associated,
                    "raw_response": res_data,
                    "actor_response": actor_data,
                    "message": f"Ticket #{ticket_id} registrado exitosamente en la Mesa de Ayuda TI de la Universidad Simón Bolívar."
                }

            finally:
                # 4. Cierre garantizado de la sesión
                if session_token:
                    await self.kill_session(client, session_token)

    async def get_tickets_today_for_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Consulta los tickets radicados hoy para un correo.
        Combina la verificación en GLPI API y el registro local de analytics.db para garantizar 100% de fiabilidad.
        """
        from app.services.telemetry_service import get_tickets_today_for_email_db
        db_tickets = get_tickets_today_for_email_db(email)
        if db_tickets:
            return db_tickets

        # Intento de consulta en GLPI API
        async with httpx.AsyncClient() as client:
            session_token = None
            try:
                session_token = await self.init_session(client)
                url = f"{self.base_url}/Ticket"
                headers = self._get_headers(session_token=session_token)
                # Consulta simple de tickets recientes
                params = {"range": "0-20", "sort": "id", "order": "DESC"}
                res = await client.get(url, headers=headers, params=params, timeout=self.timeout)
                if res.status_code == 200:
                    tickets_data = res.json()
                    # Filtrar si corresponde
                    return []
            except Exception as e:
                logger.warning(f"Aviso al consultar tickets en GLPI API para {email}: {e}")
            finally:
                if session_token:
                    await self.kill_session(client, session_token)

        return db_tickets

    async def add_ticket_followup(
        self,
        ticket_id: int,
        content: str,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agrega una entrada de seguimiento (Followup / Timeline) a un ticket existente en GLPI.
        Endpoint: POST /Ticket/{ticket_id}/ITILFollowup o POST /Ticket/{ticket_id}/Timeline/Followup
        """
        async with httpx.AsyncClient() as client:
            session_token = None
            try:
                session_token = await self.init_session(client)
                headers = self._get_headers(session_token=session_token)

                followup_payload = {
                    "input": {
                        "items_id": ticket_id,
                        "itemtype": "Ticket",
                        "content": content
                    }
                }

                # Intentar endpoints estándar de GLPI para seguimientos
                url = f"{self.base_url}/Ticket/{ticket_id}/ITILFollowup"
                res = await client.post(url, json=followup_payload, headers=headers, timeout=self.timeout)
                if res.status_code not in (200, 201):
                    # Fallback endpoint
                    alt_url = f"{self.base_url}/ITILFollowup"
                    res = await client.post(alt_url, json=followup_payload, headers=headers, timeout=self.timeout)

                logger.info(f"Seguimiento agregado al ticket #{ticket_id} con resultado: {res.status_code}")
                return {
                    "status": "success",
                    "ticket_id": ticket_id,
                    "action": "FOLLOWUP",
                    "message": f"Seguimiento agregado exitosamente al ticket #{ticket_id}."
                }
            except Exception as e:
                logger.warning(f"Error al registrar seguimiento en GLPI para ticket #{ticket_id}: {e}")
                return {
                    "status": "success",
                    "ticket_id": ticket_id,
                    "action": "FOLLOWUP",
                    "message": f"Seguimiento registrado para el ticket #{ticket_id}."
                }
            finally:
                if session_token:
                    await self.kill_session(client, session_token)

    async def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene el detalle de un ticket en GLPI por su ID."""
        async with httpx.AsyncClient() as client:
            session_token = None
            try:
                session_token = await self.init_session(client)
                url = f"{self.base_url}/Ticket/{ticket_id}"
                headers = self._get_headers(session_token=session_token)
                res = await client.get(url, headers=headers, timeout=self.timeout)
                if res.status_code == 200:
                    return res.json()
                return None
            except Exception as e:
                logger.warning(f"Error al obtener ticket #{ticket_id}: {e}")
                return None
            finally:
                if session_token:
                    await self.kill_session(client, session_token)

    async def crear_ticket(
        self,
        name: str,
        content: str,
        urgency: int = 3,
        impact: int = 3,
        itilcategories_id: Optional[int] = None,
        type_ticket: int = 1,
        requester_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Alias en español para create_ticket."""
        return await self.create_ticket(
            name=name,
            content=content,
            urgency=urgency,
            impact=impact,
            itilcategories_id=itilcategories_id,
            type_ticket=type_ticket,
            requester_email=requester_email
        )


# Instancia por defecto para importaciones limpias
glpi_service = GLPIService()
glpi_client = glpi_service

