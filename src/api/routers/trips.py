"""Router de viajes: estado y tarifas."""

import logging
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db, get_redis_client, get_neo4j_client
from src.databases.schema import Conductor, Viaje
from typing import List
from src.models.trip import (
    TripFareResponse, TripHistoryResponse, TripStatusResponse,
    TripStatusUpdate, TripCreate, TripResponse,
)
from src.services import trip_service
from src.services.neo4j_service import register_trip_relationship

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


# ==================== LISTAR MIS VIAJES ====================

@router.get(
    "/my",
    response_model=List[TripResponse],
    summary="Ver mis viajes",
)
def get_my_trips(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retorna los viajes activos del usuario autenticado.
    - Si es pasajero: sus propios viajes
    - Si es conductor: los viajes asignados a él
    """
    conductor = _load_conductor(db, current_user)

    if conductor:
        viajes = (
            db.query(Viaje)
            .filter(
                Viaje.id_conductor == conductor.id_conductor,
                Viaje.estado.in_(["pendiente", "aceptado", "en_curso"]),
            )
            .order_by(Viaje.fecha_hora.desc())
            .all()
        )
    else:
        viajes = (
            db.query(Viaje)
            .filter(
                Viaje.id_usuario == current_user.id_usuario,
                Viaje.estado.in_(["pendiente", "aceptado", "en_curso"]),
            )
            .order_by(Viaje.fecha_hora.desc())
            .all()
        )

    return [
        TripResponse(
            id_viaje=v.id_viaje,
            id_usuario=v.id_usuario,
            id_conductor=v.id_conductor,
            latitud_inicio=v.latitud_inicio,
            longitud_inicio=v.longitud_inicio,
            latitud_destino=v.latitud_destino,
            longitud_destino=v.longitud_destino,
            distancia_km=v.distancia_km,
            tiempo_minutos=v.tiempo_minutos,
            estado=v.estado,
            fecha_hora=str(v.fecha_hora),
        )
        for v in viajes
    ]


# ==================== HISTORIAL DE VIAJES ====================

@router.get(
    "/history",
    response_model=List[TripHistoryResponse],
    summary="Ver historial de viajes",
)
def get_trip_history(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retorna viajes finalizados o cancelados del usuario autenticado.
    Incluye monto pagado y estado de reseñas.
    """
    conductor = _load_conductor(db, current_user)
    conductor_id = conductor.id_conductor if conductor else None
    history = trip_service.get_trip_history(db, current_user.id_usuario, conductor_id)

    return [
        TripHistoryResponse(
            id_viaje=item["viaje"].id_viaje,
            id_usuario=item["viaje"].id_usuario,
            id_conductor=item["viaje"].id_conductor,
            latitud_inicio=item["viaje"].latitud_inicio,
            longitud_inicio=item["viaje"].longitud_inicio,
            latitud_destino=item["viaje"].latitud_destino,
            longitud_destino=item["viaje"].longitud_destino,
            distancia_km=item["viaje"].distancia_km,
            tiempo_minutos=item["viaje"].tiempo_minutos,
            estado=item["viaje"].estado,
            fecha_hora=str(item["viaje"].fecha_hora),
            monto_total=item["monto_total"],
            estado_pago=item["estado_pago"],
            mi_resena=item["mi_resena"],
            resenas_completas=item["resenas_completas"],
        )
        for item in history
    ]


# ==================== CREAR VIAJE ====================

@router.post(
    "",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva solicitud de viaje",
)
def create_trip(
    data: TripCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    redis=Depends(get_redis_client),
    neo4j=Depends(get_neo4j_client),
):
    """
    Crea una nueva solicitud de viaje y asigna automáticamente el conductor más cercano.
    
    - Usuario: pasajero que solicita el viaje
    - Sistema: busca conductores disponibles (estado='disponible', sin viajes activos)
    - Sistema: calcula distancia al usuario y asigna al más cercano
    - Resultado: viaje con estado 'aceptado' y conductor asignado, o 'pendiente' sin conductor
    """
    # Validar que el usuario no tenga demasiadas solicitudes pendientes (opcional)
    # Por ahora, permitimos crear viajes
    
    # Crear viaje en estado "pendiente"
    viaje = Viaje(
        id_usuario=current_user.id_usuario,
        id_conductor=None,  # Se asignará automáticamente
        latitud_inicio=data.latitud_inicio,
        longitud_inicio=data.longitud_inicio,
        latitud_destino=data.latitud_destino,
        longitud_destino=data.longitud_destino,
        distancia_km=data.distancia_km,
        tiempo_minutos=data.tiempo_minutos,
        estado="pendiente",
    )
    
    db.add(viaje)
    db.flush()  # Obtener el ID del viaje sin hacer commit aún
    
    # Buscar conductor disponible usando matching en dos pasos:
    # 1. Neo4j: prioriza conductores con historial con este usuario
    # 2. Fallback: conductor disponible más cercano por posición GPS
    available_drivers = trip_service.find_available_drivers(db)

    if available_drivers:
        best_driver = trip_service.find_best_driver(
            db=db,
            redis_client=redis,
            neo4j_client=neo4j,
            available_drivers=available_drivers,
            usuario_id=current_user.id_usuario,
            usuario_lat=float(data.latitud_inicio),
            usuario_lon=float(data.longitud_inicio),
        )

        if best_driver:
            trip_service.assign_trip_to_driver(db, viaje, best_driver)
            # Registrar relación en el grafo Neo4j para futuros matchings
            register_trip_relationship(neo4j, current_user.id_usuario, best_driver.id_conductor, viaje.id_viaje)
            logger.info(f"Viaje {viaje.id_viaje} asignado a conductor {best_driver.id_conductor}")
        else:
            db.commit()
            logger.info(f"Viaje {viaje.id_viaje} sin asignación (conductores sin posición registrada)")
    else:
        db.commit()
        logger.info(f"Viaje {viaje.id_viaje} sin asignación (sin conductores disponibles)")
    
    db.refresh(viaje)
    return TripResponse(
        id_viaje=viaje.id_viaje,
        id_usuario=viaje.id_usuario,
        id_conductor=viaje.id_conductor,
        latitud_inicio=viaje.latitud_inicio,
        longitud_inicio=viaje.longitud_inicio,
        latitud_destino=viaje.latitud_destino,
        longitud_destino=viaje.longitud_destino,
        distancia_km=viaje.distancia_km,
        tiempo_minutos=viaje.tiempo_minutos,
        estado=viaje.estado,
        fecha_hora=str(viaje.fecha_hora),
    )


@router.get(
    "/{trip_id}",
    response_model=TripResponse,
    summary="Ver detalles del viaje",
)
def get_trip(
    trip_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtiene detalles completos de un viaje."""
    viaje = db.get(Viaje, trip_id)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = _load_conductor(db, current_user)
    _authorize_trip_access(current_user, conductor, viaje)

    return TripResponse(
        id_viaje=viaje.id_viaje,
        id_usuario=viaje.id_usuario,
        id_conductor=viaje.id_conductor,
        latitud_inicio=viaje.latitud_inicio,
        longitud_inicio=viaje.longitud_inicio,
        latitud_destino=viaje.latitud_destino,
        longitud_destino=viaje.longitud_destino,
        distancia_km=viaje.distancia_km,
        tiempo_minutos=viaje.tiempo_minutos,
        estado=viaje.estado,
        fecha_hora=str(viaje.fecha_hora),
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
