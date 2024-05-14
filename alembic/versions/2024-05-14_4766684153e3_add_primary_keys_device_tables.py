"""add_primary_keys_device_tables

Revision ID: 4766684153e3
Revises: 9b188aee9577
Create Date: 2024-05-14 10:20:13.505383

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "4766684153e3"
down_revision = "9b188aee9577"
branch_labels = None
depends_on = None


def upgrade():
    op.create_primary_key(constraint_name="pk_run_device", table_name="run_device", columns=["id"])
    op.create_primary_key(
        constraint_name="pk_run_metrics", table_name="run_metrics", columns=["id"]
    )
    op.create_primary_key(
        constraint_name="pk_sample_run_metrics", table_name="sample_run_metrics", columns=["id"]
    )


def downgrade():
    op.drop_constraint(
        constraint_name="pk_sample_run_metrics", table_name="sample_run_metrics", type_="primary"
    )
    op.drop_constraint(constraint_name="pk_run_metrics", table_name="run_metrics", type_="primary")
    op.drop_constraint(constraint_name="pk_run_device", table_name="run_device", type_="primary")
