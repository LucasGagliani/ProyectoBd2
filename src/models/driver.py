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


class DriverVehicleCreate(BaseModel):
    """Schema para crear un vehículo."""
    marca: str
    modelo: str
    anio: int
    nro_placa: str
    color: Optional[str] = None
    tipo_vehiculo: Optional[str] = None
    capacidad_pasajeros: Optional[int] = None

    @field_validator("marca", "modelo")
    @classmethod
    def campos_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v.strip()

    @field_validator("nro_placa")
    @classmethod
    def placa_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("La placa no puede estar vacía")
        return v.strip().upper()

    @field_validator("anio")
    @classmethod
    def anio_valido(cls, v: int) -> int:
        if v < 1900 or v > 2100:
            raise ValueError("El año debe ser realista (1900-2100)")
        return v


class DriverVehicleUpdate(BaseModel):
    """Schema para actualizar un vehículo."""
    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[int] = None
    nro_placa: Optional[str] = None
    color: Optional[str] = None
    tipo_vehiculo: Optional[str] = None
    capacidad_pasajeros: Optional[int] = None

    @field_validator("nro_placa")
    @classmethod
    def placa_uppercase(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().upper()
        return v


class DriverVehicleResponse(BaseModel):
    """Schema para responder datos del vehículo."""
    id_vehiculo: int
    id_conductor: int
    marca: str
    modelo: str
    anio: int
    nro_placa: str
    color: Optional[str] = None
    tipo_vehiculo: Optional[str] = None
    capacidad_pasajeros: Optional[int] = None

    model_config = {"from_attributes": True}
