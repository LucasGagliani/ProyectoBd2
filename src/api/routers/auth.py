"""
Router de autenticación.

Endpoints:
  POST /auth/register/usuario   — registra un pasajero
  POST /auth/register/conductor — registra un conductor (crea usuario + conductor)
  POST /auth/login              — retorna JWT
  POST /auth/logout             — revoca el token de Redis
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import get_db, get_redis_client, get_neo4j_client, oauth2_scheme
from src.databases.schema import Usuario, Conductor
from src.models.user import UserCreate, UserResponse
from src.models.driver import DriverCreate, DriverResponse
from src.models.auth import LoginRequest, TokenResponse
from src.services import auth_service
from src.services.neo4j_service import sync_usuario_node, sync_conductor_node

logger = logging.getLogger(__name__)
router = APIRouter()


# ------------------------------------------------------------------
# Registro de usuario (pasajero)
# ------------------------------------------------------------------

@router.post(
    "/register/usuario",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar pasajero",
)
def register_usuario(
    data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    neo4j=Depends(get_neo4j_client),
):
    """
    Registra un nuevo pasajero.
    - Email único obligatorio.
    - Contraseña mínimo 6 caracteres (se almacena hasheada con bcrypt).
    """
    # Verificar email único
    existing = db.query(Usuario).filter(Usuario.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )

    nuevo_usuario = Usuario(
        nombre=data.nombre,
        email=data.email,
        telefono=data.telefono,
        contrasena=auth_service.hash_password(data.contrasena),
    )

    try:
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )

    # Sincronizar nodo en el grafo Neo4j para futuros matchings
    sync_usuario_node(neo4j, nuevo_usuario.id_usuario, nuevo_usuario.nombre)

    logger.info(f"Nuevo usuario registrado: id={nuevo_usuario.id_usuario}")
    return nuevo_usuario


# ------------------------------------------------------------------
# Registro de conductor
# ------------------------------------------------------------------

@router.post(
    "/register/conductor",
    response_model=DriverResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar conductor",
)
def register_conductor(
    data: DriverCreate,
    db: Annotated[Session, Depends(get_db)],
    neo4j=Depends(get_neo4j_client),
):
    """
    Registra un conductor: crea primero el usuario base y luego el conductor.
    - Email y nro_licencia deben ser únicos.
    - Estado inicial: 'disponible'.
    """
    # Verificar email único
    if db.query(Usuario).filter(Usuario.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )

    # Verificar licencia única
    if db.query(Conductor).filter(Conductor.nro_licencia == data.nro_licencia).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El número de licencia ya está registrado",
        )

    nuevo_usuario = Usuario(
        nombre=data.nombre,
        email=data.email,
        telefono=data.telefono,
        contrasena=auth_service.hash_password(data.contrasena),
    )

    try:
        db.add(nuevo_usuario)
        db.flush()  # Obtener id_usuario sin commitear aún

        nuevo_conductor = Conductor(
            id_usuario=nuevo_usuario.id_usuario,
            nro_licencia=data.nro_licencia,
            estado="disponible",
        )
        db.add(nuevo_conductor)
        db.commit()
        db.refresh(nuevo_conductor)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error de unicidad: email o licencia ya registrados",
        )

    # Sincronizar nodos en Neo4j: el conductor tiene nodo de Usuario + nodo de Conductor
    sync_usuario_node(neo4j, nuevo_usuario.id_usuario, nuevo_usuario.nombre)
    sync_conductor_node(neo4j, nuevo_conductor.id_conductor, nuevo_usuario.nombre)

    logger.info(f"Nuevo conductor registrado: id={nuevo_conductor.id_conductor}")
    return nuevo_conductor


# ------------------------------------------------------------------
# Login
# ------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
)
def login(
    data: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
    redis=Depends(get_redis_client),
):
    """
    Autentica por email + contraseña.
    Retorna un JWT guardado en Redis.
    El rol es 'conductor' si el usuario tiene registro de conductor, sino 'usuario'.
    """
    user = db.query(Usuario).filter(Usuario.email == data.email).first()

    if not user or not auth_service.verify_password(data.contrasena, user.contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Determinar rol
    conductor = (
        db.query(Conductor)
        .filter(Conductor.id_usuario == user.id_usuario)
        .first()
    )
    role = "conductor" if conductor else "usuario"

    token = auth_service.create_access_token(user_id=user.id_usuario, role=role)
    auth_service.store_token_in_redis(redis, token, user.id_usuario, role)

    logger.info(f"Login exitoso: user_id={user.id_usuario} role={role}")
    return TokenResponse(
        access_token=token,
        role=role,
        user_id=user.id_usuario,
    )


# ------------------------------------------------------------------
# Logout
# ------------------------------------------------------------------

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión",
)
def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    redis=Depends(get_redis_client),
):
    """Revoca el token activo del usuario en Redis."""
    auth_service.revoke_token_in_redis(redis, token)
    logger.info("Token revocado (logout)")
