"""remove_delivery_table

Revision ID: 9cf71c905539
Revises: b614a52759c5
Create Date: 2024-03-27 11:51:51.148871

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9cf71c905539"
down_revision = "0fda0f2746d6"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table(table_name="delivery")


def downgrade():
    op.create_table(
        "delivery",
        sa.Column("id", sa.Integer, nullable=False, primary_key=True),
        sa.Column("delivered_at", sa.DateTime, nullable=True),
        sa.Column("removed_at", sa.DateTime, nullable=True),
        sa.Column(
            "destination", sa.Enum(*("caesar", "pdc", "uppmax", "mh", "custom")), default="caesar"
        ),
        sa.Column("sample_id", sa.Integer, nullable=True),
        sa.Column("pool_id", sa.Integer, nullable=True),
        sa.ForeignKeyConstraint(["sample_id"], ["sample.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pool_id"], ["pool.id"], ondelete="CASCADE"),
        sa.Column("comment", sa.types.TEXT, nullable=True),
    )
