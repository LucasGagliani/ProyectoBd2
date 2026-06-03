"""Schemas de pagos y transacciones."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from typing import Optional

ALLOWED_PAYMENT_STATES = {"pendiente", "aprobado", "rechazado", "reembolsado"}


class PaymentCreateRequest(BaseModel):
    id_viaje: int
    monto_base: Decimal = Field(gt=0)
    tarifa_adicional: Decimal = Field(default=0)
    metodo_pago: str
    estado_transaccion: Optional[str] = "pendiente"

    @field_validator("metodo_pago")
    @classmethod
    def metodo_pago_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El método de pago no puede estar vacío")
        return value.strip()

    @field_validator("estado_transaccion")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return "pendiente"
        normalized = value.strip().lower()
        if normalized not in ALLOWED_PAYMENT_STATES:
            raise ValueError(
                f"Estado de pago inválido. Valores permitidos: {', '.join(sorted(ALLOWED_PAYMENT_STATES))}"
            )
        return normalized


class PaymentStatusUpdate(BaseModel):
    estado_transaccion: str

    @field_validator("estado_transaccion")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_PAYMENT_STATES:
            raise ValueError(
                f"Estado de pago inválido. Valores permitidos: {', '.join(sorted(ALLOWED_PAYMENT_STATES))}"
            )
        return normalized


class PaymentResponse(BaseModel):
    id_pago: int
    id_viaje: int
    monto_base: Decimal
    tarifa_adicional: Decimal
    monto_total: Decimal
    metodo_pago: str
    estado_transaccion: str
    fecha_pago: Optional[datetime] = None

    model_config = {"from_attributes": True}
