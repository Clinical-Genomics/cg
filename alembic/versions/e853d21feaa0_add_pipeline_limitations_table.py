"""Add pipeline limitations table

Revision ID: e853d21feaa0
Revises: 9def7a6eae73
Create Date: 2023-09-28 10:13:37.226849

"""
import sqlalchemy as sa
from alembic import op
from cg.constants.constants import Pipeline

# revision identifiers, used by Alembic.
revision = "e853d21feaa0"
down_revision = "9def7a6eae73"
branch_labels = None
depends_on = None

table_name = "application_limitations"


def upgrade():
    op.create_table(
        table_name,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "application_id",
            sa.Integer(),
            sa.ForeignKey("application.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pipeline", sa.Enum(*list(Pipeline)), nullable=False),
        sa.Column("limitations", sa.Text()),
        sa.Column("comment", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_onupdate=sa.func.now()),
    )


def downgrade():
    op.drop_table(table_name)
