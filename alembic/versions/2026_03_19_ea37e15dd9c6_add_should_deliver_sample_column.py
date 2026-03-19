"""add should_deliver_sample column

Revision ID: ea37e15dd9c6
Revises: 2c9a49ce5512
Create Date: 2026-03-19 13:43:58.661703

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ea37e15dd9c6"
down_revision = "2c9a49ce5512"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="case_sample",
        column=sa.Column(
            name="should_deliver_sample", type="boolean", nullable=False, server_default="false"
        ),
    )
    op.alter_column(
        table_name="case_sample", column_name="should_deliver_sample", server_default=None
    )
    op.create_index("ix_analysis_trailblazer_id", "analysis", ["trailblazer_id"], unique=True)
    op.create_unique_constraint("uq_analysis_trailblazer_id", "analysis", ["trailblazer_id"])


def downgrade():
    op.drop_constraint("uq_analysis_trailblazer_id", "analysis", type_="unique")
    op.drop_index("ix_analysis_trailblazer_id", table_name="analysis")
    op.drop_column(table_name="case_sample", column_name="should_deliver_sample")
