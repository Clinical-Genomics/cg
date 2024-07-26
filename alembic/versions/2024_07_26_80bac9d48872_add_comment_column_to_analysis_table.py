"""Add comment column to analysis table

Revision ID: 80bac9d48872
Revises: 0808675ad136
Create Date: 2024-07-26 10:05:13.623664

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "80bac9d48872"
down_revision = "0808675ad136"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="analysis",
        column=sa.Column("comment", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_column(table_name="analysis", column_name="comment")
