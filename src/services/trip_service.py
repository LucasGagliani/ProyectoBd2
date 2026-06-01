"""Lógica de negocio para viajes y tarifas."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from src.databases.schema import Viaje

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
    redis_client.set(get_cache_key_for_trip_status(viaje_id), estado, ttl=CACHE_TTL_SECONDS)


def get_cached_trip_status(redis_client, viaje_id: int) -> Optional[str]:
    if redis_client is None:
        return None
    return redis_client.get(get_cache_key_for_trip_status(viaje_id))


def get_trip_status(db, redis_client, viaje_id: int) -> tuple[str, bool]:
    cached = get_cached_trip_status(redis_client, viaje_id)
    if cached:
        return cached, True

    viaje = db.get(Viaje, viaje_id)
    if viaje is None:
        raise ValueError("Viaje no encontrado")

    cache_trip_status(redis_client, viaje_id, viaje.estado)
    return viaje.estado, False
