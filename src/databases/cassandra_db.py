"""Cassandra Database connection module."""

# Cluster y PlainTextAuthProvider se importan de forma lazy dentro de _connect()
# porque cassandra-driver detecta el event loop al nivel de módulo.
# En Python 3.12+ asyncore fue eliminado, así que hay que usar AsyncioConnection
# y registrarlo ANTES de importar Cluster. El import lazy garantiza ese orden.
from typing import Any, Optional, List, Dict
from src.config import settings
import logging

logger = logging.getLogger(__name__)


class CassandraDatabase:
    """Cassandra Database connection manager."""

    def __init__(self):
        """Initialize Cassandra connection."""
        self.cluster = None
        self.session = None
        self._connect()

    def _connect(self):
        """Establish Cassandra connection."""
        try:
            # Import lazy: AsyncioConnection debe registrarse ANTES de Cluster
            # para que cassandra-driver use asyncio en lugar del asyncore eliminado.
            from cassandra.io.asyncioreactor import AsyncioConnection
            from cassandra.cluster import Cluster
            from cassandra.auth import PlainTextAuthProvider

            # Setup authentication if credentials provided
            auth_provider = None
            if settings.CASSANDRA_USER and settings.CASSANDRA_PASSWORD:
                auth_provider = PlainTextAuthProvider(
                    username=settings.CASSANDRA_USER,
                    password=settings.CASSANDRA_PASSWORD,
                )

            # Create cluster connection usando AsyncioConnection explícitamente
            self.cluster = Cluster(
                [settings.CASSANDRA_HOST],
                port=settings.CASSANDRA_PORT,
                auth_provider=auth_provider,
                connection_class=AsyncioConnection,
            )

            # Conectar sin keyspace para poder crearlo si no existe
            temp_session = self.cluster.connect()
            temp_session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {settings.CASSANDRA_KEYSPACE}
                WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
            """)
            temp_session.shutdown()

            self.session = self.cluster.connect(settings.CASSANDRA_KEYSPACE)
            self._init_tables()
            logger.info("Connected to Cassandra database")
        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {e}")
            raise

    def _init_tables(self):
        """Crea las tablas necesarias si no existen."""
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS ubicaciones_viaje (
                id_viaje    int,
                timestamp   timestamp,
                id_conductor int,
                latitud     double,
                longitud    double,
                velocidad_estimada double,
                PRIMARY KEY (id_viaje, timestamp)
            ) WITH CLUSTERING ORDER BY (timestamp DESC)
        """)
        logger.info("Tablas Cassandra verificadas/creadas")

    def execute_query(self, query: str, parameters: Optional[List[Any]] = None):
        """
        Execute a CQL query.

        Args:
            query: CQL query string
            parameters: Query parameters

        Returns:
            Query results
        """
        try:
            if parameters:
                return self.session.execute(query, parameters)
            else:
                return self.session.execute(query)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return None

    def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """Insert data into a table."""
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            self.execute_query(query, list(data.values()))
            return True
        except Exception as e:
            logger.error(f"Error inserting data into {table}: {e}")
            return False

    def select(self, table: str, where: Optional[Dict[str, Any]] = None):
        """Select data from a table."""
        try:
            if where:
                conditions = " AND ".join([f"{k} = %s" for k in where.keys()])
                query = f"SELECT * FROM {table} WHERE {conditions}"
                return self.execute_query(query, list(where.values()))
            else:
                query = f"SELECT * FROM {table}"
                return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error selecting data from {table}: {e}")
            return None

    def update(
        self, table: str, data: Dict[str, Any], where: Dict[str, Any]
    ) -> bool:
        """Update data in a table."""
        try:
            set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
            where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            values = list(data.values()) + list(where.values())
            self.execute_query(query, values)
            return True
        except Exception as e:
            logger.error(f"Error updating data in {table}: {e}")
            return False

    def delete(self, table: str, where: Dict[str, Any]) -> bool:
        """Delete data from a table."""
        try:
            where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])
            query = f"DELETE FROM {table} WHERE {where_clause}"
            self.execute_query(query, list(where.values()))
            return True
        except Exception as e:
            logger.error(f"Error deleting data from {table}: {e}")
            return False

    def test_connection(self) -> bool:
        """Test Cassandra connection."""
        try:
            self.session.execute("SELECT now() FROM system.local")
            logger.info("Cassandra connection test successful")
            return True
        except Exception as e:
            logger.error(f"Cassandra connection test failed: {e}")
            return False

    def close(self):
        """Close Cassandra connection."""
        if self.session:
            self.session.shutdown()
        if self.cluster:
            self.cluster.shutdown()
            logger.info("Cassandra connection closed")
