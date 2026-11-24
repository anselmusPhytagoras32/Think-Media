"""Session-bound assistant previews and execution records (FR10/NFR02/04)."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision = "0010_assistant_actions"
down_revision = "0009_instructor_learning"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "assistant_actions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("arguments", JSONB(), nullable=False),
        sa.Column("precondition", sa.String(64)),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("result", JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'executed', 'cancelled')", name="status_allowed"),
    )
    op.create_index("ix_assistant_actions_actor_created", "assistant_actions", ["actor_id", "created_at"])


def downgrade():
    op.drop_table("assistant_actions")
