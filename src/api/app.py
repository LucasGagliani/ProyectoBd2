"""
Instancia principal de FastAPI.
Registra routers y crea las tablas SQL al iniciar.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import auth, users, drivers, trips, payments, reviews, locations
from src.databases.connections import get_sql
from src.databases.schema import Base

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea las tablas en PostgreSQL si no existen (al arrancar la app)."""
    try:
        sql = get_sql()
        Base.metadata.create_all(bind=sql.engine)
        logger.info("Tablas SQL verificadas/creadas correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar schema SQL: {e}")
    yield
    # Cleanup al apagar (por ahora no necesitamos nada)


app = FastAPI(
    title="Uber TPO — Ingeniería de Datos II",
    description="Backend multi-DB para la app de transporte. UADE — Equipo 07.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Handler global de excepciones no controladas
# Evita que cualquier error inesperado devuelva un 500 sin mensaje.
# ------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = str(exc)
    logger.error(f"Error no controlado en {request.method} {request.url}: {error_msg}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error interno: {error_msg}"},
    )


# ------------------------------------------------------------------
# Routers Parte 1
# ------------------------------------------------------------------
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(users.router, prefix="/users", tags=["Usuarios"])
app.include_router(drivers.router, prefix="/drivers", tags=["Conductores"])
app.include_router(trips.router, prefix="/trips", tags=["Viajes"])
app.include_router(payments.router, prefix="/payments", tags=["Pagos"])
app.include_router(reviews.router, prefix="/reviews", tags=["Reseñas"])
app.include_router(locations.router, prefix="/locations", tags=["GPS / Ubicaciones"])


@app.get("/", tags=["Health"])
def health_check():
    """Endpoint de salud — verifica que la API esté corriendo."""
    return {"status": "ok", "app": "Uber TPO API"}
