"""Add control to sample

Revision ID: c081458ff180
Revises: 7e344b9438bf
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
down_revision = "7e344b9438bf"
branch_labels = None
depends_on = None

control_options = ("no", "negative", "positive")
control_enum = mysql.ENUM(*control_options)


def upgrade():
    op.add_column("sample", Column("control", control_enum, nullable=True))


def downgrade():
    op.drop_column("sample", "control")
