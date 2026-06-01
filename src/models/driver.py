"""Schemas de Conductor."""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from decimal import Decimal


class DriverCreate(BaseModel):
    # Datos de usuario base
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None
    contrasena: str
    # Datos específicos del conductor
    nro_licencia: str

    @field_validator("contrasena")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar los 72 caracteres")
        return v

    @field_validator("nro_licencia")
    @classmethod
    def licencia_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El número de licencia no puede estar vacío")
        return v.strip()


class DriverUpdate(BaseModel):
    nro_licencia: Optional[str] = None


class DriverStatusUpdate(BaseModel):
    estado: str

    @field_validator("estado")
    @classmethod
    def estado_valido(cls, v: str) -> str:
        estados_validos = {"disponible", "ocupado", "inactivo"}
        if v not in estados_validos:
            raise ValueError(f"Estado inválido. Opciones: {estados_validos}")
        return v


class DriverResponse(BaseModel):
    id_conductor: int
    id_usuario: int
    nro_licencia: str
    estado: Optional[str] = None
    calificacion_promedio: Optional[Decimal] = None
    latitud_actual: Optional[Decimal] = None
    longitud_actual: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class DriverWithUserResponse(BaseModel):
    """Perfil completo del conductor incluyendo datos del usuario."""
    id_conductor: int
    id_usuario: int
    nombre: str
    email: str
    telefono: Optional[str] = None
    nro_licencia: str
    estado: Optional[str] = None
    calificacion_promedio: Optional[Decimal] = None
    latitud_actual: Optional[Decimal] = None
    longitud_actual: Optional[Decimal] = None
