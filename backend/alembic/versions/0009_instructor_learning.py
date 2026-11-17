"""FR03/11: instructor learning submissions and review history."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0009_instructor_learning"
down_revision = "0008_feedback_external_mode"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("quiz_questions", sa.Column("feedback", sa.String(1000), nullable=True))
    op.create_table(
        "learning_submissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("attachment_name", sa.String(200)),
        sa.Column("attachment", sa.LargeBinary()),
        sa.Column("published_content_id", sa.Uuid(), sa.ForeignKey("learning_content.id", ondelete="RESTRICT"), unique=True),
        sa.Column("approved_skill_key", sa.Text(), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('lesson', 'skill')", name="kind_allowed"),
        sa.CheckConstraint("status IN ('draft', 'pending', 'changes_requested', 'approved')", name="status_allowed"),
        sa.CheckConstraint("version >= 1", name="version_positive"),
        sa.CheckConstraint("(attachment IS NULL) = (attachment_name IS NULL)", name="attachment_pair"),
        sa.CheckConstraint("kind = 'lesson' OR attachment IS NULL", name="lesson_attachment"),
        sa.CheckConstraint(
            "(published_content_id IS NOT NULL) = (kind = 'lesson' AND status = 'approved')",
            name="published_content",
        ),
        sa.CheckConstraint(
            "(approved_skill_key IS NOT NULL) = (kind = 'skill' AND status = 'approved')",
            name="approved_skill",
        ),
    )
    op.create_index("ix_learning_submissions_author_updated", "learning_submissions", ["author_id", "updated_at", "id"])
    op.create_index("ix_learning_submissions_status_updated", "learning_submissions", ["status", "updated_at", "id"])
    op.create_table(
        "learning_reviews",
        sa.Column("submission_id", sa.Uuid(), sa.ForeignKey("learning_submissions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("submitted_version", sa.Integer(), primary_key=True),
        sa.Column("reviewer_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("feedback", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("decision IN ('approved', 'changes_requested')", name="decision_allowed"),
    )


def downgrade():
    op.drop_table("learning_reviews")
    op.drop_table("learning_submissions")
    op.drop_column("quiz_questions", "feedback")
