"""rename_fastq_to_raw_data

Revision ID: 18dbadd8c436
Revises: bb4c6dbad991
Create Date: 2024-09-04 13:15:11.876822

"""

from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy import orm, types
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from alembic import op

# revision identifiers, used by Alembic.
revision = "18dbadd8c436"
down_revision = "bb4c6dbad991"
branch_labels = None
depends_on = None


old_options = (
    "balsamic",
    "balsamic-pon",
    "balsamic-qc",
    "balsamic-umi",
    "demultiplex",
    "fluffy",
    "jasen",
    "microsalt",
    "mip-dna",
    "mip-rna",
    "mutant",
    "raredisease",
    "raw-data",
    "rnafusion",
    "rsync",
    "spring",
    "taxprofiler",
    "tomte",
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
    FLUFFY: str = "fluffy"
    JASEN: str = "jasen"
    MICROSALT: str = "microsalt"
    MIP_DNA: str = "mip-dna"
    MIP_RNA: str = "mip-rna"
    MUTANT: str = "mutant"
    RAREDISEASE: str = "raredisease"
    RAW_DATA: str = "raw-data"
    RNAFUSION: str = "rnafusion"
    RSYNC: str = "rsync"
    SPRING: str = "spring"
    TAXPROFILER: str = "taxprofiler"
    TOMTE: str = "tomte"


class Base(DeclarativeBase):
    pass


class Case(Base):
    __tablename__ = "case"
    id: Mapped[int] = mapped_column(primary_key=True)
    data_analysis: Mapped[str | None] = mapped_column(
        types.Enum(*(workflow.value for workflow in Workflow))
    )


class Analysis(Base):
    __tablename__ = "analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow: Mapped[str | None] = mapped_column(
        types.Enum(*(workflow.value for workflow in Workflow))
    )


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    try:
        session.query(Case).filter(Case.data_analysis == "fastq").update(
            {"data_analysis": Workflow.RAW_DATA}, synchronize_session="evaluate"
        )
        session.query(Analysis).filter(Analysis.workflow == "fastq").update(
            {"workflow": Workflow.RAW_DATA}, synchronize_session="evaluate"
        )
        session.commit()
    finally:
        session.close()


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    try:
        session.query(Case).filter(Case.data_analysis == Workflow.RAW_DATA).update(
            {"data_analysis": "fastq"}, synchronize_session="evaluate"
        )
        session.query(Analysis).filter(Analysis.workflow == Workflow.RAW_DATA).update(
            {"workflow": "fastq"}, synchronize_session="evaluate"
        )
        session.commit()
    finally:
        session.close()
