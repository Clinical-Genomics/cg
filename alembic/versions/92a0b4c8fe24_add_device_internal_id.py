"""add_device_internal_id

Revision ID: 92a0b4c8fe24
Revises: 078884a6b2d2
Create Date: 2024-05-13 16:15:45.639070

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "92a0b4c8fe24"
down_revision = "078884a6b2d2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="run_device",
        column=sa.Column(__name_pos="internal_id", __type_pos=sa.String(length=64), nullable=False),
    )
    op.create_unique_constraint(
        constraint_name="uq_internal_id", table_name="run_device", columns=["internal_id"]
    )


def downgrade():
    op.drop_constraint(constraint_name="uq_internal_id", table_name="run_device", type_="unique")
    op.drop_column(table_name="run_device", column_name="internal_id")
