"""FR05/11; NFR03/04/06/11: additive private attachment tombstones and audit.

No existing bytes expire during upgrade. Policy execution is a separate explicit
operator action. A downgrade cannot reconstruct bytes and refuses expiry data.
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_attachment_retention"
down_revision = "0006_satisfaction_feedback"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("applications", sa.Column("attachment_deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("applications", "attachment", existing_type=sa.LargeBinary(), nullable=True)
    op.create_check_constraint(op.f("ck_applications_attachment_state"), "applications",
        "(attachment IS NOT NULL AND attachment_deleted_at IS NULL) OR "
        "(attachment IS NULL AND attachment_deleted_at IS NOT NULL)")
    op.create_table(
        "attachment_retention_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("policy_reference", sa.String(200), nullable=False),
        sa.Column("byte_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attachment_retention_events")),
        sa.UniqueConstraint("application_id", name=op.f("uq_attachment_retention_events_application_id")),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="RESTRICT", name=op.f("fk_attachment_retention_events_application_id_applications")),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT", name=op.f("fk_attachment_retention_events_actor_id_users")),
        sa.CheckConstraint("retention_days BETWEEN 1 AND 36500", name=op.f("ck_attachment_retention_events_days_range")),
        sa.CheckConstraint("char_length(policy_reference) BETWEEN 1 AND 200", name=op.f("ck_attachment_retention_events_policy_reference_length")),
        sa.CheckConstraint("byte_count BETWEEN 1 AND 5242880", name=op.f("ck_attachment_retention_events_byte_count_range")),
    )


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("LOCK TABLE applications, attachment_retention_events IN ACCESS EXCLUSIVE MODE"))
    retained = connection.scalar(sa.text(
        "SELECT EXISTS(SELECT 1 FROM applications WHERE attachment_deleted_at IS NOT NULL OR attachment IS NULL) "
        "OR EXISTS(SELECT 1 FROM attachment_retention_events)"
    ))
    if retained:
        raise RuntimeError("Cannot downgrade attachment retention after expiry: deleted bytes cannot be reconstructed and audit history must be preserved.")
    op.drop_table("attachment_retention_events")
    op.drop_constraint(op.f("ck_applications_attachment_state"), "applications", type_="check")
    op.alter_column("applications", "attachment", existing_type=sa.LargeBinary(), nullable=False)
    op.drop_column("applications", "attachment_deleted_at")
