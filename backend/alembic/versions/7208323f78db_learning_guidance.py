"""FR03/10/11 learning, immutable quiz keys and audited moderation.

Revision ID: 7208323f78db
Revises: 4b1f750c284b
Create Date: 2026-11-06 00:00:11.366755
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7208323f78db"
down_revision: str | None = "4b1f750c284b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learning_content",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("body", sa.String(length=20000), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft','published','archived')",
            name=op.f("ck_learning_content_status_allowed"),
        ),
        sa.CheckConstraint(
            "cardinality(tags)<=30", name=op.f("ck_learning_content_tags_count")
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name=op.f("fk_learning_content_author_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_content")),
    )
    op.create_index(
        op.f("ix_learning_content_status"), "learning_content", ["status"], unique=False
    )
    op.create_table(
        "content_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("detail", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_content_events_actor_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["learning_content.id"],
            name=op.f("fk_content_events_content_id_learning_content"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_events")),
    )
    op.create_index(
        op.f("ix_content_events_content_id"),
        "content_events",
        ["content_id"],
        unique=False,
    )
    op.create_table(
        "content_states",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("saved", sa.Boolean(), nullable=False),
        sa.Column("reacted", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["learning_content.id"],
            name=op.f("fk_content_states_content_id_learning_content"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_content_states_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "content_id", name=op.f("pk_content_states")
        ),
    )
    op.create_table(
        "moderation_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("reporter_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.String(length=1000), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("resolution", sa.String(length=1000), nullable=True),
        sa.Column("resolved_by", sa.Uuid(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(status='pending' AND resolved_by IS NULL AND resolved_at IS NULL AND resolution IS NULL) OR (status='resolved' AND resolved_by IS NOT NULL AND resolved_at IS NOT NULL AND resolution IS NOT NULL)",
            name=op.f("ck_moderation_reports_resolution_consistent"),
        ),
        sa.CheckConstraint(
            "status IN ('pending','resolved')",
            name=op.f("ck_moderation_reports_status_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["learning_content.id"],
            name=op.f("fk_moderation_reports_content_id_learning_content"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_id"],
            ["users.id"],
            name=op.f("fk_moderation_reports_reporter_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by"],
            ["users.id"],
            name=op.f("fk_moderation_reports_resolved_by_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_moderation_reports")),
    )
    op.create_index(
        op.f("ix_moderation_reports_content_id"),
        "moderation_reports",
        ["content_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_moderation_reports_status"),
        "moderation_reports",
        ["status"],
        unique=False,
    )
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("answers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "total>0 AND correct>=0 AND correct<=total",
            name=op.f("ck_quiz_attempts_score_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["learning_content.id"],
            name=op.f("fk_quiz_attempts_content_id_learning_content"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_quiz_attempts_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quiz_attempts")),
    )
    op.create_index(
        op.f("ix_quiz_attempts_content_id"),
        "quiz_attempts",
        ["content_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_quiz_attempts_user_id"), "quiz_attempts", ["user_id"], unique=False
    )
    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("question", sa.String(length=1000), nullable=False),
        sa.Column("options", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "cardinality(options) BETWEEN 2 AND 6",
            name=op.f("ck_quiz_questions_options_count"),
        ),
        sa.CheckConstraint(
            "correct_index >= 0 AND correct_index < cardinality(options)",
            name=op.f("ck_quiz_questions_correct_index_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["learning_content.id"],
            name=op.f("fk_quiz_questions_content_id_learning_content"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quiz_questions")),
        sa.UniqueConstraint(
            "content_id", "position", name=op.f("uq_quiz_questions_content_id")
        ),
    )
    op.create_index(
        op.f("ix_quiz_questions_content_id"),
        "quiz_questions",
        ["content_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_quiz_questions_content_id"), table_name="quiz_questions")
    op.drop_table("quiz_questions")
    op.drop_index(op.f("ix_quiz_attempts_user_id"), table_name="quiz_attempts")
    op.drop_index(op.f("ix_quiz_attempts_content_id"), table_name="quiz_attempts")
    op.drop_table("quiz_attempts")
    op.drop_index(op.f("ix_moderation_reports_status"), table_name="moderation_reports")
    op.drop_index(
        op.f("ix_moderation_reports_content_id"), table_name="moderation_reports"
    )
    op.drop_table("moderation_reports")
    op.drop_table("content_states")
    op.drop_index(op.f("ix_content_events_content_id"), table_name="content_events")
    op.drop_table("content_events")
    op.drop_index(op.f("ix_learning_content_status"), table_name="learning_content")
    op.drop_table("learning_content")
