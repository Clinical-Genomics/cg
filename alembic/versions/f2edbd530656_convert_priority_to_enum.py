"""Convert priority to enum

Revision ID: f2edbd530656
Revises: c494649637d5
Create Date: 2021-12-16 12:39:57.439135

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm, Column, types

# revision identifiers, used by Alembic.
revision = "f2edbd530656"
down_revision = "c494649637d5"
branch_labels = None
depends_on = None

PRIORITY_MAP = {"research": 0, "standard": 1, "priority": 2, "express": 3, "clinical_trials": 4}
REV_PRIORITY_MAP = {value: key for key, value in PRIORITY_MAP.items()}

priority_options = ("research", "standard", "priority", "express", "clinical_trials")
priority_enum = mysql.ENUM(*priority_options)

Base = declarative_base()


def priority_int_to_text(priority_int: int) -> str:
    """Humanized priority for sample."""
    return REV_PRIORITY_MAP[priority_int]


def priority_text_to_int(priority_text: str) -> int:
    return PRIORITY_MAP[priority_text]


def upgrade():
    class IntSample(Base):
        __tablename__ = "sample"

        id = sa.Column(sa.types.Integer, primary_key=True)
        priority = sa.Column(sa.types.Integer)
        priority_enum = sa.Column(priority_enum)

    class IntFamily(Base):
        __tablename__ = "family"

        id = sa.Column(sa.types.Integer, primary_key=True)
        priority = sa.Column(sa.types.Integer)
        priority_enum = sa.Column(priority_enum)

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    switch_priority_int_to_enum(session, "sample", IntSample)
    switch_priority_int_to_enum(session, "family", IntFamily)


def switch_priority_int_to_enum(session, table_name, model):
    print(f"Add column priority_enum to {table_name}")
    op.add_column(table_name, Column("priority_enum", priority_enum))
    print(f"Column priority_enum added to {table_name}")

    print("Copy priority text to new enum column")
    for record in session.query(model):
        print(record.priority, end="->", flush=True)
        record.priority_enum = priority_int_to_text(record.priority)
        print(record.priority_enum, end=" ", flush=True)

    print(f"All {table_name} records processed, committing to database")

    session.commit()

    print("Data committed, Renaming columns")

    with op.batch_alter_table(table_name) as bop:
        bop.alter_column("priority", new_column_name="priority_int", existing_type=sa.Integer)

    with op.batch_alter_table(table_name) as bop:
        bop.alter_column("priority_enum", new_column_name="priority", existing_type=priority_enum)

    print(f"Remove column priority_int from {table_name}")
    op.drop_column(table_name, "priority_int")
    print(f"Column priority_int removed from {table_name}")


def downgrade():
    class EnumSample(Base):
        __tablename__ = "sample"

        id = sa.Column(sa.types.Integer, primary_key=True)
        priority = sa.Column(priority_enum)
        priority_int = sa.Column(sa.types.Integer)

    class EnumFamily(Base):
        __tablename__ = "family"

        id = sa.Column(sa.types.Integer, primary_key=True)
        priority = sa.Column(priority_enum)
        priority_int = sa.Column(sa.types.Integer)

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    switch_priority_enum_to_int(session, "sample", EnumSample)
    switch_priority_enum_to_int(session, "family", EnumFamily)


def switch_priority_enum_to_int(session, table_name, model):
    print(f"Add column priority_int to {table_name}")
    op.add_column(table_name, Column("priority_int", types.Integer))
    print(f"Column priority_int added to {table_name}")

    for record in session.query(model):
        print(record.priority, end="->", flush=True)
        record.priority_int = priority_text_to_int(record.priority)
        print(record.priority_int, end=" ", flush=True)

    print(f"All {table_name} records processed, committing to database")

    session.commit()

    print("Data committed, Renaming columns")

    with op.batch_alter_table(table_name) as bop:
        bop.alter_column("priority", new_column_name="priority_enum", existing_type=priority_enum)

    with op.batch_alter_table(table_name) as bop:
        bop.alter_column("priority_int", new_column_name="priority", existing_type=sa.Integer)

    print(f"Remove column priority_enum from {table_name}")
    op.drop_column(table_name, "priority_enum")
    print(f"Column priority_enum removed from {table_name}")
