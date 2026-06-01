"""Router de viajes: estado y tarifas."""

import logging
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db, get_redis_client
from src.databases.schema import Conductor, Viaje
from src.models.trip import TripFareResponse, TripStatusResponse, TripStatusUpdate
from src.services import trip_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _load_conductor(db: Session, current_user) -> Optional[Conductor]:
    return db.query(Conductor).filter(Conductor.id_usuario == current_user.id_usuario).first()


def _authorize_trip_access(current_user, conductor, viaje: Viaje) -> None:
    if viaje.id_usuario == current_user.id_usuario:
        return
    if conductor is not None and viaje.id_conductor == conductor.id_conductor:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tenés permisos para ver o modificar este viaje.",
    )


@router.get(
    "/{trip_id}/status",
    response_model=TripStatusResponse,
    summary="Ver estado del viaje",
)
def get_trip_status(
    trip_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    redis=Depends(get_redis_client),
):
    viaje = db.get(Viaje, trip_id)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = _load_conductor(db, current_user)
    _authorize_trip_access(current_user, conductor, viaje)

    try:
        estado, cached = trip_service.get_trip_status(db, redis, trip_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    return TripStatusResponse(id_viaje=trip_id, estado=estado, cached=cached)


@router.put(
    "/{trip_id}/status",
    response_model=TripStatusResponse,
    summary="Actualizar estado del viaje",
)
def update_trip_status(
    trip_id: int,
    data: TripStatusUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    redis=Depends(get_redis_client),
):
    viaje = db.get(Viaje, trip_id)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = _load_conductor(db, current_user)
    target_status = data.estado
    current_status = viaje.estado
    assigned_conductor = db.get(Conductor, viaje.id_conductor) if viaje.id_conductor else None

    if not trip_service.is_valid_status_transition(current_status, target_status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Transición inválida de {current_status} a {target_status}. "
                f"Permisos: pendiente→aceptado/cancelado, aceptado→en_curso/cancelado, en_curso→finalizado/cancelado."
            ),
        )

    if target_status == "aceptado":
        if conductor is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo un conductor puede aceptar un viaje.",
            )
        if viaje.id_conductor is not None and viaje.id_conductor != conductor.id_conductor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este viaje ya fue asignado a otro conductor.",
            )
        viaje.id_conductor = conductor.id_conductor
        viaje.estado = "aceptado"
        if assigned_conductor is not None:
            assigned_conductor.estado = "ocupado"
        else:
            conductor.estado = "ocupado"

    elif target_status in {"en_curso", "finalizado"}:
        if conductor is None or viaje.id_conductor != conductor.id_conductor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el conductor asignado puede avanzar el estado del viaje.",
            )
        viaje.estado = target_status
        if target_status == "finalizado" and assigned_conductor is not None:
            assigned_conductor.estado = "disponible"

    elif target_status == "cancelado":
        if viaje.id_usuario != current_user.id_usuario and (
            conductor is None or viaje.id_conductor != conductor.id_conductor
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el pasajero dueño del viaje o el conductor asignado puede cancelarlo.",
            )
        viaje.estado = "cancelado"
        if assigned_conductor is not None:
            assigned_conductor.estado = "disponible"

    db.commit()
    db.refresh(viaje)
    if conductor is not None:
        db.refresh(conductor)
    elif assigned_conductor is not None:
        db.refresh(assigned_conductor)
    trip_service.cache_trip_status(redis, trip_id, viaje.estado)

    logger.info(
        f"Viaje {trip_id} actualizado: {current_status} -> {viaje.estado}"
    )
    return TripStatusResponse(id_viaje=trip_id, estado=viaje.estado, cached=False)


@router.get(
    "/{trip_id}/fare",
    response_model=TripFareResponse,
    summary="Ver costo estimado o final del viaje",
)
def get_trip_fare(
    trip_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    viaje = db.get(Viaje, trip_id)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = _load_conductor(db, current_user)
    _authorize_trip_access(current_user, conductor, viaje)

    if viaje.pago is not None:
        pago = viaje.pago
        return TripFareResponse(
            id_viaje=trip_id,
            distancia_km=viaje.distancia_km,
            tiempo_minutos=viaje.tiempo_minutos,
            tarifa_base=pago.monto_base,
            tarifa_adicional=pago.tarifa_adicional,
            monto_total=pago.monto_total,
        )

    tarifa_base = trip_service.estimate_trip_fare(
        Decimal(viaje.distancia_km) if viaje.distancia_km is not None else Decimal(0),
        viaje.tiempo_minutos,
    )
    tarifa_adicional = Decimal("0.00")
    monto_total = trip_service.calculate_payment_total(tarifa_base, tarifa_adicional)

    return TripFareResponse(
        id_viaje=trip_id,
        distancia_km=viaje.distancia_km,
        tiempo_minutos=viaje.tiempo_minutos,
        tarifa_base=tarifa_base,
        tarifa_adicional=tarifa_adicional,
        monto_total=monto_total,
    )
