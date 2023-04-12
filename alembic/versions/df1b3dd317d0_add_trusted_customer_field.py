"""Adds a new boolean column to the customer table containing whether the customer can be trusted
with advanced options.

Revision ID: df1b3dd317d0
Revises: 554140bc13e4
Create Date: 2023-04-12 11:13:37.585551

"""

from alembic import op
import sqlalchemy as sa

from sqlalchemy import Column, types, orm
from sqlalchemy.engine import Connection
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

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
    is_trusted = Column(type_=types.Boolean)


TRUSTED_CUSTOMERS = ["cust144"]


def upgrade():
    op.add_column(table_name="customer", column=Column(name="is_trusted", type_=types.Boolean))
    bind: Connection = op.get_bind()
    session: Session = sa.orm.Session(bind=bind)
    for customer in session.query(Customer):
        if customer.internal_id in TRUSTED_CUSTOMERS:
            customer.is_trusted = True
            continue
        customer.is_trusted = False
    session.commit()
    op.alter_column(
        table_name="customer", column_name="is_trusted", nullable=False, existing_type=types.Boolean
    )


def downgrade():
    op.drop_column(table_name="customer", column_name="is_trusted")
