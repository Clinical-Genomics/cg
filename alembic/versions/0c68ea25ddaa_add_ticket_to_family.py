"""Add ticket to family

Revision ID: 0c68ea25ddaa
Revises: c494649637d5
Create Date: 2021-12-21 11:24:44.554990

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import Column, types

revision = "0c68ea25ddaa"
down_revision = "c494649637d5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("family", Column("ticket_number", types.Integer, nullable=True))

    # todo: get from sample where creation data are the same


def downgrade():
    op.drop_column("family", "ticket_number")
