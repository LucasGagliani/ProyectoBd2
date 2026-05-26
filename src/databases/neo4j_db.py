"""Neo4j Database connection module."""

from neo4j import GraphDatabase
from typing import Any, Optional, List, Dict
from src.config import settings
import logging

logger = logging.getLogger(__name__)


class Neo4jDatabase:
    """Neo4j Database connection manager for Aura and local instances."""

    def __init__(self):
        """Initialize Neo4j connection."""
        self.driver = None
        self._connect()

    def _connect(self):
        """Establish Neo4j connection using URI or host:port."""
        try:
            # Try NEO4J_URI first (supports Aura), fallback to host:port
            if hasattr(settings, 'NEO4J_URI') and settings.NEO4J_URI:
                uri = settings.NEO4J_URI
            else:
                uri = f"bolt://{settings.NEO4J_HOST}:{settings.NEO4J_PORT}"
            
            self.driver = GraphDatabase.driver(
                uri, 
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # Test connection
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j database: {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None, mode: str = "r"):
        """
        Execute a Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters
            mode: 'r' for read, 'w' for write (default: 'r')

        Returns:
            Query results or empty list if failed
        """
        try:
            with self.driver.session() as session:
                if mode == "w":
                    result = session.write_transaction(lambda tx: tx.run(query, parameters or {}).data())
                else:
                    result = session.read_transaction(lambda tx: tx.run(query, parameters or {}).data())
                return result if result else []
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []

    def create_node(self, label: str, properties: Dict[str, Any]) -> Optional[Dict]:
        """Create a node in the graph."""
        try:
            query = f"CREATE (n:{label} $props) RETURN n"
            results = self.execute_query(query, {"props": properties}, mode="w")
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error creating node: {e}")
            return None

    def update_node(self, label: str, node_id: str, properties: Dict[str, Any]) -> Optional[Dict]:
        """Update a node's properties."""
        try:
            query = f"MATCH (n:{label} {{id: $id}}) SET n += $props RETURN n"
            results = self.execute_query(query, {"id": node_id, "props": properties}, mode="w")
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error updating node: {e}")
            return None

    def delete_node(self, label: str, node_id: str) -> bool:
        """Delete a node and its relationships."""
        try:
            query = f"MATCH (n:{label} {{id: $id}}) DETACH DELETE n"
            self.execute_query(query, {"id": node_id}, mode="w")
            return True
        except Exception as e:
            logger.error(f"Error deleting node: {e}")
            return False

    def match_nodes(
        self, label: str, where: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Dict]]:
        """Match nodes with optional filters."""
        try:
            if where:
                conditions = " AND ".join([f"n.{k} = ${k}" for k in where.keys()])
                query = f"MATCH (n:{label}) WHERE {conditions} RETURN n"
                return self.execute_query(query, where, mode="r")
            else:
                query = f"MATCH (n:{label}) RETURN n"
                return self.execute_query(query, mode="r")
        except Exception as e:
            logger.error(f"Error matching nodes: {e}")
            return []

    def create_relationship(
        self,
        source_label: str,
        source_id: str,
        relationship_type: str,
        target_label: str,
        target_id: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a relationship between two nodes."""
        try:
            if properties:
                query = (
                    f"MATCH (a:{source_label}), (b:{target_label}) "
                    f"WHERE a.id = $src_id AND b.id = $tgt_id "
                    f"CREATE (a)-[r:{relationship_type} $props]->(b) RETURN r"
                )
                self.execute_query(query, {
                    "src_id": source_id,
                    "tgt_id": target_id,
                    "props": properties
                }, mode="w")
            else:
                query = (
                    f"MATCH (a:{source_label}), (b:{target_label}) "
                    f"WHERE a.id = $src_id AND b.id = $tgt_id "
                    f"CREATE (a)-[:{relationship_type}]->(b)"
                )
                self.execute_query(query, {"src_id": source_id, "tgt_id": target_id}, mode="w")
            return True
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            return False

    def test_connection(self) -> bool:
        """Test Neo4j connection."""
        try:
            self.driver.verify_connectivity()
            logger.info("Neo4j connection test successful")
            return True
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return False

    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
