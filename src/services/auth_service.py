"""
Servicio de autenticación.
Maneja hashing de contraseñas y generación/verificación de tokens JWT.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from src.config import settings

logger = logging.getLogger(__name__)

# Prefijo de las keys en Redis para tokens activos
REDIS_TOKEN_PREFIX = "token:"


def hash_password(password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(user_id: int, role: str) -> str:
    """
    Genera un JWT firmado con los datos del usuario.

    Args:
        user_id: ID del usuario en la tabla usuarios.
        role: "usuario" o "conductor".

    Returns:
        Token JWT como string.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_token(token: str) -> Optional[dict]:
    """
    Decodifica y valida un JWT.

    Returns:
        Payload del token o None si es inválido/expirado.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.warning(f"Token inválido: {e}")
        return None


def redis_token_key(token: str) -> str:
    """Genera la key de Redis para un token activo."""
    return f"{REDIS_TOKEN_PREFIX}{token}"


def store_token_in_redis(redis_client, token: str, user_id: int, role: str) -> None:
    """Guarda el token en Redis con TTL igual al tiempo de expiración del JWT."""
    key = redis_token_key(token)
    value = f"{user_id}:{role}"
    redis_client.set(key, value, ex=settings.JWT_EXPIRE_MINUTES * 60)


def revoke_token_in_redis(redis_client, token: str) -> None:
    """Elimina el token de Redis (logout)."""
    redis_client.delete(redis_token_key(token))


def token_is_active(redis_client, token: str) -> bool:
    """Verifica que el token esté activo en Redis (no fue revocado)."""
    return redis_client.exists(redis_token_key(token))
