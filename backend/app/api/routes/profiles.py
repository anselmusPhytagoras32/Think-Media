"""Profile routes (FR02)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_csrf
from app.api.responses import PROFILE_ERRORS
from app.models import SessionToken, User
from app.schemas import ProfileEnvelope, ProfileUpdateRequest
from app.services.profiles import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"], responses=PROFILE_ERRORS)


@router.get("/me", response_model=ProfileEnvelope)
def get_my_profile(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileEnvelope:
    response.headers["Cache-Control"] = "no-store"
    return ProfileService(db).get_me(user)


@router.patch("/me", response_model=ProfileEnvelope)
def update_my_profile(
    payload: ProfileUpdateRequest,
    response: Response,
    user: User = Depends(get_current_user),
    _csrf: SessionToken = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> ProfileEnvelope:
    response.headers["Cache-Control"] = "no-store"
    return ProfileService(db).update_me(user, payload)
