"""Add case sample cascading

Revision ID: 6f368f57df4a
Revises: 5552c02a4966
Create Date: 2025-02-07 11:25:01.936922

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "6f368f57df4a"
down_revision = "5552c02a4966"
branch_labels = None
depends_on = None

case_constraint_name: str = "case_sample_ibfk_1"


def upgrade():
    op.drop_constraint(
        constraint_name=case_constraint_name, table_name="case_sample", type_="foreignkey"
    )
    op.create_foreign_key(
        constraint_name=case_constraint_name,
        source_table="case_sample",
        referent_table="case",
        local_cols=["case_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        constraint_name=case_constraint_name, table_name="case_sample", type_="foreignkey"
    )
    op.create_foreign_key(
        constraint_name=case_constraint_name,
        source_table="case_sample",
        referent_table="case",
        local_cols=["case_id"],
        remote_cols=["id"],
        ondelete="RESTRICT",
    )
