"""add data archive location

Revision ID: c3fdf3a8a5b3
Revises: ffb9f8ab8e62
Create Date: 2023-07-04 15:29:48.507215

"""

import sqlalchemy as sa
from sqlalchemy import Column, types
from sqlalchemy.orm import DeclarativeBase

from alembic import op

# revision identifiers, used by Alembic.
revision = "c3fdf3a8a5b3"
down_revision = "ffb9f8ab8e62"
branch_labels = None
depends_on = None


class Model(DeclarativeBase):
    pass


class Customer(Model):
    __tablename__ = "customer"
    id = Column(types.Integer, primary_key=True)
    data_archive_location = Column(types.String(32), nullable=False, default="PDC")


def upgrade():
    op.add_column(table_name="customer", column=sa.Column("data_archive_location", sa.String(32)))
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for customer in session.query(Customer):
        customer.data_archive_location = "PDC"
    session.commit()
    op.alter_column(
        table_name="customer",
        column_name="data_archive_location",
        existing_type=sa.String(length=32),
        nullable=False,
    )


def downgrade():
    op.drop_column(table_name="customer", column_name="data_archive_location")
