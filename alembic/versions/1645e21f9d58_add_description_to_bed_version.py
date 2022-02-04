"""add description to bed_version

Revision ID: 1645e21f9d58
Revises: c76d655c8edf
Create Date: 2022-02-04 10:25:52.878013

"""
from alembic import op
from sqlalchemy import (
    Column,
    String,
    types,
)

# revision identifiers, used by Alembic.
revision = "1645e21f9d58"
down_revision = "c76d655c8edf"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("bed_version", Column("description", String(256), nullable=True))
    op.add_column("bed", Column("description", String(256), nullable=True))
    op.add_column("bed", Column("details", types.Text, nullable=True))
    op.add_column("bed", Column("limitations", types.Text, nullable=True))


def downgrade():
    op.drop_column("bed_version", "description")
    op.drop_column("bed", "description")
    op.add_column("bed", "details")
    op.add_column("bed", "limitations")
