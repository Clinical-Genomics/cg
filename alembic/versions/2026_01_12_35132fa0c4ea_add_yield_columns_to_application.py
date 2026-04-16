"""add yield columns to application

Revision ID: 35132fa0c4ea
Revises: a8c44f7715b2
Create Date: 2026-01-12 13:54:01.160451

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "35132fa0c4ea"
down_revision = "a8c44f7715b2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="application",
        column=sa.Column("target_hifi_yield", sa.BIGINT, nullable=True, default=None),
    )
    op.add_column(
        table_name="application",
        column=sa.Column("percent_hifi_yield_guaranteed", sa.Integer, nullable=True, default=None),
    )


def downgrade():
    op.drop_column("application", "target_hifi_yield")
    op.drop_column("application", "percent_hifi_yield_guaranteed")
