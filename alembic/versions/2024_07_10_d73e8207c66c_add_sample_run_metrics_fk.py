"""add_sample_run_metrics_fk

Revision ID: d73e8207c66c
Revises: 2a2c618967af
Create Date: 2024-07-10 15:12:40.785679

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d73e8207c66c"
down_revision = "2a2c618967af"
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        constraint_name="fk_sample_id",
        source_table="sample_run_metrics",
        referent_table="sample",
        local_cols=["sample_id"],
        remote_cols=["id"],
    )


def downgrade():
    op.drop_constraint(
        constraint_name="fk_sample_id", table_name="sample_run_metrics", type_="foreignkey"
    )
