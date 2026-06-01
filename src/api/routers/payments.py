"""Router de pagos."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, get_current_user
from src.databases.schema import Conductor, Pago, Viaje
from src.models.payment import PaymentCreateRequest, PaymentResponse, PaymentStatusUpdate
from src.services import payment_service

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

    _authorize_payment_access(current_user, viaje)

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

    pago = payment_service.create_payment(
        db=db,
        viaje_id=data.id_viaje,
        monto_base=data.monto_base,
        tarifa_adicional=data.tarifa_adicional,
        metodo_pago=data.metodo_pago,
        estado_transaccion=data.estado_transaccion,
    )

    logger.info(f"Pago creado: id_pago={pago.id_pago} viaje_id={pago.id_viaje}")
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
    pago = payment_service.get_payment(db, payment_id)
    if pago is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")

    viaje = db.get(Viaje, pago.id_viaje)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    _authorize_payment_access(current_user, db, viaje)

    try:
        pago = payment_service.update_payment_status(db, pago, data.estado_transaccion)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    logger.info(f"Estado de pago actualizado: id_pago={pago.id_pago} -> {pago.estado_transaccion}")
    return pago
