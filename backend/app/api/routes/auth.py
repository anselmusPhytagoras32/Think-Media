"""Authentication routes (FR01)."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import (
    get_active_session_row,
    get_current_user,
    get_db,
    get_login_throttle,
    get_registration_throttle,
    require_csrf,
    require_logout_csrf,
    settings_dep,
)
from app.api.responses import AUTH_ERRORS
from app.config import Settings
from app.errors import ApiError
from app.models import SessionToken, User
from app.repositories import SessionRepository
from app.schemas import CsrfResponse, LoginRequest, ProfileEnvelope, RegisterRequest
from app.security.cookies import clear_session_cookie, set_session_cookie
from app.security.throttle import Throttle
from app.security.tokens import (
    csrf_token_for,
    generate_opaque_token,
    hash_session_token,
)
from app.services.accounts import AccountService
from app.services.presenters import envelope
from app.time_utils import utcnow
from app.validation import normalize_email

router = APIRouter(prefix="/auth", tags=["auth"], responses=AUTH_ERRORS)


def _issue_session(
    db: Session,
    *,
    settings: Settings,
    user_id,
) -> tuple[str, SessionToken]:
    raw = generate_opaque_token()
    row = SessionRepository(db).create(
        token_hash=hash_session_token(raw),
        expires_at=utcnow() + timedelta(seconds=settings.session_ttl_seconds),
        user_id=user_id,
    )
    return raw, row


@router.get("/csrf", response_model=CsrfResponse)
def get_csrf_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> CsrfResponse:
    """Bootstrap (or reuse) a session and return its bound CSRF token."""

    row = get_active_session_row(request, db, settings)
    if row is None:
        raw, row = _issue_session(db, settings=settings, user_id=None)
        db.commit()
        set_session_cookie(response, raw, settings)
    response.headers["Cache-Control"] = "no-store"
    return CsrfResponse(csrf_token=csrf_token_for(row.token_hash, settings))


@router.post("/register", response_model=ProfileEnvelope, status_code=201)
def register(
    payload: RegisterRequest,
    request: Request,
    _csrf: SessionToken = Depends(require_csrf),
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
    throttle: Throttle = Depends(get_registration_throttle),
) -> ProfileEnvelope:
    client_ip = settings.client_ip(
        request.client.host if request.client else None,
        request.headers.get("x-forwarded-for"),
    )
    key = f"register:{client_ip}"
    retry_after = throttle.retry_after(key)
    if retry_after is not None:
        raise ApiError(
            429,
            "RATE_LIMITED",
            "Too many registration attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    throttle.record_attempt(key)

    service = AccountService(db)
    return service.register(payload)


@router.post("/login", response_model=ProfileEnvelope)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    csrf_row: SessionToken = Depends(require_csrf),
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
    throttle: Throttle = Depends(get_login_throttle),
) -> ProfileEnvelope:
    client_ip = settings.client_ip(
        request.client.host if request.client else None,
        request.headers.get("x-forwarded-for"),
    )
    try:
        throttle_key = f"login:{normalize_email(payload.email)}:{client_ip}"
    except ValueError:
        throttle_key = f"login:{payload.email}:{client_ip}"

    retry_after = throttle.retry_after(throttle_key)
    if retry_after is not None:
        raise ApiError(
            429,
            "RATE_LIMITED",
            "Too many sign-in attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    service = AccountService(db)
    try:
        user = service.authenticate(payload.email, payload.password)
    except ApiError:
        throttle.record_attempt(throttle_key)
        raise
    throttle.reset(throttle_key)

    # Rotate the session on login. The pre-login (anonymous) session is
    # revoked, so its derived CSRF token stops working.
    sessions = SessionRepository(db)
    sessions.revoke(csrf_row, utcnow())
    raw, _new_row = _issue_session(db, settings=settings, user_id=user.id)
    db.commit()
    set_session_cookie(response, raw, settings)
    response.headers["Cache-Control"] = "no-store"
    return envelope(service.profiles, user)


@router.get("/me", response_model=ProfileEnvelope)
def me(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileEnvelope:
    response.headers["Cache-Control"] = "no-store"
    return envelope(AccountService(db).profiles, user)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> Response:
    row = require_logout_csrf(request, db, settings)
    if row is not None and row.revoked_at is None:
        SessionRepository(db).revoke(row, utcnow())
        db.commit()
    response.status_code = 204
    clear_session_cookie(response, settings)
    response.headers["Cache-Control"] = "no-store"
    return response
