"""Shared pytest fixtures: real PostgreSQL, migrated schema, application factory."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from alembic import command
from app.config import Settings
from app.main import create_app

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


def alembic_config(database_url: str) -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


@pytest.fixture(scope="session")
def database_url() -> str:
    if not DATABASE_URL:
        pytest.fail(
            "Set TEST_DATABASE_URL explicitly to a disposable PostgreSQL "
            "database before running backend tests.",
            pytrace=False,
        )
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.fail(
            f"Cannot connect to TEST_DATABASE_URL ({exc.__class__.__name__}). "
            "Start a disposable PostgreSQL instance first.",
            pytrace=False,
        )
    finally:
        engine.dispose()

    command.upgrade(alembic_config(DATABASE_URL), "head")
    return DATABASE_URL


@pytest.fixture(scope="session")
def settings(database_url: str) -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=database_url,
        allowed_origins="http://testserver",
        csrf_secret="test-only-csrf-secret-not-for-deployment",
        session_ttl_hours=8,
        cookie_secure=False,
        # FR10: default-provider tests must not inherit the local API mode.
        assistant_mode="disabled",
        login_max_failures=5,
        login_window_seconds=900,
        register_max_attempts=1000,
        register_window_seconds=3600,
        max_request_body_bytes=64 * 1024,
    )


@pytest.fixture()
def app(settings: Settings):
    application = create_app(settings)
    yield application
    application.state.engine.dispose()


@pytest.fixture()
def client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture()
def db(app):
    session = app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def clean_database(database_url: str):
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE audit_events, sessions, company_profiles, "
                "instructor_profiles, student_profiles, users RESTART IDENTITY CASCADE"
            )
        )
    engine.dispose()
    yield
