"""Add label to customer table

Revision ID: fabd19666215
Revises: 96667267134e
Create Date: 2026-04-16 15:20:35.802743

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "fabd19666215"
down_revision = "96667267134e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="customer",
        column=sa.Column("label", sa.String(64), nullable=True, default=None),
    )


def downgrade():
    op.drop_column(table_name="customer", column_name="label")
