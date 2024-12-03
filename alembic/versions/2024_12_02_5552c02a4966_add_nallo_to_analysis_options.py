"""add-nallo-to-analysis-options

Revision ID: 5552c02a4966
Revises: 05ffb5e13d7b
Create Date: 2024-12-02 11:35:31.725343

"""

from enum import StrEnum

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# revision identifiers, used by Alembic.
revision = "5552c02a4966"
down_revision = "05ffb5e13d7b"
branch_labels = None
depends_on = None

base_options = (
    "balsamic",
    "balsamic-pon",
    "balsamic-qc",
    "balsamic-umi",
    "demultiplex",
    "raw-data",
    "fluffy",
    "microsalt",
    "mip-dna",
    "mip-rna",
    "mutant",
    "raredisease",
    "rnafusion",
    "rsync",
    "spring",
    "taxprofiler",
    "tomte",
    "jasen",
)

old_options = sorted(base_options)
new_options = sorted(base_options + ("nallo",))

old_analysis_enum = mysql.ENUM(*old_options)
new_analysis_enum = mysql.ENUM(*new_options)


class Pipeline(StrEnum):
    BALSAMIC: str = "balsamic"
    BALSAMIC_PON: str = "balsamic-pon"
    BALSAMIC_QC: str = "balsamic-qc"
    BALSAMIC_UMI: str = "balsamic-umi"
    DEMULTIPLEX: str = "demultiplex"
    FLUFFY: str = "fluffy"
    JASEN: str = "jasen"
    MICROSALT: str = "microsalt"
    MIP_DNA: str = "mip-dna"
    MIP_RNA: str = "mip-rna"
    MUTANT: str = "mutant"
    NALLO: str = "nallo"
    RAREDISEASE: str = "raredisease"
    RAW_DATA: str = "raw-data"
    RNAFUSION: str = "rnafusion"
    RSYNC: str = "rsync"
    SPRING: str = "spring"
    TAXPROFILER: str = "taxprofiler"
    TOMTE: str = "tomte"


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analysis"
    id = sa.Column(sa.types.Integer, primary_key=True)
    workflow = sa.Column(sa.types.Enum(*list(Pipeline)))


class Case(Base):
    __tablename__ = "case"
    id = sa.Column(sa.types.Integer, primary_key=True)
    data_analysis = sa.Column(sa.types.Enum(*list(Pipeline)))
    internal_id = sa.Column(sa.types.String)


def upgrade():
    op.alter_column("case", "data_analysis", type_=new_analysis_enum)
    op.alter_column("analysis", "workflow", type_=new_analysis_enum)


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for analysis in session.query(Analysis).filter(Analysis.workflow == "nallo"):
        print(f"Changing pipeline for Case {Case.internal_id} to raw-data")
        analysis.workflow = "raw-data"
    for case in session.query(Case).filter(Case.data_analysis == "nallo"):
        print(f"Changing data_analysis for Case {case.internal_id} to raw-data")
        case.data_analysis = "raw-data"
    op.alter_column("case", "data_analysis", type_=old_analysis_enum)
    op.alter_column("analysis", "workflow", type_=old_analysis_enum)
    session.commit()
