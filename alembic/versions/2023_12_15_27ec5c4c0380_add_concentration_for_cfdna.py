"""Add concentration for cfdna

Revision ID: 27ec5c4c0380
Revises: b105b426af99
Create Date: 2023-12-15 16:47:19.031328

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "27ec5c4c0380"
down_revision = "b105b426af99"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="application",
        column=sa.Column(
            "sample_concentration_minimum_cfdna",
            sa.DECIMAL(6, 2),
        ),
    )
    op.add_column(
        table_name="application",
        column=sa.Column(
            "sample_concentration_maximum_cfdna",
            sa.DECIMAL(6, 2),
        ),
    )


def downgrade():
    op.drop_column(table_name="application", column_name="sample_concentration_maximum_cfdna")
    op.drop_column(table_name="application", column_name="sample_concentration_minimum_cfdna")
