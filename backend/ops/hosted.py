"""Migrate and start the hosted demo. Secrets come only from runtime variables."""

import os
from pathlib import Path
import sys
from uuid import NAMESPACE_URL, UUID, uuid5

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.config import Settings
from app.db import build_engine, build_session_factory
from app.models import User
from app.validation import validate_password
from ops.learning_demo import seed_examples
from ops.demo_catalog import seed_catalog, catalog_password
from ops.presentation_accounts import ROLES, create_accounts, verify_ownership


def bootstrap_demo(db):
    """Preserve seeded accounts and edits across ephemeral container restarts."""
    manifest = {
        "accounts": {
            role: dict(
                id=str(uuid5(NAMESPACE_URL, f"thinkmedia:hosted-demo:{role}")),
                email=f"presentation-{role}@example.test",
                password=validate_password(os.environ[f"APP_DEMO_{role.upper()}_PASSWORD"]),
            )
            for role in ROLES
        },
    }
    db.execute(text("SELECT pg_advisory_xact_lock(2026112301)"))
    verify_ownership(db, manifest)
    create_accounts(db, manifest)
    instructor = db.get(User, UUID(manifest["accounts"]["instructor"]["id"]))
    administrator = db.get(User, UUID(manifest["accounts"]["administrator"]["id"]))
    seed_catalog(db, administrator, catalog_password(manifest["accounts"]["company"]["password"]))
    return seed_examples(db, instructor, administrator)


def prepare(settings):
    engine = build_engine(settings)
    try:
        # Old and new instances can overlap during a deploy. Hold a session
        # advisory lock while the independent Alembic connection migrates.
        with engine.connect() as guard:
            guard.execute(text("SELECT pg_advisory_lock(2026112300)"))
            try:
                config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
                config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
                config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
                command.upgrade(config, "head")
                if os.environ.get("APP_BOOTSTRAP_DEMO") == "true":
                    if settings.app_env != "demo":
                        raise ValueError("Demo bootstrap requires APP_ENV=demo.")
                    with build_session_factory(engine)() as db, db.begin():
                        bootstrap_demo(db)
            finally:
                guard.execute(text("SELECT pg_advisory_unlock(2026112300)"))
    finally:
        engine.dispose()


def main():
    try:
        settings = Settings()
        prepare(settings)
        port = int(os.environ.get("PORT", "10000"))
        if not 1 <= port <= 65535:
            raise ValueError("Invalid port.")
    except Exception as failure:
        # SQL/validation errors can contain connection strings or credentials.
        print(f"Hosted startup failed ({type(failure).__name__}). Check database and runtime settings.", file=sys.stderr)
        raise SystemExit(1) from None
    print("Database migrations and hosted initialization complete.", flush=True)
    os.execv(sys.executable, [
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0", "--port", str(port), "--workers", "1",
    ])


if __name__ == "__main__":
    main()
