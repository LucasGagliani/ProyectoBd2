"""
Configuration module for database connections.
Centralizes all database connection settings using environment variables.
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # SQL Configuration
    SQL_HOST: str = os.getenv("SQL_HOST", "localhost")
    SQL_PORT: int = int(os.getenv("SQL_PORT", "5432"))
    SQL_USER: str = os.getenv("SQL_USER", "postgres")
    SQL_PASSWORD: str = os.getenv("SQL_PASSWORD", "password")
    SQL_DATABASE: str = os.getenv("SQL_DATABASE", "mydb")
    SQL_SSLMODE: str = os.getenv("SQL_SSLMODE", "")

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # MongoDB Configuration
    MONGODB_HOST: str = os.getenv("MONGODB_HOST", "localhost")
    MONGODB_PORT: int = int(os.getenv("MONGODB_PORT", "27017"))
    MONGODB_USER: str = os.getenv("MONGODB_USER", "")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD", "")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "mydb")

    # Neo4j Configuration (supports both local and Aura)
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    # Backward compatibility
    NEO4J_HOST: str = os.getenv("NEO4J_HOST", "localhost")
    NEO4J_PORT: int = int(os.getenv("NEO4J_PORT", "7687"))

    # Cassandra Configuration
    CASSANDRA_HOST: str = os.getenv("CASSANDRA_HOST", "localhost")
    CASSANDRA_PORT: int = int(os.getenv("CASSANDRA_PORT", "9042"))
    CASSANDRA_KEYSPACE: str = os.getenv("CASSANDRA_KEYSPACE", "mykeyspace")
    CASSANDRA_USER: str = os.getenv("CASSANDRA_USER", "")
    CASSANDRA_PASSWORD: str = os.getenv("CASSANDRA_PASSWORD", "")

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "changeme-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 horas

    model_config = {"env_file": ".env", "case_sensitive": True}


# Global settings instance
settings = Settings()
