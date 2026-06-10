"""Router de notificaciones."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, get_current_user
from src.models.notification import NotificationResponse
from src.services import notification_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "",
    response_model=list[NotificationResponse],
    summary="Obtener notificaciones del usuario",
)
def get_notifications(
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener notificaciones del usuario actual (ordenadas por fecha descendente)."""
    notifs = notification_service.get_notifications(db, current_user.id_usuario, limit=limit)
    return notifs


@router.get(
    "/unread-count",
    summary="Contar notificaciones no leídas",
)
def get_unread_count(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener cantidad de notificaciones no leídas."""
    count = notification_service.get_unread_count(db, current_user.id_usuario)
    return {"unread_count": count}


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Marcar notificación como leída",
)
def mark_notification_as_read(
    notification_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Marcar una notificación específica como leída."""
    notif = notification_service.mark_as_read(db, notification_id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada",
        )
    
    # Verificar que la notificación pertenece al usuario actual
    if notif.id_usuario != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para marcar esta notificación como leída",
        )
    
    return notif


@router.patch(
    "/read-all",
    summary="Marcar todas las notificaciones como leídas",
)
def mark_all_notifications_as_read(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Marcar todas las notificaciones del usuario como leídas."""
    count = notification_service.mark_all_as_read(db, current_user.id_usuario)
    logger.info(f"Usuario {current_user.id_usuario} marcó {count} notificaciones como leídas")
    return {"message": f"{count} notificación(es) marcada(s) como leída(s)"}
