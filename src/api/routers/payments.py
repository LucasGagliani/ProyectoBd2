"""Router de pagos."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, get_current_user
from src.databases.schema import Conductor, Pago, Viaje
from src.models.payment import PaymentCreateRequest, PaymentResponse, PaymentStatusUpdate
from src.services import payment_service, trip_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _authorize_payment_access(current_user, db, viaje: Viaje) -> None:
    if viaje.id_usuario == current_user.id_usuario:
        return
    conductor = db.query(Conductor).filter(Conductor.id_usuario == current_user.id_usuario).first()
    if conductor is not None and viaje.id_conductor == conductor.id_conductor:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tenés permisos para ver o modificar este pago.",
    )


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear pago para un viaje finalizado",
)
def create_payment(
    data: PaymentCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    viaje = db.get(Viaje, data.id_viaje)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    if viaje.id_usuario != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el pasajero puede registrar el pago del viaje.",
        )

    if viaje.estado != "finalizado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se puede crear el pago una vez que el viaje está finalizado.",
        )

    existing_payment = payment_service.get_payment_by_trip(db, data.id_viaje)
    if existing_payment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un pago registrado para este viaje.",
        )

    monto_base = trip_service.estimate_trip_fare(
        viaje.distancia_km,
        viaje.tiempo_minutos,
    )

    pago = payment_service.create_payment(
        db=db,
        viaje_id=data.id_viaje,
        monto_base=monto_base,
        tarifa_adicional=data.tarifa_adicional,
        metodo_pago=data.metodo_pago,
        estado_transaccion="aprobado",
    )

    logger.info(f"Pago creado: id_pago={pago.id_pago} viaje_id={pago.id_viaje}")
    return pago


@router.get(
    "/trip/{trip_id}",
    response_model=PaymentResponse,
    summary="Obtener pago por viaje",
)
def get_payment_by_trip(
    trip_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    viaje = db.get(Viaje, trip_id)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    _authorize_payment_access(current_user, db, viaje)

    pago = payment_service.get_payment_by_trip(db, trip_id)
    if pago is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Este viaje aún no tiene pago registrado")
    return pago


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Obtener pago por ID",
)
def get_payment(
    payment_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pago = payment_service.get_payment(db, payment_id)
    if pago is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")

    viaje = db.get(Viaje, pago.id_viaje)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    _authorize_payment_access(current_user, db, viaje)
    return pago


@router.patch(
    "/{payment_id}/status",
    response_model=PaymentResponse,
    summary="Actualizar estado de la transacción de pago",
)
def update_payment_status(
    payment_id: int,
    data: PaymentStatusUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from src.services import notification_service
    
    pago = payment_service.get_payment(db, payment_id)
    if pago is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")

    viaje = db.get(Viaje, pago.id_viaje)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = db.query(Conductor).filter(Conductor.id_usuario == current_user.id_usuario).first()
    
    # Solo el conductor asignado puede confirmar pagos
    # (el pasajero crea el pago inicial, pero el conductor lo aprueba/rechaza)
    if conductor is None or viaje.id_conductor != conductor.id_conductor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el conductor asignado puede actualizar el estado del pago.",
        )
    
    # Validación adicional: no permitir cambio si el pago ya está finalizado
    if pago.estado_transaccion == "reembolsado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar un pago que ya ha sido reembolsado.",
        )

    old_status = pago.estado_transaccion
    try:
        pago = payment_service.update_payment_status(db, pago, data.estado_transaccion)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    # Crear notificación para el pasajero con el nuevo estado
    try:
        status_messages = {
            "aprobado": "✓ Tu pago ha sido confirmado.",
            "rechazado": "✗ Tu pago ha sido rechazado.",
            "reembolsado": "💰 Reembolso procesado.",
        }
        mensaje = status_messages.get(data.estado_transaccion, f"Estado: {data.estado_transaccion}")
        
        notification_service.create_notification(
            db=db,
            id_usuario=viaje.id_usuario,
            titulo="Cambio en estado de pago",
            mensaje=mensaje,
            tipo="pago",
            id_referencia=pago.id_pago,
        )
    except Exception as e:
        logger.warning(f"Error creating payment notification: {e}")

    logger.info(f"Estado de pago actualizado: id_pago={pago.id_pago} {old_status}→{pago.estado_transaccion} (conductor={conductor.id_conductor})")
    return pago
