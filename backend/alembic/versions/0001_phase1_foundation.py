"""Phase 1 foundation schema.

Revision ID: 0001_phase1_foundation
Revises:
Create Date: 2026-11-05

Creates users, role-specific profiles, opaque sessions and audit events.
Includes CHECK constraints for roles/statuses, foreign keys, a normalized-email
uniqueness constraint and triggers that prevent a profile row from being stored
under the wrong role (instructors are never students).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_phase1_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint(
            "role IN ('student', 'instructor', 'company', 'administrator')",
            name="role_allowed",
        ),
        sa.CheckConstraint(
            "char_length(email) BETWEEN 3 AND 254", name="email_length"
        ),
        sa.CheckConstraint("email = lower(email)", name="email_normalized"),
        sa.CheckConstraint(
            "char_length(display_name) BETWEEN 1 AND 100",
            name="display_name_length",
        ),
    )

    op.create_table(
        "student_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "institution",
            sa.String(length=200),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column(
            "program",
            sa.String(length=200),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column(
            "skills",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "interests",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_student_profiles_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_student_profiles"),
        sa.CheckConstraint(
            "char_length(institution) <= 200",
            name="institution_length",
        ),
        sa.CheckConstraint(
            "char_length(program) <= 200", name="program_length"
        ),
        sa.CheckConstraint(
            "cardinality(skills) <= 30", name="skills_count"
        ),
        sa.CheckConstraint(
            "cardinality(interests) <= 30", name="interests_count"
        ),
    )

    op.create_table(
        "instructor_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "institution",
            sa.String(length=200),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_instructor_profiles_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_instructor_profiles"),
        sa.CheckConstraint(
            "char_length(institution) <= 200",
            name="institution_length",
        ),
    )

    op.create_table(
        "company_profiles",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column(
            "description",
            sa.String(length=2000),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column(
            "location",
            sa.String(length=200),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column("website", sa.String(length=2048), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "verification_version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_company_profiles_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_company_profiles"),
        sa.UniqueConstraint("user_id", name="uq_company_profiles_user_id"),
        sa.CheckConstraint(
            "verification_status IN ('pending', 'verified', 'rejected')",
            name="verification_status_allowed",
        ),
        sa.CheckConstraint(
            "verification_version >= 1",
            name="verification_version_positive",
        ),
        sa.CheckConstraint(
            "char_length(company_name) BETWEEN 1 AND 200",
            name="company_name_length",
        ),
        sa.CheckConstraint(
            "char_length(description) <= 2000",
            name="description_length",
        ),
        sa.CheckConstraint(
            "char_length(location) <= 200",
            name="location_length",
        ),
        sa.CheckConstraint(
            "website IS NULL OR char_length(website) <= 2048",
            name="website_length",
        ),
    )
    op.create_index(
        "ix_company_profiles_status_created_at",
        "company_profiles",
        ["verification_status", "created_at"],
        unique=False,
    )

    op.create_table(
        "sessions",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_sessions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_sessions"),
        sa.UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
        sa.CheckConstraint(
            "expires_at > created_at", name="expiry_after_creation"
        ),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"], unique=False)
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("old_status", sa.String(length=20), nullable=True),
        sa.Column("new_status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name="fk_audit_events_actor_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
        sa.CheckConstraint(
            "char_length(action) BETWEEN 1 AND 100",
            name="action_length",
        ),
        sa.CheckConstraint(
            "old_status IS NULL OR old_status IN ('pending', 'verified', 'rejected')",
            name="old_status_allowed",
        ),
        sa.CheckConstraint(
            "new_status IN ('verified', 'rejected')",
            name="new_status_allowed",
        ),
        sa.CheckConstraint(
            "char_length(reason) BETWEEN 1 AND 1000",
            name="reason_length",
        ),
    )
    op.create_index(
        "ix_audit_events_created_at_id",
        "audit_events",
        ["created_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_actor_id", "audit_events", ["actor_id"], unique=False
    )
    op.create_index(
        "ix_audit_events_target_id", "audit_events", ["target_id"], unique=False
    )

    # Defence in depth: a student profile cannot be attached to an instructor
    # account (or vice versa). The application already inserts the matching
    # profile atomically; this trigger protects direct/legacy writes too.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_profile_role() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
            expected_role text;
        BEGIN
            expected_role := TG_ARGV[0];
            IF NOT EXISTS (
                SELECT 1 FROM users
                WHERE id = NEW.user_id AND role = expected_role
            ) THEN
                RAISE EXCEPTION
                    'profile role mismatch: % requires user role %',
                    TG_TABLE_NAME, expected_role
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        "CREATE TRIGGER trg_student_profiles_role "
        "BEFORE INSERT OR UPDATE ON student_profiles "
        "FOR EACH ROW EXECUTE FUNCTION enforce_profile_role('student')"
    )
    op.execute(
        "CREATE TRIGGER trg_instructor_profiles_role "
        "BEFORE INSERT OR UPDATE ON instructor_profiles "
        "FOR EACH ROW EXECUTE FUNCTION enforce_profile_role('instructor')"
    )
    op.execute(
        "CREATE TRIGGER trg_company_profiles_role "
        "BEFORE INSERT OR UPDATE ON company_profiles "
        "FOR EACH ROW EXECUTE FUNCTION enforce_profile_role('company')"
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_company_profiles_role ON company_profiles"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_instructor_profiles_role ON instructor_profiles"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_student_profiles_role ON student_profiles"
    )
    op.execute("DROP FUNCTION IF EXISTS enforce_profile_role()")

    op.drop_index("ix_audit_events_target_id", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_id", table_name="audit_events")
    op.drop_index("ix_audit_events_created_at_id", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_sessions_expires_at", table_name="sessions")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index(
        "ix_company_profiles_status_created_at", table_name="company_profiles"
    )
    op.drop_table("company_profiles")

    op.drop_table("instructor_profiles")
    op.drop_table("student_profiles")
    op.drop_table("users")
