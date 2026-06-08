"""MongoDB Database connection module."""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import Any, Optional, List, Dict
from src.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDBDatabase:
    """MongoDB Database connection manager."""

    def __init__(self):
        """Initialize MongoDB connection."""
        self.client: Optional[MongoClient] = None
        self.db = None
        self._connect()

    def _connect(self):
        """Establish MongoDB connection."""
        try:
            # Prioridad: MONGODB_URI completa (Atlas) → host:port local
            if settings.MONGODB_URI:
                connection_string = settings.MONGODB_URI
            elif settings.MONGODB_USER and settings.MONGODB_PASSWORD:
                connection_string = (
                    f"mongodb+srv://{settings.MONGODB_USER}:{settings.MONGODB_PASSWORD}"
                    f"@{settings.MONGODB_HOST}/{settings.MONGODB_DATABASE}"
                    f"?retryWrites=true&w=majority"
                )
            else:
                connection_string = (
                    f"mongodb://{settings.MONGODB_HOST}:{settings.MONGODB_PORT}/"
                )

            self.client = MongoClient(connection_string)
            # Verify connection
            self.client.admin.command("ping")
            self.db = self.client[settings.MONGODB_DATABASE]
            logger.info("Connected to MongoDB database")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        return self.db[collection_name]

    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        """Insert a document into a collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting document into {collection_name}: {e}")
            return None

    def insert_many(
        self, collection_name: str, documents: List[Dict[str, Any]]
    ) -> Optional[List[str]]:
        """Insert multiple documents into a collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_many(documents)
            return [str(id_) for id_ in result.inserted_ids]
        except Exception as e:
            logger.error(f"Error inserting documents into {collection_name}: {e}")
            return None

    def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict]:
        """Find one document in a collection."""
        try:
            collection = self.get_collection(collection_name)
            result = collection.find_one(query)
            if result:
                result["_id"] = str(result["_id"])
            return result
        except Exception as e:
            logger.error(f"Error finding document in {collection_name}: {e}")
            return None

    def find_many(
        self, collection_name: str, query: Dict[str, Any] = None
    ) -> Optional[List[Dict]]:
        """Find multiple documents in a collection."""
        try:
            collection = self.get_collection(collection_name)
            query = query or {}
            results = list(collection.find(query))
            for result in results:
                result["_id"] = str(result["_id"])
            return results
        except Exception as e:
            logger.error(f"Error finding documents in {collection_name}: {e}")
            return None

    def update_one(
        self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]
    ) -> bool:
        """Update one document in a collection."""
        try:
            collection = self.get_collection(collection_name)
            collection.update_one(query, {"$set": update})
            return True
        except Exception as e:
            logger.error(f"Error updating document in {collection_name}: {e}")
            return False

    def delete_one(self, collection_name: str, query: Dict[str, Any]) -> bool:
        """Delete one document from a collection."""
        try:
            collection = self.get_collection(collection_name)
            collection.delete_one(query)
            return True
        except Exception as e:
            logger.error(f"Error deleting document from {collection_name}: {e}")
            return False

    def test_connection(self) -> bool:
        """Test MongoDB connection."""
        try:
            self.client.admin.command("ping")
            logger.info("MongoDB connection test successful")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection test failed: {e}")
            return False

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
