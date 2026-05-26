"""Redis Database connection module."""

import redis
from typing import Any, Optional
from src.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class RedisDatabase:
    """Redis Database connection manager."""

    def __init__(self):
        """Initialize Redis connection."""
        self.client: Optional[redis.Redis] = None
        self._connect()

    def _connect(self):
        """Establish Redis connection."""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                db=settings.REDIS_DB,
                decode_responses=True,
            )
            # Test connection
            self.client.ping()
            logger.info("Connected to Redis database")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in Redis.

        Args:
            key: Redis key
            value: Value to store (will be JSON serialized if not string)
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            if not isinstance(value, str):
                value = json.dumps(value)
            self.client.set(key, value, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key {key}: {e}")
            return False

    def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from Redis."""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting JSON key {key}: {e}")
            return None

    def test_connection(self) -> bool:
        """Test Redis connection."""
        try:
            self.client.ping()
            logger.info("Redis connection test successful")
            return True
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            return False

    def close(self):
        """Close Redis connection."""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")
