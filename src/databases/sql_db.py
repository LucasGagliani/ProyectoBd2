"""SQL Database connection module."""

from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.config import settings
import logging

logger = logging.getLogger(__name__)


class SQLDatabase:
    """SQL Database connection manager using SQLAlchemy."""

    def __init__(self, db_type: str = "postgresql"):
        """
        Initialize SQL Database connection.

        Args:
            db_type: Database type ('postgresql' or 'mysql')
        """
        self.db_type = db_type
        self.engine = None
        self.SessionLocal = None
        self._connect()

    def _connect(self):
        """Establish database connection."""
        try:
            if self.db_type == "postgresql":
                connection_string = (
                    f"postgresql://{settings.SQL_USER}:{settings.SQL_PASSWORD}"
                    f"@{settings.SQL_HOST}:{settings.SQL_PORT}/{settings.SQL_DATABASE}"
                )
            elif self.db_type == "mysql":
                connection_string = (
                    f"mysql+mysqlconnector://{settings.SQL_USER}:{settings.SQL_PASSWORD}"
                    f"@{settings.SQL_HOST}:{settings.SQL_PORT}/{settings.SQL_DATABASE}"
                )
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

            # SSL requerido para providers cloud como Neon
            connect_args = {}
            if settings.SQL_SSLMODE:
                connect_args["sslmode"] = settings.SQL_SSLMODE

            self.engine = create_engine(
                connection_string,
                echo=False,
                connect_args=connect_args,
                pool_pre_ping=True,   # reconecta automáticamente si Neon cerró la conexión
                pool_recycle=300,     # recicla conexiones cada 5 min para evitar timeouts
            )
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            logger.info(f"Connected to {self.db_type} database")
        except Exception as e:
            logger.error(f"Failed to connect to SQL database: {e}")
            raise

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def execute_query(self, query: str) -> list:
        """
        Execute a raw SQL query.

        Args:
            query: SQL query string

        Returns:
            Query results as list of dictionaries
        """
        session = self.get_session()
        try:
            result = session.execute(text(query))
            return [dict(row._mapping) for row in result.fetchall()]
        finally:
            session.close()

    def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            session = self.get_session()
            session.execute(text("SELECT 1"))
            session.close()
            logger.info("SQL connection test successful")
            return True
        except Exception as e:
            logger.error(f"SQL connection test failed: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("SQL connection closed")
