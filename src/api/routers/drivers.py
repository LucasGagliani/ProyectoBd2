"""
Router de conductores.

Endpoints:
  GET   /drivers/me                      — perfil completo del conductor autenticado
  PUT   /drivers/me                      — actualizar nro_licencia
  PATCH /drivers/me/estado               — cambiar estado (disponible / ocupado / inactivo)
  GET   /drivers/me/vehicles             — listar vehículos del conductor
  POST  /drivers/me/vehicles             — crear vehículo
  PUT   /drivers/me/vehicles/{id}        — actualizar vehículo
  DELETE /drivers/me/vehicles/{id}       — eliminar vehículo
"""

import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, get_current_user, get_current_conductor
from src.databases.schema import Usuario, Conductor, Vehiculo
from src.models.driver import (
    DriverResponse, DriverUpdate, DriverStatusUpdate, DriverWithUserResponse,
    DriverVehicleCreate, DriverVehicleUpdate, DriverVehicleResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/me",
    response_model=DriverWithUserResponse,
    summary="Ver mi perfil de conductor",
)
def get_my_driver_profile(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
):
    """
    Retorna el perfil completo del conductor: datos personales + datos del conductor.
    Solo accesible con token de conductor.
    """
    return DriverWithUserResponse(
        id_conductor=conductor.id_conductor,
        id_usuario=current_user.id_usuario,
        nombre=current_user.nombre,
        email=current_user.email,
        telefono=current_user.telefono,
        nro_licencia=conductor.nro_licencia,
        estado=conductor.estado,
        calificacion_promedio=conductor.calificacion_promedio,
        latitud_actual=conductor.latitud_actual,
        longitud_actual=conductor.longitud_actual,
    )


@router.put(
    "/me",
    response_model=DriverResponse,
    summary="Actualizar perfil de conductor",
)
def update_my_driver_profile(
    data: DriverUpdate,
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Actualiza el número de licencia del conductor.
    Solo se modifican los campos enviados.
    """
    if data.nro_licencia is not None:
        # Verificar que la nueva licencia no esté en uso
        existing = (
            db.query(Conductor)
            .filter(
                Conductor.nro_licencia == data.nro_licencia,
                Conductor.id_conductor != conductor.id_conductor,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El número de licencia ya está en uso por otro conductor",
            )
        conductor.nro_licencia = data.nro_licencia.strip()

    db.commit()
    db.refresh(conductor)

    logger.info(f"Perfil conductor actualizado: id={conductor.id_conductor}")
    return conductor


@router.patch(
    "/me/estado",
    response_model=DriverResponse,
    summary="Cambiar estado del conductor",
)
def update_driver_status(
    data: DriverStatusUpdate,
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Cambia el estado del conductor.
    - disponible: puede recibir viajes
    - ocupado:    tiene un viaje activo
    - inactivo:   desconectado de la plataforma
    """
    conductor.estado = data.estado
    db.commit()
    db.refresh(conductor)

    logger.info(f"Estado conductor actualizado: id={conductor.id_conductor} -> {data.estado}")
    return conductor


# ==================== UBICACIÓN ====================

@router.patch(
    "/me/location",
    response_model=DriverResponse,
    summary="Actualizar posición GPS del conductor",
)
def update_driver_location(
    data: dict,
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
    db: Annotated[Session, Depends(get_db)],
):
    """Actualiza la posición actual del conductor para el sistema de matching."""
    lat = data.get("latitud")
    lon = data.get("longitud")
    if lat is None or lon is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Se requieren latitud y longitud")
    conductor.latitud_actual = lat
    conductor.longitud_actual = lon
    db.commit()
    db.refresh(conductor)
    logger.info(f"Ubicación conductor actualizada: id={conductor.id_conductor} -> ({lat}, {lon})")
    return conductor


# ==================== VEHÍCULOS ====================

@router.get(
    "/me/vehicles",
    response_model=List[DriverVehicleResponse],
    summary="Listar mis vehículos",
)
def get_my_vehicles(
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retorna lista de vehículos del conductor autenticado."""
    vehicles = (
        db.query(Vehiculo)
        .filter(Vehiculo.id_conductor == conductor.id_conductor)
        .all()
    )
    return vehicles


@router.post(
    "/me/vehicles",
    response_model=DriverVehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo vehículo",
)
def create_vehicle(
    data: DriverVehicleCreate,
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Crea un nuevo vehículo para el conductor autenticado.
    La placa debe ser única en el sistema.
    """
    # Verificar que la placa no esté en uso
    existing_placa = (
        db.query(Vehiculo)
        .filter(Vehiculo.nro_placa == data.nro_placa)
        .first()
    )
    if existing_placa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La placa ya está registrada en el sistema",
        )

    vehicle = Vehiculo(
        id_conductor=conductor.id_conductor,
        marca=data.marca,
        modelo=data.modelo,
        anio=data.anio,
        nro_placa=data.nro_placa,
        color=data.color,
        tipo_vehiculo=data.tipo_vehiculo,
        capacidad_pasajeros=data.capacidad_pasajeros,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    logger.info(f"Vehículo creado: id={vehicle.id_vehiculo}, conductor={conductor.id_conductor}")
    return vehicle


@router.put(
    "/me/vehicles/{vehicle_id}",
    response_model=DriverVehicleResponse,
    summary="Actualizar vehículo",
)
def update_vehicle(
    vehicle_id: int,
    data: DriverVehicleUpdate,
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Actualiza datos del vehículo.
    Solo el conductor dueño del vehículo puede actualizarlo.
    """
    vehicle = db.get(Vehiculo, vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )

    if vehicle.id_conductor != conductor.id_conductor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este vehículo",
        )

    # Validar que la nueva placa no esté en uso (si se intenta cambiar)
    if data.nro_placa is not None and data.nro_placa != vehicle.nro_placa:
        existing_placa = (
            db.query(Vehiculo)
            .filter(
                Vehiculo.nro_placa == data.nro_placa,
                Vehiculo.id_vehiculo != vehicle_id,
            )
            .first()
        )
        if existing_placa:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La nueva placa ya está registrada en el sistema",
            )

    # Actualizar solo los campos no nulos
    if data.marca is not None:
        vehicle.marca = data.marca
    if data.modelo is not None:
        vehicle.modelo = data.modelo
    if data.anio is not None:
        vehicle.anio = data.anio
    if data.nro_placa is not None:
        vehicle.nro_placa = data.nro_placa
    if data.color is not None:
        vehicle.color = data.color
    if data.tipo_vehiculo is not None:
        vehicle.tipo_vehiculo = data.tipo_vehiculo
    if data.capacidad_pasajeros is not None:
        vehicle.capacidad_pasajeros = data.capacidad_pasajeros

    db.commit()
    db.refresh(vehicle)

    logger.info(f"Vehículo actualizado: id={vehicle.id_vehiculo}")
    return vehicle


@router.delete(
    "/me/vehicles/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar vehículo",
)
def delete_vehicle(
    vehicle_id: int,
    conductor: Annotated[Conductor, Depends(get_current_conductor)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Elimina un vehículo.
    Solo el conductor dueño del vehículo puede eliminarlo.
    """
    vehicle = db.get(Vehiculo, vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )

    if vehicle.id_conductor != conductor.id_conductor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este vehículo",
        )

    db.delete(vehicle)
    db.commit()

    logger.info(f"Vehículo eliminado: id={vehicle.id_vehiculo}")

