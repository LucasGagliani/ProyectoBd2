"""
Dependencias inyectables de FastAPI.
Proveen sesiones DB, cliente Redis y el usuario autenticado actual.
"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.databases.connections import get_sql, get_redis
from src.databases.schema import Usuario, Conductor
from src.services import auth_service

logger = logging.getLogger(__name__)

# FastAPI infiere el token del header Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Session:
    """Dependency que provee una sesión SQLAlchemy por request."""
    sql = get_sql()
    db = sql.get_session()
    try:
        yield db
    finally:
        db.close()


def get_redis_client():
    """Dependency que provee el cliente Redis."""
    return get_redis().client


def get_neo4j_client():
    """
    Dependency que provee la instancia Neo4jDatabase.
    Retorna None si Neo4j no está disponible — los servicios deben manejarlo con graceful degradation.
    """
    from src.databases.connections import get_neo4j
    return get_neo4j()


# -------------------------------------------------------------------
# Dependencia principal de autenticación
# -------------------------------------------------------------------

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
    redis=Depends(get_redis_client),
) -> Usuario:
    """
    Valida el JWT y verifica que el token siga activo en Redis.
    Retorna el objeto Usuario de la DB.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = auth_service.decode_token(token)
    if payload is None:
        raise credentials_exception

    if not auth_service.token_is_active(redis, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada o cerrada. Volvé a iniciar sesión.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.get(Usuario, int(user_id))
    if user is None:
        raise credentials_exception

    return user


def get_current_conductor(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Conductor:
    """
    Igual que get_current_user pero verifica que sea un conductor.
    """
    conductor = (
        db.query(Conductor)
        .filter(Conductor.id_usuario == current_user.id_usuario)
        .first()
    )
    if conductor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta acción requiere una cuenta de conductor",
        )
    return conductor
