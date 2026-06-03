"""Lógica de negocio para viajes y tarifas."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple
import math

from sqlalchemy.orm import Session
from src.databases.schema import Viaje, Conductor

# Para compatibilidad con Python 3.9+
try:
    from typing import Tuple as TupleType
except ImportError:
    TupleType = tuple

BASE_FARE = Decimal("150.00")
COST_PER_KM = Decimal("120.00")
COST_PER_MIN = Decimal("25.00")
CACHE_TTL_SECONDS = 3600

ALLOWED_TRANSITIONS = {
    "pendiente": {"aceptado", "cancelado"},
    "aceptado": {"en_curso", "cancelado"},
    "en_curso": {"finalizado", "cancelado"},
    "finalizado": set(),
    "cancelado": set(),
}


def estimate_trip_fare(distancia_km: Optional[Decimal], tiempo_minutos: Optional[int]) -> Decimal:
    distancia = Decimal(distancia_km or 0)
    minutos = Decimal(tiempo_minutos or 0)
    total = BASE_FARE + distancia * COST_PER_KM + minutos * COST_PER_MIN
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_payment_total(monto_base: Decimal, tarifa_adicional: Decimal) -> Decimal:
    total = monto_base + tarifa_adicional
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def is_valid_status_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def get_cache_key_for_trip_status(viaje_id: int) -> str:
    return f"trip:{viaje_id}:status"


def cache_trip_status(redis_client, viaje_id: int, estado: str) -> None:
    if redis_client is None:
        return
    redis_client.set(get_cache_key_for_trip_status(viaje_id), estado, ex=CACHE_TTL_SECONDS)


def get_cached_trip_status(redis_client, viaje_id: int) -> Optional[str]:
    if redis_client is None:
        return None
    return redis_client.get(get_cache_key_for_trip_status(viaje_id))


def get_trip_status(db, redis_client, viaje_id: int) -> Tuple[str, bool]:
    cached = get_cached_trip_status(redis_client, viaje_id)
    if cached:
        return cached, True

    viaje = db.get(Viaje, viaje_id)
    if viaje is None:
        raise ValueError("Viaje no encontrado")

    cache_trip_status(redis_client, viaje_id, viaje.estado)
    return viaje.estado, False


def get_conductor_position_key(conductor_id: int) -> str:
    """Genera la clave Redis para la posición de un conductor."""
    return f"conductor:{conductor_id}:posicion"


def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula distancia euclidiana entre dos puntos (aproximación simple).
    Para distancias cortas en coordenadas geográficas, es suficiente.
    """
    lat_diff = float(lat2) - float(lat1)
    lon_diff = float(lon2) - float(lon1)
    return math.sqrt(lat_diff ** 2 + lon_diff ** 2)


def find_available_drivers(db: Session) -> List[Conductor]:
    """
    Obtiene lista de conductores disponibles (estado='disponible').
    Valida que no tengan viajes activos.
    """
    # Conductores con estado disponible
    drivers = db.query(Conductor).filter(Conductor.estado == "disponible").all()
    
    # Filtrar: solo conductores sin viajes activos
    active_states = {"pendiente", "aceptado", "en_curso"}
    available = []
    for driver in drivers:
        active_trip = (
            db.query(Viaje)
            .filter(
                Viaje.id_conductor == driver.id_conductor,
                Viaje.estado.in_(active_states)
            )
            .first()
        )
        if active_trip is None:
            available.append(driver)
    
    return available


def find_nearest_driver(
    db: Session,
    redis_client,
    available_drivers: List[Conductor],
    usuario_lat: float,
    usuario_lon: float,
) -> Optional[Conductor]:
    """
    Encuentra el conductor disponible más cercano al usuario.
    Usa posición actual del conductor de Redis (latitud_actual, longitud_actual en Conductor).
    """
    if not available_drivers:
        return None
    
    nearest_driver = None
    min_distance = float("inf")
    
    for driver in available_drivers:
        # Obtener posición actual del conductor
        lat = driver.latitud_actual
        lon = driver.longitud_actual
        
        if lat is None or lon is None:
            continue
        
        # Calcular distancia
        distance = _calculate_distance(usuario_lat, usuario_lon, lat, lon)
        
        if distance < min_distance:
            min_distance = distance
            nearest_driver = driver
    
    return nearest_driver


def assign_trip_to_driver(
    db: Session,
    viaje: Viaje,
    conductor: Conductor,
) -> None:
    """
    Asigna un viaje a un conductor.
    - Cambia id_conductor del viaje
    - Cambia estado a 'aceptado'
    - Cambia estado del conductor a 'ocupado'
    """
    viaje.id_conductor = conductor.id_conductor
    viaje.estado = "aceptado"
    conductor.estado = "ocupado"
    
    db.commit()
    db.refresh(viaje)
    db.refresh(conductor)


def has_active_trip(db: Session, conductor_id: int) -> bool:
    """
    Verifica si un conductor tiene un viaje activo.
    Viajes activos: pendiente, aceptado, en_curso
    """
    active_states = {"pendiente", "aceptado", "en_curso"}
    return (
        db.query(Viaje)
        .filter(
            Viaje.id_conductor == conductor_id,
            Viaje.estado.in_(active_states)
        )
        .first()
    ) is not None
