"""Add analysis cascading


Revision ID: 76214cad1cb7
Revises: 2d63ba0d1154
Create Date: 2025-10-30 16:19:08.025635

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "76214cad1cb7"
down_revision = "2d63ba0d1154"
branch_labels = None
depends_on = None

analysis_contraint_name = "analysis_ibfk_1"


def upgrade():
    op.drop_constraint(
        constraint_name=analysis_contraint_name, table_name="analysis", type_="foreignkey"
    )
    op.create_foreign_key(
        constraint_name=analysis_contraint_name,
        source_table="analysis",
        referent_table="case",
        local_cols=["case_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        constraint_name=analysis_contraint_name, table_name="analysis", type_="foreignkey"
    )
    op.create_foreign_key(
        constraint_name=analysis_contraint_name,
        source_table="analysis",
        referent_table="case",
        local_cols=["case_id"],
        remote_cols=["id"],
        ondelete="RESTRICT",
    )
