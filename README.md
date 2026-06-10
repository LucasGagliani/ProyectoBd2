# Uber TPO - Proyecto Multi-Database

Backend FastAPI + frontend React/Vite para una app de viajes con PostgreSQL,
Redis, MongoDB, Neo4j y Cassandra/Astra.

## Requisitos

- Python 3.10 o superior
- Node.js 20 o superior
- Acceso a las bases configuradas en `.env`

## Configurar Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Editar `.env` con las credenciales reales. Para Neo4j Aura, usar
`neo4j+s://...`; si Windows/Python rechaza el certificado SSL, usar
`neo4j+ssc://...`.

Levantar API:

```bash
python main.py
```

La API queda en:

```text
http://localhost:8000
http://localhost:8000/docs
```

## Configurar Frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend queda en:

```text
http://localhost:5173
```

## Verificaciones

Backend:

```bash
python -m compileall src
```

Frontend:

```bash
cd frontend
npm run build
```

## Notas

- No commitear `.env`; usar `.env.example` como plantilla.
- `node_modules/`, `.venv/` y archivos locales quedan ignorados por Git.
- El backend soporta degradacion parcial para algunas bases, pero PostgreSQL y
  Redis son necesarios para el flujo principal de autenticacion y viajes.
