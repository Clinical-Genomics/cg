"""rename_pipeline_sars-cov2

Revision ID: de0f5b78dca4
Revises: a6befebf1231
Create Date: 2024-01-25 09:24:36.338102

"""

from enum import StrEnum

from sqlalchemy import orm, types
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from alembic import op


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


# revision identifiers, used by Alembic.
revision = "de0f5b78dca4"
down_revision = "a6befebf1231"
branch_labels = None
depends_on = None

old_options = (
    "taxprofiler",
    "microsalt",
    "rnafusion",
    "balsamic-umi",
    "raredisease",
    "sars-cov-2",
    "balsamic-qc",
    "balsamic",
    "balsamic-pon",
    "demultiplex",
    "fluffy",
    "mip-dna",
    "mip-rna",
    "rsync",
    "spring",
    "fastq",
)
new_options = sorted(old_options + ("mutant",))
new_options.remove("sars-cov-2")

old_enum = mysql.ENUM(*list(old_options))
new_enum = mysql.ENUM(*list(new_options))


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    pipeline: Mapped[str]


class Case(Base):
    __tablename__ = "case"
    data_analysis: Mapped[str]
    id: Mapped[int] = mapped_column(primary_key=True)


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    op.alter_column("case", "data_analysis", type_=mysql.VARCHAR(64), existing_nullable=True)
    op.alter_column("analysis", "pipeline", type_=mysql.VARCHAR(64), existing_nullable=True)

    for case in session.query(Case).filter(Case.data_analysis == ""):
        print(f"Altering case: {str(case)}")
        case.data_analysis = "fastq"
        case.action = "hold"
        print(f"Altered case: {str(case)}")

    for case in session.query(Case).filter(Case.data_analysis == "sars-cov-2"):
        print(f"Altering case: {str(case)}")
        case.data_analysis = str(Workflow.MUTANT)
        print(f"Altered case: {str(case)}")

    for analysis in session.query(Analysis).filter(Analysis.pipeline == "sars-cov-2"):
        print(f"Altering analysis: {str(analysis)}")
        analysis.pipeline = str(Workflow.MUTANT)
        print(f"Altered analysis: {str(analysis)}")

    session.commit()
    op.alter_column("case", "data_analysis", type_=new_enum, existing_nullable=True)
    op.alter_column("analysis", "pipeline", type_=new_enum, existing_nullable=True)


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    op.alter_column("case", "data_analysis", type_=mysql.VARCHAR(64), existing_nullable=True)
    op.alter_column("analysis", "pipeline", type_=mysql.VARCHAR(64), existing_nullable=True)

    for case in session.query(Case).filter(Case.data_analysis == "mutant"):
        print(f"Altering case: {str(case)}")
        case.data_analysis = "sars-cov-2"
        print(f"Altered case: {str(case)}")

    for analysis in session.query(Analysis).filter(Analysis.pipeline == "mutant"):
        print(f"Altering analysis: {str(analysis)}")
        analysis.pipeline = "sars-cov-2"
        print(f"Altered analysis: {str(analysis)}")

    session.commit()
    op.alter_column("case", "data_analysis", type_=old_enum, existing_nullable=True)
    op.alter_column("analysis", "pipeline", type_=old_enum, existing_nullable=True)
