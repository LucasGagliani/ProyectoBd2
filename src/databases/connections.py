"""
Instancias singleton de las conexiones a base de datos.
Compartidas entre todos los módulos de la app para evitar múltiples conexiones.
"""

import logging
from src.databases.sql_db import SQLDatabase
from src.databases.redis_db import RedisDatabase

logger = logging.getLogger(__name__)

_sql: SQLDatabase = None
_redis: RedisDatabase = None


def get_sql() -> SQLDatabase:
    """Retorna la instancia singleton de SQLDatabase."""
    global _sql
    if _sql is None:
        _sql = SQLDatabase()
    return _sql


def get_redis() -> RedisDatabase:
    """Retorna la instancia singleton de RedisDatabase."""
    global _redis
    if _redis is None:
        _redis = RedisDatabase()
    return _redis
