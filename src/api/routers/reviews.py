"""
Router de reseñas mutuas.

Las reseñas se almacenan en MongoDB (documentos flexibles).
El promedio de calificación se actualiza en PostgreSQL.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db, get_mongo_client
from src.databases.schema import Conductor, Viaje
from src.models.review import ReviewCreate, ReviewResponse, TripReviewStatusResponse
from src.services import review_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _load_conductor(db: Session, current_user):
    return db.query(Conductor).filter(Conductor.id_usuario == current_user.id_usuario).first()


def _authorize_trip_access(current_user, conductor, viaje: Viaje) -> None:
    if viaje.id_usuario == current_user.id_usuario:
        return
    if conductor is not None and viaje.id_conductor == conductor.id_conductor:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tenés permisos para ver o modificar reseñas de este viaje.",
    )


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reseña (guardada en MongoDB)",
)
def create_review(
    data: ReviewCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    mongo=Depends(get_mongo_client),
):
    """
    Crea una reseña para un viaje finalizado y pagado.
    El documento se guarda en MongoDB. El promedio se recalcula en PostgreSQL.
    """
    viaje = db.get(Viaje, data.id_viaje)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = _load_conductor(db, current_user)
    _authorize_trip_access(current_user, conductor, viaje)

    try:
        doc = review_service.create_review(
            db=db,
            mongo=mongo,
            viaje=viaje,
            autor=current_user,
            conductor=conductor,
            calificacion=data.calificacion,
            comentario=data.comentario,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    logger.info(f"Reseña creada: viaje={data.id_viaje} tipo={doc.get('tipo')}")
    return ReviewResponse(
        id_resena=0,
        id_viaje=doc["id_viaje"],
        id_autor=doc["id_autor"],
        id_receptor=doc["id_receptor"],
        calificacion=doc["calificacion"],
        comentario=doc.get("comentario"),
        tipo=doc["tipo"],
        fecha=None,
    )


@router.get(
    "/trip/{trip_id}",
    response_model=List[ReviewResponse],
    summary="Listar reseñas de un viaje (desde MongoDB)",
)
def get_reviews_by_trip(
    trip_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    mongo=Depends(get_mongo_client),
):
    viaje = db.get(Viaje, trip_id)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = _load_conductor(db, current_user)
    _authorize_trip_access(current_user, conductor, viaje)

    docs = review_service.get_reviews_by_trip(mongo, db, trip_id)
    return [
        ReviewResponse(
            id_resena=0,
            id_viaje=d["id_viaje"],
            id_autor=d["id_autor"],
            id_receptor=d["id_receptor"],
            calificacion=d["calificacion"],
            comentario=d.get("comentario"),
            tipo=d["tipo"],
            fecha=None,
        )
        for d in docs
    ]


@router.get(
    "/trip/{trip_id}/status",
    response_model=TripReviewStatusResponse,
    summary="Ver estado de reseñas de un viaje",
)
def get_trip_review_status(
    trip_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    mongo=Depends(get_mongo_client),
):
    viaje = db.get(Viaje, trip_id)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = _load_conductor(db, current_user)
    _authorize_trip_access(current_user, conductor, viaje)

    data = review_service.get_trip_review_status(mongo, db, viaje, current_user, conductor)
    return TripReviewStatusResponse(**data)
