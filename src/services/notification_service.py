"""Servicio de notificaciones."""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.databases.schema import Notificacion


def create_notification(
    db: Session,
    id_usuario: int,
    titulo: str,
    mensaje: str,
    tipo: str,
    id_referencia: Optional[int] = None,
) -> Notificacion:
    """Crear una nueva notificación."""
    notif = Notificacion(
        id_usuario=id_usuario,
        titulo=titulo,
        mensaje=mensaje,
        tipo=tipo,
        id_referencia=id_referencia,
        leida=0,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def get_notifications(db: Session, id_usuario: int, limit: int = 50) -> List[Notificacion]:
    """Obtener notificaciones de un usuario (más recientes primero)."""
    return db.query(Notificacion)\
        .filter(Notificacion.id_usuario == id_usuario)\
        .order_by(Notificacion.fecha_creacion.desc())\
        .limit(limit)\
        .all()


def get_unread_count(db: Session, id_usuario: int) -> int:
    """Contar notificaciones no leídas."""
    return db.query(Notificacion)\
        .filter(Notificacion.id_usuario == id_usuario)\
        .filter(Notificacion.leida == 0)\
        .count()


def mark_as_read(db: Session, id_notificacion: int) -> Notificacion:
    """Marcar notificación como leída."""
    notif = db.get(Notificacion, id_notificacion)
    if notif:
        notif.leida = 1
        db.commit()
        db.refresh(notif)
    return notif


def mark_all_as_read(db: Session, id_usuario: int) -> int:
    """Marcar todas las notificaciones de un usuario como leídas."""
    count = db.query(Notificacion)\
        .filter(Notificacion.id_usuario == id_usuario)\
        .filter(Notificacion.leida == 0)\
        .count()
    
    db.query(Notificacion)\
        .filter(Notificacion.id_usuario == id_usuario)\
        .filter(Notificacion.leida == 0)\
        .update({"leida": 1})
    db.commit()
    return count
