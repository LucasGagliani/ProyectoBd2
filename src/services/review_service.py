"""
Lógica de negocio para reseñas mutuas.

Distribución de DBs según el plan:
  - MongoDB  → almacena los documentos de reseñas (esquema flexible, texto libre)
  - PostgreSQL → actualiza calificacion_promedio en usuarios y conductores (ACID)
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.databases.schema import Conductor, Pago, Resena, Usuario, Viaje

COLLECTION = "resenas"


# ------------------------------------------------------------------
# Helpers de calificación (PostgreSQL)
# ------------------------------------------------------------------

def _quantize(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _recalculate_passenger_rating(db: Session, mongo, user_id: int) -> None:
    """Recalcula el promedio de calificación del pasajero usando MongoDB."""
    if mongo is not None:
        resenas = mongo.find_many(COLLECTION, {
            "id_receptor": user_id,
            "tipo": "conductor_a_usuario",
        }) or []
        if resenas:
            avg = sum(r["calificacion"] for r in resenas) / len(resenas)
        else:
            avg = 0.0
    else:
        # Fallback a PostgreSQL si MongoDB no está disponible
        avg = db.query(func.avg(Resena.calificacion)).filter(
            Resena.id_receptor == user_id,
            Resena.tipo == "conductor_a_usuario",
        ).scalar() or 0.0

    usuario = db.get(Usuario, user_id)
    if usuario:
        usuario.calificacion_promedio = _quantize(float(avg))
        db.commit()


def _recalculate_conductor_rating(db: Session, mongo, conductor: Conductor) -> None:
    """Recalcula el promedio de calificación del conductor usando MongoDB."""
    if mongo is not None:
        resenas = mongo.find_many(COLLECTION, {
            "id_receptor": conductor.id_usuario,
            "tipo": "usuario_a_conductor",
        }) or []
        if resenas:
            avg = sum(r["calificacion"] for r in resenas) / len(resenas)
        else:
            avg = 0.0
    else:
        avg = db.query(func.avg(Resena.calificacion)).filter(
            Resena.id_receptor == conductor.id_usuario,
            Resena.tipo == "usuario_a_conductor",
        ).scalar() or 0.0

    conductor.calificacion_promedio = _quantize(float(avg))
    db.commit()


# ------------------------------------------------------------------
# Validación del viaje
# ------------------------------------------------------------------

def _validate_trip_ready_for_review(db: Session, viaje: Viaje) -> None:
    if viaje.estado != "finalizado":
        raise ValueError("Solo se pueden dejar reseñas en viajes finalizados.")
    pago = db.query(Pago).filter(Pago.id_viaje == viaje.id_viaje).first()
    if pago is None or pago.estado_transaccion != "aprobado":
        raise ValueError("El pago del viaje debe estar aprobado antes de dejar una reseña.")


# ------------------------------------------------------------------
# CRUD de reseñas (MongoDB)
# ------------------------------------------------------------------

def get_reviews_by_trip(mongo, db: Session, trip_id: int) -> List[dict]:
    """Lee reseñas de un viaje desde MongoDB."""
    if mongo is not None:
        return mongo.find_many(COLLECTION, {"id_viaje": trip_id}) or []
    # Fallback a PostgreSQL
    return [
        {
            "id_resena": r.id_resena,
            "id_viaje": r.id_viaje,
            "id_autor": r.id_autor,
            "id_receptor": r.id_receptor,
            "calificacion": r.calificacion,
            "comentario": r.comentario,
            "tipo": r.tipo,
            "fecha": r.fecha,
        }
        for r in db.query(Resena).filter(Resena.id_viaje == trip_id).all()
    ]


def get_review_by_trip_and_author(mongo, db: Session, trip_id: int, author_id: int) -> Optional[dict]:
    """Verifica si un autor ya reseñó este viaje."""
    if mongo is not None:
        return mongo.find_one(COLLECTION, {"id_viaje": trip_id, "id_autor": author_id})
    row = db.query(Resena).filter(
        Resena.id_viaje == trip_id, Resena.id_autor == author_id
    ).first()
    return {"id_resena": row.id_resena} if row else None


def create_review(
    db: Session,
    mongo,
    viaje: Viaje,
    autor: Usuario,
    conductor: Optional[Conductor],
    calificacion: int,
    comentario: Optional[str],
) -> dict:
    """
    Crea una reseña:
    - Documento guardado en MongoDB
    - calificacion_promedio actualizado en PostgreSQL
    """
    _validate_trip_ready_for_review(db, viaje)

    # Determinar tipo y receptor
    if viaje.id_usuario == autor.id_usuario:
        if viaje.id_conductor is None:
            raise ValueError("El viaje no tiene conductor asignado.")
        assigned_conductor = db.get(Conductor, viaje.id_conductor)
        if assigned_conductor is None:
            raise ValueError("Conductor del viaje no encontrado.")
        tipo = "usuario_a_conductor"
        id_receptor = assigned_conductor.id_usuario
    elif conductor is not None and viaje.id_conductor == conductor.id_conductor:
        tipo = "conductor_a_usuario"
        id_receptor = viaje.id_usuario
        assigned_conductor = conductor
    else:
        raise ValueError("No tenés permisos para reseñar este viaje.")

    if get_review_by_trip_and_author(mongo, db, viaje.id_viaje, autor.id_usuario) is not None:
        raise ValueError("Ya dejaste una reseña para este viaje.")

    documento = {
        "id_viaje": viaje.id_viaje,
        "id_autor": autor.id_usuario,
        "id_receptor": id_receptor,
        "calificacion": calificacion,
        "comentario": comentario,
        "tipo": tipo,
        "fecha": datetime.now(timezone.utc).isoformat(),
    }

    if mongo is not None:
        mongo.insert_one(COLLECTION, documento)
    else:
        # Fallback: guardar en PostgreSQL si MongoDB no está disponible
        resena = Resena(
            id_viaje=viaje.id_viaje,
            id_autor=autor.id_usuario,
            id_receptor=id_receptor,
            calificacion=calificacion,
            comentario=comentario,
            tipo=tipo,
        )
        db.add(resena)
        db.commit()

    # Actualizar promedio en PostgreSQL
    if tipo == "usuario_a_conductor":
        _recalculate_conductor_rating(db, mongo, assigned_conductor)
    else:
        _recalculate_passenger_rating(db, mongo, viaje.id_usuario)

    return documento


def get_trip_review_status(mongo, db: Session, viaje: Viaje, current_user: Usuario, conductor) -> dict:
    reviews = get_reviews_by_trip(mongo, db, viaje.id_viaje)
    usuario_a_conductor = any(r.get("tipo") == "usuario_a_conductor" for r in reviews)
    conductor_a_usuario = any(r.get("tipo") == "conductor_a_usuario" for r in reviews)
    mi_resena = any(r.get("id_autor") == current_user.id_usuario for r in reviews)

    puede_resenar = False
    if not mi_resena and viaje.estado == "finalizado":
        pago = db.query(Pago).filter(Pago.id_viaje == viaje.id_viaje).first()
        if pago and pago.estado_transaccion == "aprobado":
            is_passenger = viaje.id_usuario == current_user.id_usuario
            is_driver = conductor is not None and viaje.id_conductor == conductor.id_conductor
            puede_resenar = is_passenger or is_driver

    return {
        "id_viaje": viaje.id_viaje,
        "usuario_a_conductor": usuario_a_conductor,
        "conductor_a_usuario": conductor_a_usuario,
        "mi_resena": mi_resena,
        "puede_resenar": puede_resenar,
    }
