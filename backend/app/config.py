"""Runtime configuration.

Secrets are read from the environment (or a local, git-ignored ``.env`` file).
The defaults below are safe for local HTTP development only; nothing here is a
deployment secret.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:8000,http://127.0.0.1:8000"
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variable names intentionally avoid an ``APP_`` prefix for
    ``DATABASE_URL`` (container convention) while other knobs use ``APP_``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    recommender_alpha: float = Field(
        default=1.0,
        ge=0,
        le=1,
        allow_inf_nan=False,
        validation_alias="APP_RECOMMENDER_ALPHA",
    )

    assistant_mode: Literal["disabled", "retrieval"] = Field(
        default="disabled", validation_alias="APP_ASSISTANT_MODE"
    )
    assistant_max_requests: int = Field(
        default=10, ge=1, le=100, validation_alias="APP_ASSISTANT_MAX_REQUESTS"
    )
    assistant_window_seconds: int = Field(
        default=60, ge=1, le=3600, validation_alias="APP_ASSISTANT_WINDOW_SECONDS"
    )

    app_env: str = Field(
        default="local",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/thinkmedia",
        validation_alias=AliasChoices("DATABASE_URL", "APP_DATABASE_URL"),
    )
    allowed_origins: Annotated[str, NoDecode] = Field(
        default=DEFAULT_ALLOWED_ORIGINS,
        validation_alias=AliasChoices(
            "APP_ALLOWED_ORIGINS", "ALLOWED_ORIGINS", "CORS_ALLOWED_ORIGINS"
        ),
    )

    session_cookie_name: str = Field(
        default="tm_session",
        validation_alias=AliasChoices("APP_SESSION_COOKIE_NAME"),
    )
    session_ttl_hours: int = Field(
        default=8,
        ge=1,
        le=24 * 30,
        validation_alias=AliasChoices("APP_SESSION_TTL_HOURS"),
    )
    cookie_secure: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("APP_COOKIE_SECURE"),
    )
    csrf_secret: str = Field(
        default_factory=lambda: secrets.token_urlsafe(48),
        validation_alias=AliasChoices("APP_CSRF_SECRET"),
    )
    csrf_header_name: str = Field(
        default="X-CSRF-Token",
        validation_alias=AliasChoices("APP_CSRF_HEADER_NAME"),
    )

    max_request_body_bytes: int = Field(
        default=64 * 1024,
        ge=1024,
        le=10 * 1024 * 1024,
        validation_alias=AliasChoices("APP_MAX_REQUEST_BODY_BYTES"),
    )

    login_max_failures: int = Field(
        default=5,
        ge=1,
        validation_alias=AliasChoices("APP_LOGIN_MAX_FAILURES"),
    )
    login_window_seconds: int = Field(
        default=15 * 60,
        ge=1,
        validation_alias=AliasChoices("APP_LOGIN_WINDOW_SECONDS"),
    )
    register_max_attempts: int = Field(
        default=20,
        ge=1,
        validation_alias=AliasChoices("APP_REGISTER_MAX_ATTEMPTS"),
    )
    register_window_seconds: int = Field(
        default=60 * 60,
        ge=1,
        validation_alias=AliasChoices("APP_REGISTER_WINDOW_SECONDS"),
    )

    trusted_proxy_headers: bool = Field(
        default=False,
        validation_alias=AliasChoices("APP_TRUSTED_PROXY_HEADERS"),
    )

    @field_validator("app_env")
    @classmethod
    def _normalize_env(cls, value: str) -> str:
        return value.strip().lower()

    @property
    def origin_set(self) -> frozenset[str]:
        return frozenset(
            part.strip().rstrip("/")
            for part in self.allowed_origins.split(",")
            if part.strip()
        )

    @property
    def local_http_mode(self) -> bool:
        return self.app_env in {"local", "test", "development"}

    @property
    def cookie_secure_enabled(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        # Secure is mandatory outside an explicit local/test HTTP mode.
        return not self.local_http_mode

    @property
    def session_ttl_seconds(self) -> int:
        return self.session_ttl_hours * 60 * 60

    def client_ip(self, peer_host: str | None, forwarded_for: str | None) -> str:
        """Return the client address used for throttling.

        ``X-Forwarded-For`` is only honoured when the operator explicitly
        declares the app is behind a trusted proxy. Otherwise a client could
        spoof the header and evade throttles.
        """

        if self.trusted_proxy_headers and forwarded_for:
            first = forwarded_for.split(",")[0].strip()
            if first:
                return first
        return peer_host or "unknown"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Test hook: clear the cached settings instance."""

    get_settings.cache_clear()
