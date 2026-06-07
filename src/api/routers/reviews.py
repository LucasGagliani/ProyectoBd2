"""Router de reseñas mutuas."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
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
    summary="Crear reseña para un viaje finalizado y pagado",
)
def create_review(
    data: ReviewCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    viaje = db.get(Viaje, data.id_viaje)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = _load_conductor(db, current_user)
    _authorize_trip_access(current_user, conductor, viaje)

    try:
        resena = review_service.create_review(
            db=db,
            viaje=viaje,
            autor=current_user,
            conductor=conductor,
            calificacion=data.calificacion,
            comentario=data.comentario,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    logger.info(f"Reseña creada: id_resena={resena.id_resena} viaje={resena.id_viaje} tipo={resena.tipo}")
    return resena


@router.get(
    "/trip/{trip_id}",
    response_model=List[ReviewResponse],
    summary="Listar reseñas de un viaje",
)
def get_reviews_by_trip(
    trip_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    viaje = db.get(Viaje, trip_id)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = _load_conductor(db, current_user)
    _authorize_trip_access(current_user, conductor, viaje)

    return review_service.get_reviews_by_trip(db, trip_id)


@router.get(
    "/trip/{trip_id}/status",
    response_model=TripReviewStatusResponse,
    summary="Ver estado de reseñas de un viaje",
)
def get_trip_review_status(
    trip_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    viaje = db.get(Viaje, trip_id)
    if viaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")

    conductor = _load_conductor(db, current_user)
    _authorize_trip_access(current_user, conductor, viaje)

    status_data = review_service.get_trip_review_status(db, viaje, current_user, conductor)
    return TripReviewStatusResponse(**status_data)
