"""
DataStax Astra DB wrapper — usa astrapy (Data API).
Reemplaza cassandra-driver para conexiones cloud a Astra.

Rol en el sistema: almacenamiento de series temporales GPS (RF-10).
Colección: ubicaciones_viaje
"""

import logging
from typing import List, Optional

from src.config import settings

logger = logging.getLogger(__name__)

GPS_COLLECTION = "ubicaciones_viaje"


class AstraDatabase:
    """Wrapper sobre DataStax Astra DB usando la Data API (astrapy)."""

    def __init__(self):
        self.db = None
        self._connect()

    def _connect(self):
        try:
            from astrapy import DataAPIClient

            client = DataAPIClient()
            self.db = client.get_database(
                settings.ASTRA_API_ENDPOINT,
                token=settings.ASTRA_TOKEN,
                keyspace=settings.ASTRA_KEYSPACE,
            )
            # Verificar conexión
            self.db.list_collection_names()
            # Crear colección GPS si no existe
            self._init_collections()
            logger.info(f"Connected to Astra DB: {settings.ASTRA_API_ENDPOINT}")
        except Exception as e:
            logger.error(f"Failed to connect to Astra DB: {e}")
            raise

    def _init_collections(self):
        """Crea la colección de GPS si no existe."""
        existing = self.db.list_collection_names()
        if GPS_COLLECTION not in existing:
            self.db.create_collection(GPS_COLLECTION)
            logger.info(f"Colección '{GPS_COLLECTION}' creada en Astra DB")

    def insert_location(self, doc: dict) -> bool:
        """Inserta un punto GPS en la colección."""
        try:
            collection = self.db.get_collection(GPS_COLLECTION)
            collection.insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Error insertando en Astra: {e}")
            return False

    def get_trip_locations(self, id_viaje: int) -> List[dict]:
        """Recupera el historial GPS de un viaje ordenado por timestamp desc."""
        try:
            collection = self.db.get_collection(GPS_COLLECTION)
            cursor = collection.find(
                {"id_viaje": id_viaje},
                sort={"timestamp": -1},
            )
            results = []
            for doc in cursor:
                doc.pop("_id", None)
                results.append(doc)
            return results
        except Exception as e:
            logger.error(f"Error leyendo GPS de Astra: {e}")
            return []

    def test_connection(self) -> bool:
        try:
            self.db.list_collection_names()
            return True
        except Exception:
            return False
