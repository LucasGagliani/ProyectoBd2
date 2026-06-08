"""
Servicio de ubicaciones GPS.

Distribución de DBs según el plan:
  - Cassandra  → historial de ubicaciones del viaje (serie temporal, alta escritura)
  - Redis      → posición actual del conductor (tiempo real, acceso instantáneo)
  - PostgreSQL → sincroniza latitud_actual/longitud_actual en el modelo Conductor
"""

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

logger = logging.getLogger(__name__)

REDIS_POSITION_PREFIX = "conductor:posicion:"


# ------------------------------------------------------------------
# Redis — posición actual del conductor
# ------------------------------------------------------------------

def get_redis_position_key(conductor_id: int) -> str:
    return f"{REDIS_POSITION_PREFIX}{conductor_id}"


def update_conductor_position_redis(redis, conductor_id: int, lat: float, lon: float) -> None:
    """Guarda la posición actual del conductor en Redis (TTL 1 hora)."""
    if redis is None:
        return
    try:
        key = get_redis_position_key(conductor_id)
        value = json.dumps({"lat": lat, "lon": lon})
        redis.set(key, value, ex=3600)
    except Exception as e:
        logger.warning(f"No se pudo actualizar posición en Redis: {e}")


def get_conductor_position_redis(redis, conductor_id: int) -> Optional[dict]:
    """Lee la posición actual del conductor desde Redis."""
    if redis is None:
        return None
    try:
        key = get_redis_position_key(conductor_id)
        value = redis.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Error leyendo posición de Redis: {e}")
    return None


# ------------------------------------------------------------------
# Cassandra — historial GPS
# ------------------------------------------------------------------

def save_location_to_cassandra(cassandra, id_viaje: int, id_conductor: int,
                                lat: float, lon: float, velocidad: Optional[float]) -> None:
    """
    Guarda un punto GPS en Astra DB (Cassandra) como registro de serie temporal.
    Usa el wrapper AstraDatabase que expone insert_location().
    """
    if cassandra is None:
        logger.warning("Astra/Cassandra no disponible — punto GPS no guardado en historial")
        return
    try:
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id_viaje": id_viaje,
            "timestamp": now,
            "id_conductor": id_conductor,
            "latitud": lat,
            "longitud": lon,
            "velocidad_estimada": velocidad or 0.0,
        }
        cassandra.insert_location(doc)
    except Exception as e:
        logger.warning(f"Error guardando GPS en Astra: {e}")


def get_trip_gps_history(cassandra, id_viaje: int) -> List[dict]:
    """
    Recupera el historial GPS de un viaje desde Astra DB (Cassandra).
    Retorna los puntos ordenados por timestamp descendente (más reciente primero).
    """
    if cassandra is None:
        return []
    try:
        return cassandra.get_trip_locations(id_viaje)
    except Exception as e:
        logger.warning(f"Error leyendo historial GPS de Astra: {e}")
        return []
