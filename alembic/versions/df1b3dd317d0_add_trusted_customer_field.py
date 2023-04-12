"""Adds a new boolean column to the customer table containing whether the customer can be trusted
with advanced options.

Revision ID: df1b3dd317d0
Revises: 554140bc13e4
Create Date: 2023-04-12 11:13:37.585551

"""

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import mysql
from sqlalchemy import Column, types, orm
from sqlalchemy.ext.declarative import declarative_base


# revision identifiers, used by Alembic.
revision = "df1b3dd317d0"
down_revision = "554140bc13e4"
branch_labels = None
depends_on = None

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customer"
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(32), unique=False, nullable=False)


def upgrade():
    op.add_column(table_name="customer", column=Column())


def downgrade():
    pass
