"""Opaque session and CSRF token helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime

from app.config import Settings


def generate_opaque_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def hash_session_token(token: str) -> str:
    """Session tokens are stored only as SHA-256 hex digests."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _csrf_mac(session_token_hash: str, settings: Settings) -> bytes:
    return hmac.new(
        settings.csrf_secret.encode("utf-8"),
        session_token_hash.encode("ascii"),
        hashlib.sha256,
    ).digest()


def csrf_token_for(session_token_hash: str, settings: Settings) -> str:
    """Derive a session-bound CSRF token without persisting it.

    Rotating the session (login/logout) changes the derived token, which is how
    login invalidates the previous CSRF token.
    """

    return base64.urlsafe_b64encode(_csrf_mac(session_token_hash, settings)).decode().rstrip("=")


def csrf_token_matches(
    provided: str, session_token_hash: str, settings: Settings
) -> bool:
    if not provided:
        return False
    expected = csrf_token_for(session_token_hash, settings)
    return hmac.compare_digest(provided, expected)


def is_session_active(expires_at: datetime, revoked_at: datetime | None, now: datetime) -> bool:
    return revoked_at is None and expires_at > now
