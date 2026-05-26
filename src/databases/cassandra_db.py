"""Cassandra Database connection module."""

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
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
            # Setup authentication if credentials provided
            auth_provider = None
            if settings.CASSANDRA_USER and settings.CASSANDRA_PASSWORD:
                auth_provider = PlainTextAuthProvider(
                    username=settings.CASSANDRA_USER,
                    password=settings.CASSANDRA_PASSWORD,
                )

            # Create cluster connection
            self.cluster = Cluster(
                [settings.CASSANDRA_HOST],
                port=settings.CASSANDRA_PORT,
                auth_provider=auth_provider,
            )

            self.session = self.cluster.connect(settings.CASSANDRA_KEYSPACE)
            logger.info("Connected to Cassandra database")
        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {e}")
            raise

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
