"""Shared OpenAPI error response declarations (runtime envelope in app.errors)."""

from __future__ import annotations

from app.schemas import ErrorEnvelope


def _error(description: str) -> dict:
    return {"model": ErrorEnvelope, "description": description}


AUTH_ERRORS = {
    401: _error("Authentication required or invalid credentials."),
    403: _error("Forbidden request, invalid CSRF token or disallowed origin."),
    422: _error("Request validation failed."),
    429: _error("Authentication throttle exceeded."),
    500: _error("Unexpected server error without internal details."),
}

PROFILE_ERRORS = {
    401: _error("Authentication required."),
    403: _error("Forbidden request, invalid CSRF token or disallowed origin."),
    422: _error("Request validation failed."),
    500: _error("Unexpected server error without internal details."),
}

ADMIN_ERRORS = {
    401: _error("Authentication required."),
    403: _error("Administrator privileges required or CSRF check failed."),
    404: _error("Company not found."),
    409: _error("Stale or disallowed verification state."),
    422: _error("Request validation failed."),
    500: _error("Unexpected server error without internal details."),
}

HEALTH_ERRORS = {
    500: _error("Unexpected server error without internal details."),
}
