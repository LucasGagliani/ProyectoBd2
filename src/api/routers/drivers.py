"""
Router de conductores.

Endpoints:
  GET   /drivers/me         — perfil completo del conductor autenticado
  PUT   /drivers/me         — actualizar nro_licencia
  PATCH /drivers/me/estado  — cambiar estado (disponible / ocupado / inactivo)
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, get_current_user, get_current_conductor
from src.databases.schema import Usuario, Conductor
from src.models.driver import DriverResponse, DriverUpdate, DriverStatusUpdate, DriverWithUserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/me",
    response_model=DriverWithUserResponse,
    summary="Ver mi perfil de conductor",
)
def get_my_driver_profile(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
):
    """
    Retorna el perfil completo del conductor: datos personales + datos del conductor.
    Solo accesible con token de conductor.
    """
    return DriverWithUserResponse(
        id_conductor=conductor.id_conductor,
        id_usuario=current_user.id_usuario,
        nombre=current_user.nombre,
        email=current_user.email,
        telefono=current_user.telefono,
        nro_licencia=conductor.nro_licencia,
        estado=conductor.estado,
        calificacion_promedio=conductor.calificacion_promedio,
        latitud_actual=conductor.latitud_actual,
        longitud_actual=conductor.longitud_actual,
    )


@router.put(
    "/me",
    response_model=DriverResponse,
    summary="Actualizar perfil de conductor",
)
def update_my_driver_profile(
    data: DriverUpdate,
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Actualiza el número de licencia del conductor.
    Solo se modifican los campos enviados.
    """
    if data.nro_licencia is not None:
        # Verificar que la nueva licencia no esté en uso
        existing = (
            db.query(Conductor)
            .filter(
                Conductor.nro_licencia == data.nro_licencia,
                Conductor.id_conductor != conductor.id_conductor,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El número de licencia ya está en uso por otro conductor",
            )
        conductor.nro_licencia = data.nro_licencia.strip()

    db.commit()
    db.refresh(conductor)

    logger.info(f"Perfil conductor actualizado: id={conductor.id_conductor}")
    return conductor


@router.patch(
    "/me/estado",
    response_model=DriverResponse,
    summary="Cambiar estado del conductor",
)
def update_driver_status(
    data: DriverStatusUpdate,
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Cambia el estado del conductor.
    - disponible: puede recibir viajes
    - ocupado:    tiene un viaje activo
    - inactivo:   desconectado de la plataforma
    """
    conductor.estado = data.estado
    db.commit()
    db.refresh(conductor)

    logger.info(f"Estado conductor actualizado: id={conductor.id_conductor} -> {data.estado}")
    return conductor
