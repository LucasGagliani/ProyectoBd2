"""Schemas de viajes y tarifas."""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, field_validator

ALLOWED_TRIP_STATUSES = {"pendiente", "aceptado", "en_curso", "finalizado", "cancelado"}


class TripStatusUpdate(BaseModel):
    estado: str

    @field_validator("estado")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_TRIP_STATUSES:
            raise ValueError(
                f"Estado inválido. Valores permitidos: {', '.join(sorted(ALLOWED_TRIP_STATUSES))}"
            )
        return normalized


class TripStatusResponse(BaseModel):
    id_viaje: int
    estado: str
    cached: bool = False

    model_config = {"from_attributes": True}


class TripFareResponse(BaseModel):
    id_viaje: int
    distancia_km: Optional[Decimal] = None
    tiempo_minutos: Optional[int] = None
    tarifa_base: Decimal
    tarifa_adicional: Decimal
    monto_total: Decimal

    model_config = {"from_attributes": True}
