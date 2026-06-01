"""
Router de usuarios (pasajeros).

Endpoints:
  GET  /users/me  — perfil del usuario autenticado
  PUT  /users/me  — actualizar nombre y/o teléfono
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, get_current_user
from src.databases.schema import Usuario
from src.models.user import UserResponse, UserUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Ver mi perfil",
)
def get_my_profile(
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    """Retorna el perfil del usuario autenticado."""
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Actualizar mi perfil",
)
def update_my_profile(
    data: UserUpdate,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Actualiza nombre y/o teléfono del usuario autenticado.
    Solo se modifican los campos enviados (parcial).
    """
    if data.nombre is not None:
        current_user.nombre = data.nombre.strip()
    if data.telefono is not None:
        current_user.telefono = data.telefono

    db.commit()
    db.refresh(current_user)

    logger.info(f"Perfil actualizado: user_id={current_user.id_usuario}")
    return current_user
