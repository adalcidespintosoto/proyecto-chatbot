"""
Módulo de Seguridad, Autenticación y Autorización para UniMon.
Provee esquemas de autenticación HTTP Basic seguros contra timing attacks
para proteger el panel administrativo y las APIs de gestión.
"""

import secrets
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import get_settings

logger = logging.getLogger("unimon.security")

security = HTTPBasic()


def require_admin_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Valida las credenciales administrativas mediante comparación en tiempo constante
    (secrets.compare_digest) para mitigar timing attacks.
    """
    settings = get_settings()

    if not settings.admin_username or not settings.admin_password:
        logger.error("Vulnerabilidad prevenida: ADMIN_USERNAME o ADMIN_PASSWORD no están definidos en .env")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración del servidor. El acceso administrativo está deshabilitado por seguridad."
        )

    correct_username_bytes = settings.admin_username.encode("utf-8")
    provided_username_bytes = credentials.username.encode("utf-8")
    is_username_correct = secrets.compare_digest(correct_username_bytes, provided_username_bytes)

    correct_password_bytes = settings.admin_password.encode("utf-8")
    provided_password_bytes = credentials.password.encode("utf-8")
    is_password_correct = secrets.compare_digest(correct_password_bytes, provided_password_bytes)

    if not (is_username_correct and is_password_correct):
        logger.warning(
            "Intento de acceso administrativo no autorizado con usuario: '%s'",
            credentials.username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de administración inválidas.",
            headers={"WWW-Authenticate": "Basic realm='UniMon Admin'"}
        )

    return credentials.username
