"""
Instancias singleton de las conexiones a base de datos.
Compartidas entre todos los módulos de la app para evitar múltiples conexiones.
"""

import logging
from typing import Optional
from src.databases.sql_db import SQLDatabase
from src.databases.redis_db import RedisDatabase

logger = logging.getLogger(__name__)

_sql: SQLDatabase = None
_redis: RedisDatabase = None
_neo4j = None
_neo4j_initialized: bool = False
_mongo = None
_mongo_initialized: bool = False
_cassandra = None
_cassandra_initialized: bool = False


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


def get_mongo():
    """
    Retorna la instancia singleton de MongoDBDatabase.
    Retorna None si no está disponible — graceful degradation.
    """
    global _mongo, _mongo_initialized
    if _mongo_initialized:
        return _mongo
    _mongo_initialized = True
    try:
        from src.databases.mongodb_db import MongoDBDatabase
        _mongo = MongoDBDatabase()
        logger.info("MongoDB conectado")
    except Exception as e:
        logger.warning(f"MongoDB no disponible: {e}")
        _mongo = None
    return _mongo


def get_cassandra():
    """
    Retorna la instancia singleton de AstraDatabase (DataStax Astra / Cassandra cloud).
    Si ASTRA_TOKEN está configurado usa Astra DB, sino intenta cassandra-driver local.
    Retorna None si no está disponible — graceful degradation.
    """
    global _cassandra, _cassandra_initialized
    if _cassandra_initialized:
        return _cassandra
    _cassandra_initialized = True
    try:
        from src.config import settings
        if settings.ASTRA_TOKEN and settings.ASTRA_API_ENDPOINT:
            from src.databases.astra_db import AstraDatabase
            _cassandra = AstraDatabase()
            logger.info("Astra DB (Cassandra cloud) conectado")
        else:
            from src.databases.cassandra_db import CassandraDatabase
            _cassandra = CassandraDatabase()
            logger.info("Cassandra local conectado")
    except Exception as e:
        logger.warning(f"Cassandra/Astra no disponible: {e}")
        _cassandra = None
    return _cassandra


def get_neo4j(  ):
    """
    Retorna la instancia singleton de Neo4jDatabase.
    Si Neo4j no está disponible o las credenciales no están configuradas,
    retorna None y la app sigue funcionando sin el grafo.
    """
    global _neo4j, _neo4j_initialized
    if _neo4j_initialized:
        return _neo4j
    _neo4j_initialized = True
    try:
        from src.databases.neo4j_db import Neo4jDatabase
        _neo4j = Neo4jDatabase()
        logger.info("Neo4j conectado")
    except Exception as e:
        logger.warning(f"Neo4j no disponible — operando sin grafo de relaciones: {e}")
        _neo4j = None
    return _neo4j
