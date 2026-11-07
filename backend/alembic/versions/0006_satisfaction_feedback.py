"""FR12 explicit optional CSAT, additive and private (NFR02–03,08)."""
from alembic import op
import sqlalchemy as sa
revision='0006_satisfaction_feedback'
down_revision='a7eed17d111a'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('satisfaction_feedback',sa.Column('user_id',sa.Uuid(),nullable=False),sa.Column('rating',sa.Integer(),nullable=False),sa.Column('mode',sa.String(20),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('rating BETWEEN 1 AND 5',name=op.f('ck_satisfaction_feedback_rating_range')),sa.CheckConstraint("mode IN ('disabled','retrieval')",name=op.f('ck_satisfaction_feedback_mode_allowed')),sa.ForeignKeyConstraint(['user_id'],['users.id'],name=op.f('fk_satisfaction_feedback_user_id_users'),ondelete='CASCADE'),sa.PrimaryKeyConstraint('user_id',name=op.f('pk_satisfaction_feedback')))
def downgrade():
    op.drop_table('satisfaction_feedback')
