"""add_device_internal_id

Revision ID: fa7a3d066872
Revises: e5c6bf847e25
Create Date: 2024-05-14 16:02:06.382170

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "fa7a3d066872"
down_revision = "e5c6bf847e25"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="run_device",
        column=sa.Column("internal_id", sa.String(length=64), nullable=False),
    )
    op.create_unique_constraint(
        constraint_name="uq_internal_id", table_name="run_device", columns=["internal_id"]
    )


def downgrade():
    op.drop_constraint(constraint_name="uq_internal_id", table_name="run_device", type_="unique")
    op.drop_column(table_name="run_device", column_name="internal_id")
