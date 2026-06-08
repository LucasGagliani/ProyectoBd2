"""
Servicio de Neo4j — grafo de relaciones entre usuarios y conductores.

Modelo del grafo:
  Nodos:  (Usuario {id_usuario, nombre})
          (Conductor {id_conductor, nombre})
  Aristas: (Usuario)-[:REALIZO_VIAJE {id_viaje, fecha}]->(Conductor)

Uso en el flujo de viajes:
  - Al registrar usuario/conductor → crear nodo en Neo4j
  - Al asignar un viaje → crear relación REALIZO_VIAJE
  - Al buscar conductor → priorizar conductores con historial con ese usuario
"""

import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


def sync_usuario_node(neo4j, usuario_id: int, nombre: str) -> None:
    """
    Crea o actualiza el nodo Usuario en Neo4j.
    Usa MERGE para no duplicar si ya existe.
    """
    if neo4j is None:
        return
    try:
        query = """
        MERGE (u:Usuario {id_usuario: $id_usuario})
        SET u.nombre = $nombre
        """
        neo4j.execute_query(query, {"id_usuario": usuario_id, "nombre": nombre}, mode="w")
        logger.debug(f"Nodo Usuario sincronizado: id={usuario_id}")
    except Exception as e:
        logger.warning(f"No se pudo sincronizar nodo Usuario {usuario_id} en Neo4j: {e}")


def sync_conductor_node(neo4j, conductor_id: int, nombre: str) -> None:
    """
    Crea o actualiza el nodo Conductor en Neo4j.
    Usa MERGE para no duplicar si ya existe.
    """
    if neo4j is None:
        return
    try:
        query = """
        MERGE (c:Conductor {id_conductor: $id_conductor})
        SET c.nombre = $nombre
        """
        neo4j.execute_query(query, {"id_conductor": conductor_id, "nombre": nombre}, mode="w")
        logger.debug(f"Nodo Conductor sincronizado: id={conductor_id}")
    except Exception as e:
        logger.warning(f"No se pudo sincronizar nodo Conductor {conductor_id} en Neo4j: {e}")


def register_trip_relationship(
    neo4j,
    usuario_id: int,
    conductor_id: int,
    viaje_id: int,
    usuario_nombre: str = "",
    conductor_nombre: str = "",
) -> None:
    """
    Registra una relación REALIZO_VIAJE entre Usuario y Conductor en Neo4j.
    Usa MERGE + SET para que los nodos siempre tengan nombre,
    incluso si fueron creados por primera vez aquí.
    """
    if neo4j is None:
        return
    try:
        query = """
        MERGE (u:Usuario {id_usuario: $id_usuario})
        SET u.nombre = $usuario_nombre
        MERGE (c:Conductor {id_conductor: $id_conductor})
        SET c.nombre = $conductor_nombre
        CREATE (u)-[:REALIZO_VIAJE {id_viaje: $id_viaje, fecha: datetime()}]->(c)
        """
        neo4j.execute_query(query, {
            "id_usuario": usuario_id,
            "id_conductor": conductor_id,
            "id_viaje": viaje_id,
            "usuario_nombre": usuario_nombre,
            "conductor_nombre": conductor_nombre,
        }, mode="w")
        logger.debug(f"Relación REALIZO_VIAJE registrada: usuario={usuario_id} ({usuario_nombre}) → conductor={conductor_id} ({conductor_nombre})")
    except Exception as e:
        logger.warning(f"No se pudo registrar relación de viaje en Neo4j: {e}")


def find_preferred_conductors(neo4j, usuario_id: int, available_conductor_ids: List[int]) -> List[int]:
    """
    Busca en el grafo conductores con los que este usuario ya viajó antes,
    filtrando solo los que están actualmente disponibles.

    Retorna lista de id_conductor ordenada por cantidad de viajes previos (más frecuente primero).
    Si Neo4j no está disponible o no hay historial, retorna lista vacía
    y el sistema cae al matching por posición.
    """
    if neo4j is None or not available_conductor_ids:
        return []
    try:
        query = """
        MATCH (u:Usuario {id_usuario: $id_usuario})-[:REALIZO_VIAJE]->(c:Conductor)
        WHERE c.id_conductor IN $available_ids
        RETURN c.id_conductor AS id_conductor, count(*) AS viajes
        ORDER BY viajes DESC
        """
        results = neo4j.execute_query(query, {
            "id_usuario": usuario_id,
            "available_ids": available_conductor_ids,
        }, mode="r")

        preferred = [r["id_conductor"] for r in results]
        if preferred:
            logger.info(f"Neo4j: conductores preferidos para usuario {usuario_id}: {preferred}")
        return preferred
    except Exception as e:
        logger.warning(f"Error consultando Neo4j para matching preferencial: {e}")
        return []
