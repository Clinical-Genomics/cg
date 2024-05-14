"""fix_new_tech_tables

Revision ID: 078884a6b2d2
Revises: 9b188aee9577
Create Date: 2024-05-13 11:36:49.628610

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "078884a6b2d2"
down_revision = "9b188aee9577"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column(table_name="run_device", column_name="device_id")
    op.add_column(
        table_name="run_metrics",
        column=sa.Column(
            "device_id",
            sa.Integer(),
            sa.ForeignKey(column="run_device.id", name="fk_device_id", nullable=False),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_constraint(constraint_name="fk_device_id", table_name="run_metrics", type_="foreignkey")
    op.drop_column(table_name="run_metrics", column_name="device_id")
    op.add_column(
        table_name="run_device",
        column=sa.Column(__name_pos="device_id", __type_pos=sa.Integer(), nullable=False),
    )
