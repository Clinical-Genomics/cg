"""Renames customer_group to collaboration and adds a link table between it and customer

Revision ID: ddc94088be4d
Revises: 33cd4b45acb4
Create Date: 2022-06-29 15:11:08.142445

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from sqlalchemy.dialects import mysql
from sqlalchemy import Column, types, orm
from sqlalchemy.ext.declarative import declarative_base

revision = "ddc94088be4d"
down_revision = "33cd4b45acb4"
branch_labels = None
depends_on = None

Base = declarative_base()

customer_collaboration = sa.Table(
    "customer_collaboration",
    Base.metadata,
    Column("customer_id", types.Integer, sa.ForeignKey("customer.id"), nullable=False),
    Column("collaboration_id", types.Integer, sa.ForeignKey("collaboration.id"), nullable=False),
    sa.UniqueConstraint("customer_id", "collaboration_id", name="_customer_collaboration_uc"),
)


class Customer(Base):
    __tablename__ = "customer"
    id = Column(types.Integer, primary_key=True)
    customer_group_id = Column(sa.ForeignKey("collaboration.id"), nullable=False)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(32), unique=False, nullable=False)
    collaborations = orm.relationship("Collaboration", secondary=customer_collaboration)


class Collaboration(Base):
    __tablename__ = "collaboration"
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)
    customers = orm.relationship(Customer)


def upgrade():
    op.alter_column("customer", "customer_group_id", nullable=True, existing_type=mysql.INTEGER)
    op.drop_constraint("customer_group_ibfk_1", table_name="customer", type_="foreignkey")
    op.rename_table(old_table_name="customer_group", new_table_name="collaboration")
    op.create_table(
        "customer_collaboration",
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("collaboration_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ("customer_id",),
            ["customer.id"],
        ),
        sa.ForeignKeyConstraint(
            ("collaboration_id",),
            ["collaboration.id"],
        ),
        sa.UniqueConstraint("customer_id", "collaboration_id", name="_customer_collaboration_uc"),
    )
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for collaboration in session.query(Collaboration):
        if len(collaboration.customers) > 1:
            for customer in collaboration.customers:
                customer.collaborations.append(collaboration)
        else:
            session.delete(collaboration)
    session.commit()
    op.drop_column(
        table_name="customer",
        column_name="customer_group_id",
    )


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    op.add_column(
        "customer",
        sa.Column(
            name="customer_group_id",
            type_=mysql.INTEGER(display_width=11),
            nullable=False,
        ),
    )
    for customer in session.query(Customer):
        if not customer.collaborations:
            customer_group = Collaboration(internal_id=customer.internal_id, name=customer.name)
            session.add(customer_group)
            session.commit()
            session.refresh(customer_group)
            customer.customer_group_id = customer_group.id
        else:
            customer.customer_group_id = customer.collaborations[0].id
    session.commit()
    op.rename_table(new_table_name="customer_group", old_table_name="collaboration")
    op.create_foreign_key(
        "customer_group_ibfk_1",
        source_table="customer",
        referent_table="customer_group",
        local_cols=["customer_group_id"],
        remote_cols=["id"],
    )
    op.drop_table("customer_collaboration")
    session.commit()
