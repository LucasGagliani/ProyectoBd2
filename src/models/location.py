"""Schemas de GPS / ubicaciones."""

from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal


class LocationUpdate(BaseModel):
    """El conductor envía su posición actual."""
    id_viaje: Optional[int] = None        # None si no está en viaje activo
    latitud: Decimal
    longitud: Decimal
    velocidad_estimada: Optional[Decimal] = None

    @field_validator("latitud", "longitud")
    @classmethod
    def validar_coordenadas(cls, v: Decimal) -> Decimal:
        if float(v) < -180 or float(v) > 180:
            raise ValueError("Coordenada fuera de rango (-180 a 180)")
        return v


class LocationResponse(BaseModel):
    id_conductor: int
    id_viaje: Optional[int] = None
    latitud: Decimal
    longitud: Decimal
    velocidad_estimada: Optional[Decimal] = None
    timestamp: Optional[str] = None


class LocationHistoryResponse(BaseModel):
    id_viaje: int
    registros: list
