"""remove_delivery_table

Revision ID: 9cf71c905539
Revises: b614a52759c5
Create Date: 2024-03-27 11:51:51.148871

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9cf71c905539'
down_revision = 'b614a52759c5'
branch_labels = None
depends_on = None


def upgrade():

    op.drop_table(table_name="delivery")
    op.drop_column(table_name="pool", column_name="deliveries")
    op.drop_column(table_name="sample", column_name="deliveries")

def downgrade():

    op.add_column("pool", sa.Column("deliveries", sa.TEXT))
    op.add_column("sample", sa.Column("deliveries", sa.TEXT))

    op.create_table(
        "delivery",
        sa.Column("id", sa.Integer, nullable=False, primary_key=True),
        sa.Column("delivered_at", sa.DateTime, nullable=True),
        sa.Column("removed_at", sa.DateTime, nullable=True),
        sa.Column("destination", sa.Enum(*("caesar", "pdc", "uppmax", "mh", "custom")), default="caesar"),
        sa.ForeignKeyConstraint(["sample_id"], ["sample.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pool_id"], ["pool.id"], ondelete="CASCADE"),
        sa.Column("comment", sa.types.TEXT, nullable=True),
    )

