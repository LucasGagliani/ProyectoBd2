"""Aplicación principal."""

from src.databases import SQLDatabase, RedisDatabase, MongoDBDatabase, Neo4jDatabase, CassandraDatabase


def main():
    """Conectar a todas las bases de datos."""
    databases = {
        "SQL": SQLDatabase,
        "Redis": RedisDatabase,
        "MongoDB": MongoDBDatabase,
        "Neo4j": Neo4jDatabase,
        "Cassandra": CassandraDatabase
    }
    
    for name, db_class in databases.items():
        try:
            db = db_class()
            print(f"✓ {name} conectado")
        except Exception as e:
            print(f"✗ {name}: {e}")


if __name__ == "__main__":
    main()
