"""Schemas de viajes y tarifas."""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, field_validator

ALLOWED_TRIP_STATUSES = {"pendiente", "aceptado", "en_curso", "finalizado", "cancelado"}


class TripCreate(BaseModel):
    """Schema para crear un viaje."""
    latitud_inicio: Decimal
    longitud_inicio: Decimal
    latitud_destino: Decimal
    longitud_destino: Decimal
    distancia_km: Optional[Decimal] = None
    tiempo_minutos: Optional[int] = None

    @field_validator("latitud_inicio", "longitud_inicio", "latitud_destino", "longitud_destino")
    @classmethod
    def validar_coordenadas(cls, v: Decimal) -> Decimal:
        v_float = float(v)
        if v_float < -180 or v_float > 180:
            raise ValueError("Coordenada fuera de rango válido (-180 a 180)")
        return v


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


class TripResponse(BaseModel):
    """Respuesta completa de un viaje."""
    id_viaje: int
    id_usuario: int
    id_conductor: Optional[int] = None
    latitud_inicio: Decimal
    longitud_inicio: Decimal
    latitud_destino: Decimal
    longitud_destino: Decimal
    distancia_km: Optional[Decimal] = None
    tiempo_minutos: Optional[int] = None
    estado: str
    fecha_hora: Optional[str] = None

    model_config = {"from_attributes": True}
