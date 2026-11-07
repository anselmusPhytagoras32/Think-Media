"""FR08–09 typed actual interactions and unique latest explicit ratings.

Revision ID: a7eed17d111a
Revises: 7208323f78db
Create Date: 2026-11-06 00:07:13.073374
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a7eed17d111a"
down_revision: str | None = "7208323f78db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=True),
        sa.Column("content_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=10), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(event_type='view' AND rating IS NULL) OR (event_type='rating' AND rating BETWEEN 1 AND 5 AND rating IS NOT NULL)",
            name=op.f("ck_interactions_event_rating_valid"),
        ),
        sa.CheckConstraint(
            "(listing_id IS NOT NULL AND content_id IS NULL) OR (listing_id IS NULL AND content_id IS NOT NULL)",
            name=op.f("ck_interactions_one_item"),
        ),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["learning_content.id"],
            name=op.f("fk_interactions_content_id_learning_content"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
            name=op.f("fk_interactions_listing_id_listings"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_interactions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interactions")),
    )
    op.create_index(
        op.f("ix_interactions_content_id"), "interactions", ["content_id"], unique=False
    )
    op.create_index(
        op.f("ix_interactions_listing_id"), "interactions", ["listing_id"], unique=False
    )
    op.create_index(
        op.f("ix_interactions_user_id"), "interactions", ["user_id"], unique=False
    )
    op.create_index(
        "uq_interactions_content_rating",
        "interactions",
        ["user_id", "content_id"],
        unique=True,
        postgresql_where=sa.text("event_type='rating'"),
    )
    op.create_index(
        "uq_interactions_listing_rating",
        "interactions",
        ["user_id", "listing_id"],
        unique=True,
        postgresql_where=sa.text("event_type='rating'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_interactions_listing_rating",
        table_name="interactions",
        postgresql_where=sa.text("event_type='rating'"),
    )
    op.drop_index(
        "uq_interactions_content_rating",
        table_name="interactions",
        postgresql_where=sa.text("event_type='rating'"),
    )
    op.drop_index(op.f("ix_interactions_user_id"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_listing_id"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_content_id"), table_name="interactions")
    op.drop_table("interactions")
