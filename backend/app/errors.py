"""Uniform API error envelope and exception handlers."""

from __future__ import annotations

import logging
import re
import uuid
from contextvars import ContextVar
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("thinkmedia.errors")

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,100}$")

_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
}


def sanitize_request_id(value: str | None) -> str | None:
    if value and _REQUEST_ID_RE.match(value):
        return value
    return None


def current_request_id() -> str:
    return request_id_var.get() or str(uuid.uuid4())


def error_payload(
    code: str,
    message: str,
    fields: dict[str, list[str]] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "fields": fields or {},
            "request_id": request_id or current_request_id(),
        }
    }


class ApiError(Exception):
    """An expected, uniformly rendered API failure."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        fields: dict[str, list[str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields or {}
        self.headers = headers or {}


def json_error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    fields: dict[str, list[str]] | None = None,
    headers: dict[str, str] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    rid = request_id or current_request_id()
    merged_headers = {"Cache-Control": "no-store"}
    if headers:
        merged_headers.update(headers)
    merged_headers.setdefault("X-Request-ID", rid)
    return JSONResponse(
        status_code=status_code,
        content=error_payload(code, message, fields, request_id=rid),
        headers=merged_headers,
    )


def _validation_fields(exc: RequestValidationError) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for error in exc.errors():
        location = [
            str(part)
            for part in error.get("loc", ())
            if part not in {"body", "query", "path", "header", "cookie"}
            and not isinstance(part, int)
            and not (isinstance(part, str) and part.isdigit())
        ]
        key = ".".join(location) or "body"
        fields.setdefault(key, []).append(str(error.get("msg", "Invalid value.")))
    return fields


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return json_error_response(
            exc.status_code,
            exc.code,
            exc.message,
            fields=exc.fields,
            headers=exc.headers,
            request_id=getattr(request.state, "request_id", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return json_error_response(
            422,
            "VALIDATION_ERROR",
            "Request validation failed.",
            fields=_validation_fields(exc),
            request_id=getattr(request.state, "request_id", None),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_error(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        status = exc.status_code
        code = _STATUS_CODES.get(status, "HTTP_ERROR")
        message = "Resource not found." if status == 404 else str(exc.detail)
        if status == 405:
            message = "Method not allowed."
        headers = dict(getattr(exc, "headers", None) or {})
        if status == 401:
            headers.setdefault("WWW-Authenticate", "Session")
        return json_error_response(status, code, message, headers=headers, request_id=getattr(request.state, "request_id", None))

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Log the server-side trace only; never return traces, SQL or secrets.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return json_error_response(
            500,
            "INTERNAL_ERROR",
            "An unexpected error occurred.",
            request_id=getattr(request.state, "request_id", None),
        )
