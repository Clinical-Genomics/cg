"""add-eligible-for-skip-qc

Revision ID: 79454ff320bf
Revises: b105b426af99
Create Date: 2023-12-11 15:02:40.593762

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "79454ff320bf"
down_revision = "b105b426af99"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "application",
        sa.Column("is_eligible_for_skip_qc", sa.Boolean(), nullable=False),
    )


def downgrade():
    op.drop_column("application", "is_eligible_for_skip_qc")
