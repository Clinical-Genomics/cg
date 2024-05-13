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
    op.drop_column("run_device", "device_id")
    op.add_column("run_metrics", sa.Column("device_id", sa.Integer(), sa.ForeignKey("run_device.id", name="fk_device_id",  nullable=False))


def downgrade():
    op.drop_constraint("fk_device_id", "run_metrics", type_="foreignkey")
    op.drop_column("run_metrics", "device_id")
    op.add_column("run_device", sa.Column("device_id", sa.Integer(), nullable=False))
