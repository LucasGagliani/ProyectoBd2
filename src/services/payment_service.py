"""Lógica de negocio para pagos."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session

from src.databases.schema import Pago

ALLOWED_PAYMENT_STATES = {"pendiente", "aprobado", "rechazado", "reembolsado"}


def calculate_payment_total(monto_base: Decimal, tarifa_adicional: Decimal) -> Decimal:
    total = monto_base + tarifa_adicional
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_payment_by_trip(db: Session, viaje_id: int) -> Optional[Pago]:
    return db.query(Pago).filter(Pago.id_viaje == viaje_id).first()


def get_payment(db: Session, payment_id: int) -> Optional[Pago]:
    return db.get(Pago, payment_id)


def create_payment(
    db: Session,
    viaje_id: int,
    monto_base: Decimal,
    tarifa_adicional: Decimal,
    metodo_pago: str,
    estado_transaccion: str = "pendiente",
) -> Pago:
    monto_total = calculate_payment_total(monto_base, tarifa_adicional)
    fecha_pago = None
    if estado_transaccion != "pendiente":
        fecha_pago = datetime.now(timezone.utc)

    pago = Pago(
        id_viaje=viaje_id,
        monto_base=monto_base,
        tarifa_adicional=tarifa_adicional,
        monto_total=monto_total,
        metodo_pago=metodo_pago,
        estado_transaccion=estado_transaccion,
        fecha_pago=fecha_pago,
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)
    return pago


def update_payment_status(db: Session, payment: Pago, new_status: str) -> Pago:
    if new_status not in ALLOWED_PAYMENT_STATES:
        raise ValueError("Estado de pago inválido")

    payment.estado_transaccion = new_status
    if new_status != "pendiente":
        payment.fecha_pago = datetime.now(timezone.utc)
    db.commit()
    db.refresh(payment)
    return payment
