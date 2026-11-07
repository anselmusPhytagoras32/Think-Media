"""FastAPI application factory."""

from __future__ import annotations

import logging
import re
import uuid

from fastapi import FastAPI, Request

from app.api.responses import HEALTH_ERRORS
from app.api.routes import admin, auth, learning, marketplace, profiles, recommendations
from app.api.routes import feedback
from app.config import Settings, get_settings
from app.db import build_engine, build_session_factory
from app.errors import (
    install_exception_handlers,
    json_error_response,
    request_id_var,
    sanitize_request_id,
)
from app.providers.assistant import provider_for
from app.schemas import HealthResponse
from app.security.throttle import Throttle

logger = logging.getLogger("thinkmedia")

API_PREFIX = "/api/v1"


def _request_body_cap(request: Request, settings: Settings) -> int:
    if request.method == "POST" and re.fullmatch(
        r"/api/v1/listings/[0-9a-fA-F-]{36}/applications", request.url.path
    ):
        return 6 * 1024 * 1024
    return settings.max_request_body_bytes


async def _bounded_request(request: Request, call_next, settings: Settings):
    """Enforce NFR02/11 on actual bytes, including chunked or false lengths.

    Stop reading immediately at the limit rather than first buffering an
    unbounded body. Starlette replays the bounded cached body to the router.
    """
    cap = _request_body_cap(request, settings)
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > cap:
            return json_error_response(
                413, "PAYLOAD_TOO_LARGE", "Request body is too large."
            )
        chunks.append(chunk)
    request._body = b"".join(chunks)
    return await call_next(request)


def _create_throttles(settings: Settings) -> tuple[Throttle, Throttle]:
    login = Throttle(
        max_attempts=settings.login_max_failures,
        window_seconds=settings.login_window_seconds,
    )
    registration = Throttle(
        max_attempts=settings.register_max_attempts,
        window_seconds=settings.register_window_seconds,
    )
    return login, registration


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="ThinkMedia API",
        version="0.4.0",
        description=("ThinkMedia accounts, private applications, verified-company listings, approved learning, recommendations, feedback, administration and read-only resource guidance."),
    )

    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    login_throttle, registration_throttle = _create_throttles(settings)

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.login_throttle = login_throttle
    app.state.registration_throttle = registration_throttle
    app.state.interaction_throttle = Throttle(max_attempts=60, window_seconds=60)
    app.state.assistant_provider = provider_for(settings.assistant_mode)
    app.state.assistant_throttle = Throttle(
        max_attempts=settings.assistant_max_requests,
        window_seconds=settings.assistant_window_seconds,
    )

    install_exception_handlers(app)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = sanitize_request_id(request.headers.get("x-request-id")) or str(
            uuid.uuid4()
        )
        token = request_id_var.set(rid)
        request.state.request_id = rid
        try:
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    cap = _request_body_cap(request, settings)
                    too_large = int(content_length) > cap
                except ValueError:
                    too_large = False
                if too_large:
                    response = json_error_response(
                        413,
                        "PAYLOAD_TOO_LARGE",
                        "Request body is too large.",
                    )
                else:
                    response = await _bounded_request(request, call_next, settings)
            else:
                response = await _bounded_request(request, call_next, settings)
        finally:
            request_id_var.reset(token)

        response.headers["X-Request-ID"] = rid
        if request.url.path.startswith(API_PREFIX):
            response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

    app.include_router(feedback.router, prefix=API_PREFIX)
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(profiles.router, prefix=API_PREFIX)
    app.include_router(admin.router, prefix=API_PREFIX)
    app.include_router(marketplace.router, prefix=API_PREFIX)
    app.include_router(learning.router, prefix=API_PREFIX)
    app.include_router(recommendations.router, prefix=API_PREFIX)

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["health"],
        responses=HEALTH_ERRORS,
    )
    def health() -> HealthResponse:
        return HealthResponse()

    return app


app = create_app()
