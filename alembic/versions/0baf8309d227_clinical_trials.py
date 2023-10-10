"""empty message

Revision ID: 0baf8309d227
Revises: bf97b0121538
Create Date: 2022-03-28 15:13:20.409452

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0baf8309d227"
down_revision = "bf97b0121538"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    op.add_column(
        "application_version", sa.Column("price_clinical_trials", sa.Integer(), nullable=True)
    )


def downgrade():
    op.drop_column(
        "application_version", sa.Column("price_clinical_trials", sa.Integer(), nullable=True)
    )
