"""Reusable FastAPI dependencies: DB session, CSRF, authentication, RBAC."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config import Settings
from app.enums import Role
from app.errors import ApiError
from app.models import SessionToken, User
from app.repositories import SessionRepository, UserRepository
from app.security.throttle import Throttle
from app.security.tokens import (
    csrf_token_matches,
    hash_session_token,
    is_session_active,
)
from app.services.verification import VerifiedCompany, load_verified_company
from app.time_utils import utcnow


def settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Iterator[Session]:
    factory = request.app.state.session_factory
    db: Session = factory()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_login_throttle(request: Request) -> Throttle:
    return request.app.state.login_throttle


def get_registration_throttle(request: Request) -> Throttle:
    return request.app.state.registration_throttle


def _session_cookie_token(request: Request, settings: Settings) -> str | None:
    return request.cookies.get(settings.session_cookie_name)


def lookup_session_row(
    request: Request, db: Session, settings: Settings
) -> SessionToken | None:
    raw = _session_cookie_token(request, settings)
    if not raw:
        return None
    return SessionRepository(db).get_by_token_hash(hash_session_token(raw))


def get_active_session_row(
    request: Request, db: Session, settings: Settings
) -> SessionToken | None:
    row = lookup_session_row(request, db, settings)
    if row is None:
        return None
    if not is_session_active(row.expires_at, row.revoked_at, utcnow()):
        return None
    return row


def enforce_origin(request: Request, settings: Settings) -> None:
    """Reject disallowed browser origins on unsafe requests.

    A missing Origin is tolerated for non-browser clients (they do not carry
    ambient cookies cross-site). When an Origin is supplied - as browsers do
    for fetch/XHR POST/PATCH - it must be explicitly allow-listed.
    """

    origin = request.headers.get("origin")
    if origin is None:
        return
    if origin.rstrip("/") not in settings.origin_set:
        raise ApiError(403, "CSRF_INVALID", "Request origin is not allowed.")


def require_csrf(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> SessionToken:
    """Validate Origin + session-bound CSRF token for unsafe methods."""

    enforce_origin(request, settings)
    provided = request.headers.get(settings.csrf_header_name, "")
    if not provided:
        raise ApiError(403, "CSRF_INVALID", "Missing CSRF token.")

    row = get_active_session_row(request, db, settings)
    if row is None or not csrf_token_matches(provided, row.token_hash, settings):
        raise ApiError(403, "CSRF_INVALID", "Invalid or expired CSRF token.")
    return row


def require_logout_csrf(
    request: Request,
    db: Session,
    settings: Settings,
) -> SessionToken | None:
    """Logout variant: a revoked session can still prove CSRF for idempotency."""

    enforce_origin(request, settings)
    row = lookup_session_row(request, db, settings)
    if row is None:
        return None
    provided = request.headers.get(settings.csrf_header_name, "")
    if not provided or not csrf_token_matches(provided, row.token_hash, settings):
        raise ApiError(403, "CSRF_INVALID", "Invalid or expired CSRF token.")
    return row


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> User:
    row = get_active_session_row(request, db, settings)
    if row is None or row.user_id is None:
        raise ApiError(401, "UNAUTHENTICATED", "Authentication is required.")
    user = UserRepository(db).get_by_id(row.user_id)
    if user is None:
        raise ApiError(401, "UNAUTHENTICATED", "Authentication is required.")
    request.state.session_row = row
    # Always load the role from the database rather than trusting any cached
    # session/user payload from the client or an earlier request.
    return user


def require_administrator(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.ADMINISTRATOR:
        raise ApiError(403, "FORBIDDEN", "Administrator privileges are required.")
    return user


def require_verified_company_dependency(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VerifiedCompany:
    """Current-state check; Phase 2 write endpoints will depend on this."""

    return load_verified_company(db, user)


# Public alias used by Phase 2 consumers and tests.
require_verified_company = require_verified_company_dependency
