"""remove sample.time_point

Revision ID: 367813f2e597
Revises: 0baf8309d227
Create Date: 2022-04-06 10:45:32.903682

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '367813f2e597'
down_revision = '0baf8309d227'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("sample", "time_point")


def downgrade():
    op.add_column("sample", sa.Column("time_point", sa.Integer))
