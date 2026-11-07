"""FR08–09 suggestion and explicit feedback HTTP adapters."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_csrf
from app.models import User
from app.schemas.recommendations import InteractionInput
from app.services.recommendations import InteractionService, RecommendationService

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations")
def recommendations(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return RecommendationService(
        db, user, request.app.state.settings.recommender_alpha
    ).recommend(limit)


@router.post("/interactions", status_code=201, dependencies=[Depends(require_csrf)])
def interactions(
    payload: InteractionInput,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return InteractionService(db, user, request.app.state.interaction_throttle).record(
        payload
    )
