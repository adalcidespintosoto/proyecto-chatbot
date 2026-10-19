"""Cifrado de secretos administrados por la aplicación."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


class SecretStoreError(ValueError):
    """La aplicación no puede cifrar o descifrar una credencial segura."""


def _cipher() -> Fernet:
    master_key = get_settings().llm_credentials_encryption_key
    if len(master_key) < 32:
        raise SecretStoreError("La protección de credenciales no está disponible en el servidor.")
    # Deriva una clave Fernet válida sin almacenar una segunda llave en el código.
    key = base64.urlsafe_b64encode(hashlib.sha256(master_key.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    if not value:
        raise SecretStoreError("La credencial del proveedor está vacía.")
    return _cipher().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str) -> str:
    if not value:
        raise SecretStoreError("La instancia no tiene una credencial de proveedor guardada.")
    try:
        return _cipher().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, ValueError) as exc:
        raise SecretStoreError(
            "No se pudo validar la credencial guardada. Revisa la configuración de seguridad del servidor."
        ) from exc
