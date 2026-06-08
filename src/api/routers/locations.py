"""
Router de ubicaciones GPS.

Endpoints:
  POST /locations/update            — conductor actualiza su posición actual
  GET  /locations/{trip_id}/history — historial GPS del viaje (Cassandra)
  GET  /locations/conductor/{id}    — posición actual de un conductor (Redis)

DBs usadas:
  - Cassandra → historial completo del recorrido (serie temporal)
  - Redis     → posición actual del conductor (tiempo real)
  - PostgreSQL → sincroniza latitud_actual/longitud_actual en Conductor
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import (
    get_current_user, get_db, get_redis_client,
    get_cassandra_client, get_current_conductor,
)
from src.databases.schema import Conductor, Viaje
from src.models.location import LocationUpdate, LocationResponse, LocationHistoryResponse
from src.services import location_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/update",
    response_model=LocationResponse,
    summary="Actualizar posición del conductor",
)
def update_location(
    data: LocationUpdate,
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
    db: Annotated[Session, Depends(get_db)],
    redis=Depends(get_redis_client),
    cassandra=Depends(get_cassandra_client),
):
    """
    El conductor envía su posición actual:
    1. Redis → actualiza posición en tiempo real (clave con TTL 1h)
    2. Cassandra → guarda el punto en el historial del viaje (si hay viaje activo)
    3. PostgreSQL → sincroniza latitud_actual/longitud_actual en el modelo Conductor
    """
    lat = float(data.latitud)
    lon = float(data.longitud)
    vel = float(data.velocidad_estimada) if data.velocidad_estimada else None

    # 1. Redis — posición actual
    location_service.update_conductor_position_redis(redis, conductor.id_conductor, lat, lon)

    # 2. Cassandra — historial del viaje
    if data.id_viaje is not None:
        # Verificar que el viaje pertenece a este conductor
        viaje = db.get(Viaje, data.id_viaje)
        if viaje and viaje.id_conductor == conductor.id_conductor:
            location_service.save_location_to_cassandra(
                cassandra, data.id_viaje, conductor.id_conductor, lat, lon, vel
            )

    # 3. PostgreSQL — sincronizar posición en el modelo
    conductor.latitud_actual = data.latitud
    conductor.longitud_actual = data.longitud
    db.commit()

    logger.info(f"Posición actualizada: conductor={conductor.id_conductor} lat={lat} lon={lon}")
    return LocationResponse(
        id_conductor=conductor.id_conductor,
        id_viaje=data.id_viaje,
        latitud=data.latitud,
        longitud=data.longitud,
        velocidad_estimada=data.velocidad_estimada,
    )


@router.get(
    "/{trip_id}/history",
    response_model=LocationHistoryResponse,
    summary="Historial GPS del viaje (Cassandra)",
)
def get_trip_history(
    trip_id: int,
    current_user=Depends(get_current_user),
    db: Annotated[Session, Depends(get_db)] = None,
    cassandra=Depends(get_cassandra_client),
):
    """
    Retorna el historial completo de ubicaciones GPS del viaje desde Cassandra.
    Accesible por el pasajero o el conductor asignado.
    """
    viaje = db.get(Viaje, trip_id)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = db.query(Conductor).filter(
        Conductor.id_usuario == current_user.id_usuario
    ).first()

    if viaje.id_usuario != current_user.id_usuario:
        if conductor is None or viaje.id_conductor != conductor.id_conductor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés permisos para ver el historial de este viaje.",
            )

    registros = location_service.get_trip_gps_history(cassandra, trip_id)
    return LocationHistoryResponse(id_viaje=trip_id, registros=registros)


@router.get(
    "/conductor/{conductor_id}",
    response_model=LocationResponse,
    summary="Posición actual de un conductor (Redis)",
)
def get_conductor_position(
    conductor_id: int,
    current_user=Depends(get_current_user),
    redis=Depends(get_redis_client),
    db: Annotated[Session, Depends(get_db)] = None,
):
    """
    Retorna la posición actual del conductor desde Redis.
    Disponible para cualquier usuario autenticado (útil para el front en tiempo real).
    """
    pos = location_service.get_conductor_position_redis(redis, conductor_id)

    if pos is None:
        # Fallback a PostgreSQL si Redis no tiene el dato
        conductor = db.get(Conductor, conductor_id)
        if conductor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conductor no encontrado")
        if conductor.latitud_actual is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El conductor no tiene posición registrada",
            )
        return LocationResponse(
            id_conductor=conductor_id,
            latitud=conductor.latitud_actual,
            longitud=conductor.longitud_actual,
        )

    return LocationResponse(
        id_conductor=conductor_id,
        latitud=pos["lat"],
        longitud=pos["lon"],
    )
