"""2024_05_22_add_yield_columns

Revision ID: 18e3b2aba252
Revises: 5fd7e8758fb1
Create Date: 2024-05-22 14:01:15.197675

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "18e3b2aba252"
down_revision = "5fd7e8758fb1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="illumina_sample_run_metrics",
        column=sa.Column("yield", sa.Integer(), nullable=True),
    )
    op.add_column(
        table_name="illumina_sample_run_metrics",
        column=sa.Column("yield_q30", sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column(table_name="illumina_sample_run_metrics", column_name="yield")
    op.drop_column(table_name="illumina_sample_run_metrics", column_name="yield_q30")
