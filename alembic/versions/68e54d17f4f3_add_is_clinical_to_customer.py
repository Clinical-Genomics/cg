"""add is_clinical to customer

Revision ID: 68e54d17f4f3
Revises: 2fdb42ba801a
Create Date: 2023-07-07 09:57:29.371815

"""

import sqlalchemy as sa
from sqlalchemy import Column, types
from sqlalchemy.orm import DeclarativeBase

from alembic import op

# revision identifiers, used by Alembic.
revision = "68e54d17f4f3"
down_revision = "2fdb42ba801a"
branch_labels = None
depends_on = None


class Model(DeclarativeBase):
    pass


class Customer(Model):
    __tablename__ = "customer"
    id = Column(types.Integer, primary_key=True)
    is_clinical = Column(types.Boolean, nullable=True)


def upgrade():
    op.add_column(table_name="customer", column=sa.Column("is_clinical", sa.BOOLEAN))
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for customer in session.query(Customer):
        customer.is_clinical = False
    session.commit()
    op.alter_column(
        table_name="customer",
        column_name="is_clinical",
        existing_type=sa.BOOLEAN,
        nullable=False,
    )


def downgrade():
    op.drop_column(table_name="customer", column_name="is_clinical")
