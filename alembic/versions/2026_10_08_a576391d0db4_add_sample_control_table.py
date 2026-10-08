"""add sample control table

Revision ID: a576391d0db4
Revises: dbcd93acdda1
Create Date: 2026-10-08 09:43:05.184374

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a576391d0db4"
down_revision = "dbcd93acdda1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sample_control",
        sa.Column("sample_id", sa.Integer(), nullable=False, index=True),
        sa.Column("control_sample_id", sa.Integer(), nullable=False, index=True),
    )


def downgrade():
    pass
