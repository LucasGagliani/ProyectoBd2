"""
Utility module for database initialization and schema setup.
Useful for creating tables and collections automatically.
"""

import logging
from sqlalchemy import text
from src.databases import SQLDatabase, MongoDBDatabase, CassandraDatabase

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Initialize database schemas and collections."""

    @staticmethod
    def init_sql_schema(db: SQLDatabase):
        """
        Initialize SQL database schema.

        Example tables for a typical project.
        """
        sql_queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER NOT NULL,
                total DECIMAL(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
        ]

        session = db.get_session()
        try:
            for query in sql_queries:
                session.execute(text(query))
            session.commit()
            logger.info("SQL schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing SQL schema: {e}")
            session.rollback()
        finally:
            session.close()

    @staticmethod
    def init_mongodb_collections(db: MongoDBDatabase):
        """
        Initialize MongoDB collections with indexes.
        """
        try:
            # Users collection
            users_collection = db.get_collection("users")
            users_collection.create_index("email", unique=True)
            logger.info("Users collection initialized")

            # Products collection
            products_collection = db.get_collection("products")
            products_collection.create_index("name")
            logger.info("Products collection initialized")

            # Orders collection
            orders_collection = db.get_collection("orders")
            orders_collection.create_index("user_id")
            orders_collection.create_index("created_at")
            logger.info("Orders collection initialized")

        except Exception as e:
            logger.error(f"Error initializing MongoDB collections: {e}")

    @staticmethod
    def init_cassandra_keyspace(db: CassandraDatabase):
        """
        Initialize Cassandra keyspace and tables.

        Note: Requires manual setup of keyspace first via Astra dashboard
        """
        try:
            # Create tables - adjust based on your keyspace
            logger.info("Cassandra keyspace should be pre-created via Astra dashboard")

            # Example table creation (if keyspace allows):
            # query = """
            # CREATE TABLE IF NOT EXISTS users (
            #     user_id UUID PRIMARY KEY,
            #     username TEXT,
            #     email TEXT,
            #     created_at TIMESTAMP
            # )
            # """
            # db.execute_query(query)

        except Exception as e:
            logger.error(f"Error initializing Cassandra: {e}")


def init_all_databases():
    """Initialize all databases."""
    try:
        # SQL
        sql_db = SQLDatabase(db_type="postgresql")
        DatabaseInitializer.init_sql_schema(sql_db)
        sql_db.close()

        # MongoDB
        mongo_db = MongoDBDatabase()
        DatabaseInitializer.init_mongodb_collections(mongo_db)
        mongo_db.close()

        # Cassandra
        cassandra_db = CassandraDatabase()
        DatabaseInitializer.init_cassandra_keyspace(cassandra_db)
        cassandra_db.close()

        logger.info("All databases initialized successfully")

    except Exception as e:
        logger.error(f"Error during initialization: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_all_databases()
