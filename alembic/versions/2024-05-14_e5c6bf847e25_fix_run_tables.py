"""fix_run_tables

Revision ID: e5c6bf847e25
Revises: 4766684153e3
Create Date: 2024-05-14 15:34:50.944774

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e5c6bf847e25"
down_revision = "4766684153e3"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column(table_name="run_device", column_name="device_id")
    op.add_column(
        table_name="run_metrics",
        column=sa.Column(
            "device_id",
            sa.Integer(),
            sa.ForeignKey(column="run_device.id", name="fk_device_id"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_constraint(constraint_name="fk_device_id", table_name="run_metrics", type_="foreignkey")
    op.drop_column(table_name="run_metrics", column_name="device_id")
    op.add_column(
        table_name="run_device",
        column=sa.Column("device_id", sa.Integer(), nullable=False),
    )
