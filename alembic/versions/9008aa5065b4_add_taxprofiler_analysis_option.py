"""Add taxprofiler analysis option

Revision ID: 9008aa5065b4
Revises: df1b3dd317d0
Create Date: 2023-04-19 13:46:29.137152

"""
from alembic import op
from sqlalchemy.dialects import mysql
from sqlalchemy.ext.declarative import declarative_base

import sqlalchemy as sa
from cg.constants import Pipeline


# revision identifiers, used by Alembic.
revision = "9008aa5065b4"
down_revision = "df1b3dd317d0"
branch_labels = None
depends_on = None

Base = declarative_base()

old_options = (
    "balsamic",
    "balsamic-pon",
    "balsamic-qc",
    "balsamic-umi",
    "demultiplex",
    "fastq",
    "fluffy",
    "microsalt",
    "mip-dna",
    "mip-rna",
    "rnafusion",
    "rsync",
    "sars-cov-2",
    "spring",
)
new_options = sorted(old_options + ("taxprofiler",))

old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


class Analysis(Base):
    __tablename__ = "analysis"
    id = sa.Column(sa.types.Integer, primary_key=True)
    pipeline = sa.Column(sa.types.Enum(*list(Pipeline)))


class Family(Base):
    __tablename__ = "family"
    id = sa.Column(sa.types.Integer, primary_key=True)
    data_analysis = sa.Column(sa.types.Enum(*list(Pipeline)))


def upgrade():
    op.alter_column("family", "data_analysis", type_=new_enum)
    op.alter_column("analysis", "pipeline", type_=new_enum)


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for analysis in session.query(Analysis).filter(Analysis.pipeline == "taxprofiler"):
        analysis.pipeline = "fastq"
    for family in session.query(Family).filter(Family.data_analysis == "taxprofiler"):
        family.data_analysis = "fastq"
    session.commit()
