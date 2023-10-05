"""Add customer lab contact

Revision ID: db61c62d9bc0
Revises: e853d21feaa0
Create Date: 2023-10-05 12:53:28.435684

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "db61c62d9bc0"
down_revision = "e853d21feaa0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="customer",
        column=sa.Column(
            "lab_contact_id",
            sa.INTEGER,
            sa.ForeignKey(name="customer_lab_contact_fk_1", column="user.id"),
        ),
    )


def downgrade():
    op.drop_constraint(constraint_name="customer_lab_contact_fk_1", table_name="customer")
    op.drop_column(table_name="customer", column_name="lab_contact_id")
