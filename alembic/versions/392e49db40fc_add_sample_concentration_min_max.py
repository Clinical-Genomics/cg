"""Add sample concentration min max

Revision ID: 392e49db40fc
Revises: db61c62d9bc0
Create Date: 2023-10-25 09:50:16.779186

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "392e49db40fc"
down_revision = "db61c62d9bc0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="application",
        column=sa.Column(
            "sample_concentration_minimum",
            sa.DECIMAL,
        ),
    )
    op.add_column(
        table_name="application",
        column=sa.Column(
            "sample_concentration_maximum",
            sa.DECIMAL,
        ),
    )


def downgrade():
    op.drop_column(table_name="application", column_name="sample_concentration_maximum")
    op.drop_column(table_name="application", column_name="sample_concentration_minimum")
