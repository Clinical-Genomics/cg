"""remove balsamic qc

Revision ID: a9568bb3a8b7
Revises: 5552c02a4966
Create Date: 2025-02-10 16:08:22.255991

"""

from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import DeclarativeBase

from alembic import op

# revision identifiers, used by Alembic.
revision = "a9568bb3a8b7"
down_revision = "5552c02a4966"
branch_labels = None
depends_on = None


base_options: tuple = (
    "balsamic",
    "balsamic-pon",
    "balsamic-umi",
    "demultiplex",
    "fluffy",
    "jasen",
    "microsalt",
    "mip-dna",
    "mip-rna",
    "mutant",
    "nallo",
    "raredisease",
    "raw-data",
    "rnafusion",
    "rsync",
    "spring",
    "taxprofiler",
    "tomte",
)

old_options = sorted(base_options + ("balsamic-qc",))
new_options = sorted(base_options)

old_analysis_enum = mysql.ENUM(*old_options)
new_analysis_enum = mysql.ENUM(*new_options)


class Workflow(StrEnum):
    BALSAMIC: str = "balsamic"
    RAREDISEASE: str = "raredisease"
    BALSAMIC_PON: str = "balsamic-pon"
    BALSAMIC_UMI: str = "balsamic-umi"
    DEMULTIPLEX: str = "demultiplex"
    FLUFFY: str = "fluffy"
    JASEN: str = "jasen"
    MIP_DNA: str = "mip-dna"
    MIP_RNA: str = "mip-rna"
    MUTANT: str = "mutant"
    NALLO: str = "nallo"
    RAW_DATA: str = "raw-data"
    RNAFUSION: str = "rnafusion"
    RSYNC: str = "rsync"
    SPRING: str = "spring"
    TAXPROFILER: str = "taxprofiler"
    TOMTE: str = "tomte"
    MICROSALT: str = "microsalt"


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analysis"
    id = sa.Column(sa.types.Integer, primary_key=True)
    workflow = sa.Column(sa.types.Enum(*list(Workflow)))


class Case(Base):
    __tablename__ = "case"
    id = sa.Column(sa.types.Integer, primary_key=True)
    data_analysis = sa.Column(sa.types.Enum(*list(Workflow)))


def upgrade():
    op.alter_column("case", "data_analysis", type_=new_analysis_enum)
    op.alter_column("analysis", "workflow", type_=new_analysis_enum)


def downgrade():
    op.alter_column("case", "data_analysis", type_=old_analysis_enum)
    op.alter_column("analysis", "workflow", type_=old_analysis_enum)
