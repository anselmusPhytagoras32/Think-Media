"""FR04–07 private marketplace and atomic history (NFR02–04,06).

Revision ID: 4b1f750c284b
Revises: 0002_profile_details
Create Date: 2026-11-05 23:43:09.039864
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "4b1f750c284b"
down_revision: str | None = "0002_profile_details"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "listings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=10000), nullable=False),
        sa.Column("requirements", sa.String(length=10000), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("skills", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft','published','closed')",
            name=op.f("ck_listings_status_allowed"),
        ),
        sa.CheckConstraint(
            "type IN ('ojt','job')", name=op.f("ck_listings_type_allowed")
        ),
        sa.CheckConstraint(
            "cardinality(skills) <= 30", name=op.f("ck_listings_skills_count")
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["company_profiles.id"],
            name=op.f("fk_listings_company_id_company_profiles"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_listings")),
    )
    op.create_index(
        op.f("ix_listings_company_id"), "listings", ["company_id"], unique=False
    )
    op.create_index(op.f("ix_listings_status"), "listings", ["status"], unique=False)
    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reference", sa.String(length=40), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("cover_letter", sa.String(length=5000), nullable=False),
        sa.Column("attachment_name", sa.String(length=200), nullable=False),
        sa.Column("attachment", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('submitted','under_review','accepted','rejected')",
            name=op.f("ck_applications_status_allowed"),
        ),
        sa.CheckConstraint(
            "octet_length(attachment) BETWEEN 1 AND 5242880",
            name=op.f("ck_applications_attachment_size"),
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
            name=op.f("fk_applications_listing_id_listings"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.id"],
            name=op.f("fk_applications_student_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
        sa.UniqueConstraint("reference", name=op.f("uq_applications_reference")),
        sa.UniqueConstraint(
            "student_id", "listing_id", name="uq_application_student_listing"
        ),
    )
    op.create_index(
        op.f("ix_applications_listing_id"), "applications", ["listing_id"], unique=False
    )
    op.create_index(
        op.f("ix_applications_student_id"), "applications", ["student_id"], unique=False
    )
    op.create_table(
        "marketplace_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("old_status", sa.String(length=20), nullable=True),
        sa.Column("new_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_marketplace_events_actor_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
            name=op.f("fk_marketplace_events_listing_id_listings"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_marketplace_events")),
    )
    op.create_index(
        op.f("ix_marketplace_events_listing_id"),
        "marketplace_events",
        ["listing_id"],
        unique=False,
    )
    op.create_table(
        "application_status_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("old_status", sa.String(length=20), nullable=True),
        sa.Column("new_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "new_status IN ('submitted','under_review','accepted','rejected')",
            name=op.f("ck_application_status_history_new_status_allowed"),
        ),
        sa.CheckConstraint(
            "old_status IS NULL OR old_status IN ('submitted','under_review','accepted','rejected')",
            name=op.f("ck_application_status_history_old_status_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_application_status_history_actor_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_application_status_history_application_id_applications"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_status_history")),
    )
    op.create_index(
        op.f("ix_application_status_history_application_id"),
        "application_status_history",
        ["application_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_application_status_history_application_id"),
        table_name="application_status_history",
    )
    op.drop_table("application_status_history")
    op.drop_index(
        op.f("ix_marketplace_events_listing_id"), table_name="marketplace_events"
    )
    op.drop_table("marketplace_events")
    op.drop_index(op.f("ix_applications_student_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_listing_id"), table_name="applications")
    op.drop_table("applications")
    op.drop_index(op.f("ix_listings_status"), table_name="listings")
    op.drop_index(op.f("ix_listings_company_id"), table_name="listings")
    op.drop_table("listings")
