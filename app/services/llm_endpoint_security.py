"""Validación defensiva de endpoints LLM configurables desde administración."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit


def validate_custom_llm_base_url(base_url: str, *, resolve_dns: bool = False) -> str:
    """Acepta únicamente endpoints HTTPS públicos, sin credenciales ni redirecciones embebidas."""
    value = str(base_url or "").strip().rstrip("/")
    if len(value) > 512:
        raise ValueError("La URL base no puede superar 512 caracteres.")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError("La URL base del proveedor no es válida.") from exc
    if (
        parsed.scheme.casefold() != "https"
        or not hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Usa una URL HTTPS pública, sin usuario, contraseña, parámetros ni fragmento.")
    if port not in (None, 443):
        raise ValueError("Por seguridad, los endpoints personalizados deben usar HTTPS en el puerto estándar 443.")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("El endpoint no puede apuntar a una dirección IP privada o local.")

    if resolve_dns:
        try:
            resolved = {
                ipaddress.ip_address(item[4][0].split("%", 1)[0])
                for item in socket.getaddrinfo(hostname, port or 443, type=socket.SOCK_STREAM)
            }
        except (OSError, ValueError) as exc:
            raise ValueError("No se pudo comprobar el dominio del proveedor. Revisa la URL y su conexión.") from exc
        if not resolved or any(not item.is_global for item in resolved):
            raise ValueError("El dominio del proveedor resuelve a una dirección privada o no pública.")
    return value
