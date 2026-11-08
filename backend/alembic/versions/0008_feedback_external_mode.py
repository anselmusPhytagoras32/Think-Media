"""FR10/12: preserve satisfaction feedback in external assistant mode."""
from alembic import op
import sqlalchemy as sa

revision = '0008_feedback_external_mode'
down_revision = '0007_attachment_retention'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(op.f('ck_satisfaction_feedback_mode_allowed'), 'satisfaction_feedback', type_='check')
    op.create_check_constraint(op.f('ck_satisfaction_feedback_mode_allowed'), 'satisfaction_feedback', "mode IN ('disabled','retrieval','external')")


def downgrade():
    # Reclassifying or dropping genuine feedback would alter research evidence.
    op.get_bind().execute(sa.text('LOCK TABLE satisfaction_feedback IN ACCESS EXCLUSIVE MODE'))
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM satisfaction_feedback WHERE mode='external')")):
        raise RuntimeError('Cannot downgrade while external-mode satisfaction feedback exists; preserve those records.')
    op.drop_constraint(op.f('ck_satisfaction_feedback_mode_allowed'), 'satisfaction_feedback', type_='check')
    op.create_check_constraint(op.f('ck_satisfaction_feedback_mode_allowed'), 'satisfaction_feedback', "mode IN ('disabled','retrieval')")
