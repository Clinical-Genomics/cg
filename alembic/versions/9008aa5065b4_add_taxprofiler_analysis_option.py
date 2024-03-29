"""Add taxprofiler analysis option

Revision ID: 9008aa5065b4
Revises: df1b3dd317d0
Create Date: 2023-04-19 13:46:29.137152

"""

from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import declarative_base

from alembic import op

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


class Workflow(StrEnum):
    BALSAMIC: str = "balsamic"
    BALSAMIC_PON: str = "balsamic-pon"
    BALSAMIC_QC: str = "balsamic-qc"
    BALSAMIC_UMI: str = "balsamic-umi"
    DEMULTIPLEX: str = "demultiplex"
    FASTQ: str = "fastq"
    FLUFFY: str = "fluffy"
    MICROSALT: str = "microsalt"
    MIP_DNA: str = "mip-dna"
    MIP_RNA: str = "mip-rna"
    MUTANT: str = "mutant"
    RAREDISEASE: str = "raredisease"
    RNAFUSION: str = "rnafusion"
    RSYNC: str = "rsync"
    SPRING: str = "spring"
    TAXPROFILER: str = "taxprofiler"


class Analysis(Base):
    __tablename__ = "analysis"
    id = sa.Column(sa.types.Integer, primary_key=True)
    pipeline = sa.Column(sa.types.Enum(*list(Workflow)))


class Case(Base):
    __tablename__ = "family"
    id = sa.Column(sa.types.Integer, primary_key=True)
    data_analysis = sa.Column(sa.types.Enum(*list(Workflow)))


def upgrade():
    op.alter_column("family", "data_analysis", type_=new_enum)
    op.alter_column("analysis", "pipeline", type_=new_enum)


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for analysis in session.query(Analysis).filter(Analysis.pipeline == "taxprofiler"):
        analysis.pipeline = "fastq"
    for family in session.query(Case).filter(Case.data_analysis == "taxprofiler"):
        family.data_analysis = "fastq"
    session.commit()
