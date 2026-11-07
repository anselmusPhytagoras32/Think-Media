"""Complete FR02 student background/location and optional company contacts.

Existing profiles retain empty student fields and nullable contacts.
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_profile_details"
down_revision = "0001_phase1_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("student_profiles", sa.Column("location", sa.String(200), nullable=False, server_default=sa.text("''")))
    op.add_column("student_profiles", sa.Column("background", sa.String(2000), nullable=False, server_default=sa.text("''")))
    op.create_check_constraint("location_length", "student_profiles", "char_length(location) <= 200")
    op.create_check_constraint("background_length", "student_profiles", "char_length(background) <= 2000")
    op.add_column("company_profiles", sa.Column("contact_email", sa.String(254), nullable=True))
    op.add_column("company_profiles", sa.Column("contact_phone", sa.String(40), nullable=True))


def downgrade():
    op.drop_column("company_profiles", "contact_phone")
    op.drop_column("company_profiles", "contact_email")
    op.drop_constraint(op.f("ck_student_profiles_background_length"), "student_profiles", type_="check")
    op.drop_constraint(op.f("ck_student_profiles_location_length"), "student_profiles", type_="check")
    op.drop_column("student_profiles", "background")
    op.drop_column("student_profiles", "location")
