"""Schemas de Usuario (pasajero)."""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class UserCreate(BaseModel):
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None
    contrasena: str

    @field_validator("contrasena")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar los 72 caracteres")
        return v

    @field_validator("nombre")
    @classmethod
    def nombre_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()


class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None


class UserResponse(BaseModel):
    id_usuario: int
    nombre: str
    email: str
    telefono: Optional[str] = None
    calificacion_promedio: Optional[Decimal] = None
    fecha_registro: Optional[datetime] = None

    model_config = {"from_attributes": True}
