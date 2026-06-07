"""Schemas de reseñas mutuas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

REVIEW_TYPES = {"usuario_a_conductor", "conductor_a_usuario"}


class ReviewCreate(BaseModel):
    id_viaje: int
    calificacion: int = Field(ge=1, le=5)
    comentario: Optional[str] = None

    @field_validator("comentario")
    @classmethod
    def strip_comentario(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ReviewResponse(BaseModel):
    id_resena: int
    id_viaje: int
    id_autor: int
    id_receptor: int
    calificacion: int
    comentario: Optional[str] = None
    tipo: str
    fecha: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TripReviewStatusResponse(BaseModel):
    id_viaje: int
    usuario_a_conductor: bool
    conductor_a_usuario: bool
    mi_resena: bool
    puede_resenar: bool
