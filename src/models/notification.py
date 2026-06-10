"""Modelo para notificaciones."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationCreate(BaseModel):
    """Crear notificación."""
    id_usuario: int
    titulo: str
    mensaje: str
    tipo: str  # 'viaje', 'pago', 'review', etc.
    id_referencia: Optional[int] = None  # ID del viaje, pago, etc.
    leida: bool = False


class NotificationResponse(BaseModel):
    """Respuesta de notificación."""
    id_notificacion: int
    id_usuario: int
    titulo: str
    mensaje: str
    tipo: str
    id_referencia: Optional[int] = None
    leida: bool
    fecha_creacion: datetime

    model_config = {"from_attributes": True}
