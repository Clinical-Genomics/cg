"""add external sample table

Revision ID: 8a0dd32c2550
Revises: 5f3c86391226
Create Date: 2026-08-21 11:09:16.355663

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8a0dd32c2550"
down_revision = "5f3c86391226"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "external_sample",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sample_name", sa.String(128), nullable=False, unique=False),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customer.id"), nullable=False),
        sa.Column("customer_uploaded_at", sa.DateTime, nullable=False),
        sa.Column("transferred_at", sa.DateTime, server_default=None, nullable=True, index=True),
        sa.Index("ix_sample_name_customer_id", "sample_name", "customer_id"),
        sa.UniqueConstraint("sample_name", "customer_id", name="uq_sample_name_customer_id"),
    )


def downgrade():
    op.drop_table("external_sample")
