# Proyecto Multi-Database

Conexiones básicas a 5 bases de datos: SQL, Redis, MongoDB, Neo4j y Cassandra.

## Instalación

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## Configuración

1. Copiar `.env.example` a `.env`
2. Editar `.env` con tus credenciales

## Uso

```python
from src.databases import SQLDatabase, RedisDatabase, MongoDBDatabase
from src.databases import Neo4jDatabase, CassandraDatabase

sql_db = SQLDatabase(db_type="postgresql")
redis_db = RedisDatabase()
mongo_db = MongoDBDatabase()
neo4j_db = Neo4jDatabase()
cassandra_db = CassandraDatabase()
```

Ver `INDEX.txt` para estructura completa.
