"""fix-sars-cov-2-data-analysis-to-database

Revision ID: 432379a1adfa
Revises: 6d74453565f2
Create Date: 2021-03-16 12:05:13.275423

"""
from cg.constants import Pipeline, DataDelivery
from sqlalchemy.dialects import mysql

from alembic import op
import sqlalchemy as sa

from sqlalchemy import orm, Column, types
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# revision identifiers, used by Alembic.
revision = "432379a1adfa"
down_revision = "6d74453565f2"
branch_labels = None
depends_on = None


class Family(Base):
    __tablename__ = "family"

    id = sa.Column(sa.types.Integer, primary_key=True)
    internal_id = sa.Column(sa.types.String(32), unique=True, nullable=False)
    name = sa.Column(sa.types.String(128), nullable=False)
    data_analysis = Column(types.Enum(*list(Pipeline)))
    data_delivery = Column(types.Enum(*list(DataDelivery)))

    def __str__(self) -> str:
        return (
            f"{self.internal_id} ({self.name}) {self.data_analysis or 'None'}"
            f" {self.data_delivery}"
        )


old_options = ("balsamic", "fastq", "fluffy", "microsalt", "mip-dna", "mip-rna")
new_options = sorted(old_options + ("sars-cov-2",))

old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    op.alter_column("family", "data_analysis", type_=new_enum)
    op.alter_column("analysis", "pipeline", type_=new_enum)

    for family in (
        session.query(Family)
        .filter(Family.data_delivery == str(DataDelivery.FASTQ))
        .filter(Family.data_analysis == "")
    ):
        print(f"Altering family: {str(family)}")
        family.data_analysis = str(Pipeline.SARS_COV_2)
        print(f"Altered family: {str(family)}")

    session.commit()


def downgrade():
    op.alter_column("family", "data_analysis", type_=old_enum)
    op.alter_column("analysis", "pipeline", type_=old_enum)
