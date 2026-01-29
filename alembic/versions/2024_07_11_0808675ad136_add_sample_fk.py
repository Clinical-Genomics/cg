"""add_sample_fk

Revision ID: 0808675ad136
Revises: 2a2c618967af
Create Date: 2024-07-11 09:31:16.561316

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0808675ad136"
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
