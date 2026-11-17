"""Migration upgrade/downgrade/re-upgrade against a disposable real database."""

from __future__ import annotations

import uuid
from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from alembic import command

BACKEND_ROOT = Path(__file__).resolve().parents[1]
APP_TABLES = {
    "users",
    "student_profiles",
    "instructor_profiles",
    "company_profiles",
    "sessions",
    "audit_events",
    "listings",
    "applications",
    "application_status_history",
    "marketplace_events",
    "learning_content",
    "quiz_questions",
    "learning_submissions",
    "learning_reviews",
    "quiz_attempts",
    "content_states",
    "moderation_reports",
    "content_events",
    "interactions",
    "satisfaction_feedback",
    "attachment_retention_events",
}


def _config(database_url: str) -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def _constraint_names(engine, table: str) -> set[str]:
    with engine.connect() as connection:
        return set(
            connection.execute(
                text(
                    "SELECT conname FROM pg_constraint "
                    "WHERE conrelid = to_regclass(:table)"
                ),
                {"table": table},
            ).scalars()
        )


def _trigger_names(engine, table: str) -> set[str]:
    with engine.connect() as connection:
        return set(
            connection.execute(
                text(
                    "SELECT tgname FROM pg_trigger "
                    "WHERE NOT tgisinternal AND tgrelid = to_regclass(:table)"
                ),
                {"table": table},
            ).scalars()
        )


def test_migration_upgrade_downgrade_reupgrade(database_url: str):
    url = make_url(database_url)
    db_name = f"tm_migration_{uuid.uuid4().hex[:12]}"
    admin_engine = create_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    temp_engine = None

    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{db_name}"'))

    # NFR06: str(URL) redacts the password and cannot open a new connection.
    temp_url = url.set(database=db_name).render_as_string(hide_password=False)
    cfg = _config(temp_url)

    try:
        # FR02: upgrading a populated foundation preserves existing profiles.
        command.upgrade(cfg, "0001_phase1_foundation")
        temp_engine = create_engine(temp_url)
        with temp_engine.begin() as connection:
            existing_id = uuid.uuid4()
            connection.execute(text("INSERT INTO users (id,email,password_hash,display_name,role) VALUES (:id,'migration@example.org','unused','Existing Student','student')"), {"id": existing_id})
            connection.execute(text("INSERT INTO student_profiles (user_id,program) VALUES (:id,'BSCS')"), {"id": existing_id})
        command.upgrade(cfg, "head")
        with temp_engine.connect() as connection:
            preserved = connection.execute(text("SELECT program, location, background FROM student_profiles WHERE user_id=:id"), {"id": existing_id}).one()
            assert tuple(preserved) == ("BSCS", "", "")
        inspector = inspect(temp_engine)
        tables = set(inspector.get_table_names())
        assert APP_TABLES <= tables
        assert "alembic_version" in tables

        users_constraints = _constraint_names(temp_engine, "users")
        assert "ck_users_role_allowed" in users_constraints
        assert "ck_users_email_normalized" in users_constraints
        assert "uq_users_email" in users_constraints

        company_constraints = _constraint_names(temp_engine, "company_profiles")
        assert "ck_company_profiles_verification_status_allowed" in company_constraints
        assert "ck_company_profiles_verification_version_positive" in company_constraints
        assert "uq_company_profiles_user_id" in company_constraints
        assert "fk_company_profiles_user_id_users" in company_constraints

        session_constraints = _constraint_names(temp_engine, "sessions")
        assert "ck_sessions_expiry_after_creation" in session_constraints
        assert "uq_sessions_token_hash" in session_constraints

        assert "trg_student_profiles_role" in _trigger_names(
            temp_engine, "student_profiles"
        )
        assert "trg_instructor_profiles_role" in _trigger_names(
            temp_engine, "instructor_profiles"
        )
        assert "trg_company_profiles_role" in _trigger_names(
            temp_engine, "company_profiles"
        )

        indexes = {
            index["name"] for index in inspector.get_indexes("company_profiles")
        }
        assert "ix_company_profiles_status_created_at" in indexes
        assert "ix_sessions_user_id" in {
            index["name"] for index in inspector.get_indexes("sessions")
        }

        temp_engine.dispose()
        temp_engine = None

        # Roll back every table, then apply again on the same disposable DB.
        command.downgrade(cfg, "base")
        temp_engine = create_engine(temp_url)
        remaining = set(inspect(temp_engine).get_table_names())
        assert not (APP_TABLES & remaining)
        temp_engine.dispose()
        temp_engine = None

        command.upgrade(cfg, "head")
        temp_engine = create_engine(temp_url)
        assert APP_TABLES <= set(inspect(temp_engine).get_table_names())
        # The profile-role trigger function was recreated with the schema.
        with temp_engine.connect() as connection:
            function_exists = connection.execute(
                text(
                    "SELECT count(*) FROM pg_proc WHERE proname = 'enforce_profile_role'"
                )
            ).scalar_one()
            assert function_exists == 1
    finally:
        if temp_engine is not None:
            temp_engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
        admin_engine.dispose()
