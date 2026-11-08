"""NFR02/03/11: no implicit DB target, aggregate-only reports, atomic expiry."""

from datetime import datetime, timedelta, timezone
import json
import uuid

import pytest
from sqlalchemy import create_engine, text

from ops import maintenance


@pytest.mark.parametrize("app_env,url", [
    ("", "postgresql+psycopg://localhost/demo"),
    ("production", "postgresql+psycopg://localhost/demo"),
    ("local", ""),
    ("local", "postgresql+psycopg://remote.example/demo"),
    ("local", "sqlite:///demo"),
    ("local", "postgresql+psycopg://localhost/demo?host=remote.example"),
])
def test_rejects_implicit_remote_or_production_configuration(monkeypatch, app_env, url):
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("DATABASE_URL", url)
    with pytest.raises(ValueError):
        maintenance.local_database_url()


@pytest.fixture()
def maintenance_database(monkeypatch, database_url):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", database_url)
    engine = create_engine(database_url)
    now = datetime.now(timezone.utc)
    # Anonymous sessions are sufficient and avoid adding private account data.
    with engine.begin() as connection:
        for expired in (True, False):
            connection.execute(text(
                "INSERT INTO sessions (id, token_hash, created_at, expires_at) "
                "VALUES (:id, :hash, :created, :expiry)"
            ), {
                "id": uuid.uuid4(), "hash": ("a" if expired else "b") * 64,
                "created": now - timedelta(days=2),
                "expiry": now - timedelta(days=1) if expired else now + timedelta(days=1),
            })
    yield engine
    engine.dispose()


def test_default_report_is_aggregate_and_does_not_delete(maintenance_database):
    report = maintenance.run()
    assert report["mode"] == "read_only"
    assert report["deleted_sessions"] == 0
    assert report["expired_sessions"] == 1
    assert report["row_counts"]["sessions"] == 2
    assert report["database_bytes"] > 0
    assert report["private_attachment_bytes"] == 0
    assert "a" * 64 not in json.dumps(report)
    with maintenance_database.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM sessions")) == 2


def test_explicit_prune_preserves_valid_sessions_and_other_tables(maintenance_database):
    before = maintenance.run()["row_counts"]
    report = maintenance.run(prune_expired_sessions=True)
    assert report["deleted_sessions"] == 1
    assert report["expired_sessions"] == 0
    assert report["row_counts"]["sessions"] == 1
    assert {k: v for k, v in report["row_counts"].items() if k != "sessions"} == {
        k: v for k, v in before.items() if k != "sessions"
    }


def test_failure_after_delete_rolls_back(maintenance_database, monkeypatch):
    def fail(*args):
        raise RuntimeError("Injected report failure")
    monkeypatch.setattr(maintenance, "snapshot", fail)
    with pytest.raises(RuntimeError, match="Injected"):
        maintenance.run(prune_expired_sessions=True)
    with maintenance_database.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM sessions")) == 2
