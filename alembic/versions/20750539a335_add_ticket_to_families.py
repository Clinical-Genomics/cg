"""Adds ticket to Families

Revision ID: 20750539a335
Revises: ddc94088be4d
Create Date: 2022-07-22 08:43:36.271777

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20750539a335"
down_revision = "ddc94088be4d"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "sample",
        "ticket_number",
        new_column_name="original_ticket",
    )


def downgrade():
    pass
