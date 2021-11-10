"""Add control to sample

Revision ID: c081458ff180
Revises: 1c27462b49f6
Create Date: 2021-09-10 13:33:51.083517

"""
from alembic import op
from sqlalchemy import (
    types,
    Column,
    ForeignKey,
    orm,
    String,
)
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "c081458ff180"
down_revision = "1c27462b49f6"
branch_labels = None
depends_on = None

control_options = ("", "negative", "positive")
control_enum = mysql.ENUM(*control_options)


def upgrade():
    op.add_column("sample", Column("control", control_enum, nullable=True))


def downgrade():
    op.drop_column("sample", "control")
