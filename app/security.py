"""
Módulo de Seguridad, Autenticación y Autorización para UniMon.
Provee esquemas de autenticación HTTP Basic seguros contra timing attacks
para proteger el panel administrativo y las APIs de gestión.
"""

import secrets
import logging
from urllib.parse import urlsplit
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import get_settings

logger = logging.getLogger("unimon.security")

security = HTTPBasic()


def require_admin_origin(request: Request) -> None:
    """Bloquea solicitudes administrativas mutantes provenientes de otro sitio."""
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(status_code=403, detail="Origen no autorizado")
    origin = request.headers.get("origin")
    if origin:
        submitted = urlsplit(origin)
        host = request.headers.get("host", "")
        if submitted.netloc.lower() != host.lower() or submitted.scheme not in {"http", "https"}:
            raise HTTPException(status_code=403, detail="Origen no autorizado")


def require_admin_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Valida las credenciales administrativas mediante comparación en tiempo constante
    (secrets.compare_digest) para mitigar timing attacks.
    """
    settings = get_settings()

    if (not settings.admin_username or not settings.admin_password
            or secrets.compare_digest(settings.admin_password, "UniMonAdmin2026*")):
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
        logger.warning("Intento de acceso administrativo no autorizado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de administración inválidas.",
            headers={"WWW-Authenticate": "Basic realm='UniMon Admin'"}
        )

    return credentials.username
