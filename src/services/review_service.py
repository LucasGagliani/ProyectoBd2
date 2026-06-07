"""Lógica de negocio para reseñas mutuas."""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.databases.schema import Conductor, Pago, Resena, Usuario, Viaje


def get_reviews_by_trip(db: Session, trip_id: int) -> List[Resena]:
    return db.query(Resena).filter(Resena.id_viaje == trip_id).order_by(Resena.fecha).all()


def get_review_by_trip_and_author(db: Session, trip_id: int, author_id: int) -> Optional[Resena]:
    return (
        db.query(Resena)
        .filter(Resena.id_viaje == trip_id, Resena.id_autor == author_id)
        .first()
    )


def _quantize_rating(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _recalculate_passenger_rating(db: Session, user_id: int) -> None:
    avg = (
        db.query(func.avg(Resena.calificacion))
        .filter(Resena.id_receptor == user_id, Resena.tipo == "conductor_a_usuario")
        .scalar()
    )
    usuario = db.get(Usuario, user_id)
    if usuario is not None:
        usuario.calificacion_promedio = _quantize_rating(float(avg or 0))


def _recalculate_conductor_rating(db: Session, conductor: Conductor) -> None:
    avg = (
        db.query(func.avg(Resena.calificacion))
        .filter(
            Resena.id_receptor == conductor.id_usuario,
            Resena.tipo == "usuario_a_conductor",
        )
        .scalar()
    )
    conductor.calificacion_promedio = _quantize_rating(float(avg or 0))


def _validate_trip_ready_for_review(db: Session, viaje: Viaje) -> Pago:
    if viaje.estado != "finalizado":
        raise ValueError("Solo se pueden dejar reseñas en viajes finalizados.")

    pago = db.query(Pago).filter(Pago.id_viaje == viaje.id_viaje).first()
    if pago is None or pago.estado_transaccion != "aprobado":
        raise ValueError("El pago del viaje debe estar aprobado antes de dejar una reseña.")

    return pago


def create_review(
    db: Session,
    viaje: Viaje,
    autor: Usuario,
    conductor: Optional[Conductor],
    calificacion: int,
    comentario: Optional[str],
) -> Resena:
    _validate_trip_ready_for_review(db, viaje)

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
    else:
        raise ValueError("No tenés permisos para reseñar este viaje.")

    if get_review_by_trip_and_author(db, viaje.id_viaje, autor.id_usuario) is not None:
        raise ValueError("Ya dejaste una reseña para este viaje.")

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
    db.refresh(resena)

    if tipo == "usuario_a_conductor":
        assigned_conductor = db.get(Conductor, viaje.id_conductor)
        if assigned_conductor is not None:
            _recalculate_conductor_rating(db, assigned_conductor)
    else:
        _recalculate_passenger_rating(db, viaje.id_usuario)

    db.commit()
    return resena


def get_trip_review_status(
    db: Session,
    viaje: Viaje,
    current_user: Usuario,
    conductor: Optional[Conductor],
) -> dict:
    reviews = get_reviews_by_trip(db, viaje.id_viaje)
    usuario_a_conductor = any(r.tipo == "usuario_a_conductor" for r in reviews)
    conductor_a_usuario = any(r.tipo == "conductor_a_usuario" for r in reviews)
    mi_resena = any(r.id_autor == current_user.id_usuario for r in reviews)

    puede_resenar = False
    if not mi_resena and viaje.estado == "finalizado":
        pago = db.query(Pago).filter(Pago.id_viaje == viaje.id_viaje).first()
        if pago is not None and pago.estado_transaccion == "aprobado":
            is_passenger = viaje.id_usuario == current_user.id_usuario
            is_driver = (
                conductor is not None
                and viaje.id_conductor == conductor.id_conductor
            )
            puede_resenar = is_passenger or is_driver

    return {
        "id_viaje": viaje.id_viaje,
        "usuario_a_conductor": usuario_a_conductor,
        "conductor_a_usuario": conductor_a_usuario,
        "mi_resena": mi_resena,
        "puede_resenar": puede_resenar,
    }
