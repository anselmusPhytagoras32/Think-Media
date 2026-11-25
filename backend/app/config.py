"""Runtime configuration.

Secrets are read from the environment (or local, git-ignored dotenv files).
The defaults below are safe for local HTTP development only; nothing here is a
deployment secret.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import make_url

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
        # FR10/NFR02: local server-only overrides; process variables still win.
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    recommender_alpha: float = Field(
        default=0.5,
        ge=0,
        le=1,
        allow_inf_nan=False,
        validation_alias="APP_RECOMMENDER_ALPHA",
    )

    assistant_mode: Literal["disabled", "retrieval", "external"] = Field(
        default="disabled", validation_alias="APP_ASSISTANT_MODE"
    )
    assistant_provider_profile: Literal["openai", "gemini", "groq", "openrouter", "groq_openrouter"] = Field(
        default="openai", validation_alias="APP_ASSISTANT_PROVIDER_PROFILE"
    )
    assistant_reasoning_effort: Literal["low", "medium", "high"] = Field(
        default="low", validation_alias="APP_ASSISTANT_REASONING_EFFORT"
    )
    # FR10/NFR02/11: explicit operator configuration, never supplied by a client.
    assistant_endpoint: str = Field(
        default="", max_length=2048, validation_alias="APP_ASSISTANT_ENDPOINT"
    )
    assistant_model: str = Field(
        default="", max_length=200, validation_alias="APP_ASSISTANT_MODEL"
    )
    assistant_api_key: SecretStr = Field(
        default=SecretStr(""), repr=False, validation_alias="APP_ASSISTANT_API_KEY"
    )
    groq_api_key: SecretStr = Field(default=SecretStr(""), repr=False, validation_alias="GROQ_API_KEY")
    openrouter_api_key: SecretStr = Field(default=SecretStr(""), repr=False, validation_alias="OPENROUTER_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-20b", min_length=1, max_length=200, validation_alias="GROQ_MODEL")
    openrouter_model: str = Field(default="nvidia/nemotron-3.5-super-vl:free", min_length=1, max_length=200, validation_alias="OPENROUTER_MODEL")
    assistant_timeout_seconds: float = Field(
        default=10, ge=1, le=30, allow_inf_nan=False,
        validation_alias="APP_ASSISTANT_TIMEOUT_SECONDS",
    )
    assistant_max_completion_tokens: int = Field(
        default=512, ge=64, le=2048,
        validation_alias="APP_ASSISTANT_MAX_COMPLETION_TOKENS",
    )
    assistant_call_budget: int = Field(
        default=0, ge=0, le=10000, validation_alias="APP_ASSISTANT_CALL_BUDGET"
    )
    assistant_max_requests: int = Field(
        default=10, ge=1, le=100, validation_alias="APP_ASSISTANT_MAX_REQUESTS"
    )
    assistant_window_seconds: int = Field(
        default=60, ge=1, le=3600, validation_alias="APP_ASSISTANT_WINDOW_SECONDS"
    )
    assistant_tools_enabled: bool = Field(default=True, validation_alias="APP_ASSISTANT_TOOLS_ENABLED")

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
    public_origin: str = Field(
        default="",
        validation_alias=AliasChoices("APP_PUBLIC_ORIGIN", "RENDER_EXTERNAL_URL"),
    )
    frontend_dist: str = Field(default="", validation_alias="APP_FRONTEND_DIST")
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

    @field_validator("assistant_endpoint")
    @classmethod
    def _assistant_endpoint(cls, value: str) -> str:
        value = value.strip()
        if value:
            parsed = urlsplit(value)
            if (
                parsed.scheme != "https" or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or not parsed.path.endswith("/chat/completions")
            ):
                raise ValueError("Use an HTTPS chat/completions endpoint without URL credentials or query parameters.")
        return value

    @field_validator("app_env")
    @classmethod
    def _normalize_env(cls, value: str) -> str:
        return value.strip().lower()

    @property
    def assistant_effective_endpoint(self) -> str:
        if self.assistant_provider_profile == "gemini" and not self.assistant_endpoint:
            return "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        return self.assistant_endpoint

    @field_validator("database_url")
    @classmethod
    def _database_url(cls, value: str) -> str:
        try:
            url = make_url(value)
            if url.drivername in {"postgres", "postgresql"}:
                url = url.set(drivername="postgresql+psycopg")
            if url.drivername != "postgresql+psycopg" or not url.database:
                raise ValueError
            return url.render_as_string(hide_password=False)
        except Exception:
            raise ValueError("Use a PostgreSQL connection URL with a database name.") from None

    @field_validator("public_origin")
    @classmethod
    def _public_origin(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if value:
            parsed = urlsplit(value)
            if (
                parsed.scheme != "https" or not parsed.hostname
                or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment
            ):
                raise ValueError("Use an HTTPS application origin.")
        return value

    @property
    def assistant_effective_model(self) -> str:
        if self.assistant_provider_profile == "gemini" and not self.assistant_model.strip():
            return "gemini-3.8-flash"
        return self.assistant_model.strip()

    @property
    def origin_set(self) -> frozenset[str]:
        origins = frozenset(
            part.strip().rstrip("/")
            for part in self.allowed_origins.split(",")
            if part.strip()
        )
        return origins | {self.public_origin} if self.public_origin else origins

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
