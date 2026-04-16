"""Add Jasen analysis option

Revision ID: 0fda0f2746d6
Revises: f7a1394cf7cd
Create Date: 2024-04-25 12:17:39.250700

"""

from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import declarative_base

from alembic import op

# revision identifiers, used by Alembic.
revision = "0fda0f2746d6"
down_revision = "f7a1394cf7cd"
branch_labels = None
depends_on = None

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
    "mutant",
    "raredisease",
    "rnafusion",
    "rsync",
    "spring",
    "taxprofiler",
    "tomte",
)
new_options = sorted(old_options + ("jasen",))

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
    JASEN: str = "jasen"
    MICROSALT: str = "microsalt"
    MIP_DNA: str = "mip-dna"
    MIP_RNA: str = "mip-rna"
    MUTANT: str = "mutant"
    RAREDISEASE: str = "raredisease"
    RNAFUSION: str = "rnafusion"
    RSYNC: str = "rsync"
    SPRING: str = "spring"
    TAXPROFILER: str = "taxprofiler"
    TOMTE: str = "tomte"


Base = declarative_base()


class Analysis(Base):
    __tablename__ = "analysis"
    id = sa.Column(sa.types.Integer, primary_key=True)
    workflow = sa.Column(sa.types.Enum(*list(Workflow)))


class ApplicationLimitations(Base):
    __tablename__ = "application_limitations"
    id = sa.Column(sa.types.Integer, primary_key=True)
    workflow = sa.Column(sa.types.Enum(*list(Workflow)))


class Case(Base):
    __tablename__ = "case"
    id = sa.Column(sa.types.Integer, primary_key=True)
    data_analysis = sa.Column(sa.types.Enum(*list(Workflow)))


class Order(Base):
    __tablename__ = "order"
    id = sa.Column(sa.types.Integer, primary_key=True)
    workflow = sa.Column(sa.types.Enum(*list(Workflow)))


def upgrade():
    op.alter_column("analysis", "workflow", type_=new_enum)
    op.alter_column("application_limitations", "workflow", type_=new_enum)
    op.alter_column("case", "data_analysis", type_=new_enum)
    op.alter_column("order", "workflow", type_=new_enum)


def downgrade():
    # Set jasen tagged workflow fields to fastq (as something generic)
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    # Analysis
    for analysis in session.query(Analysis).filter(Analysis.workflow == "jasen"):
        analysis.workflow = "fastq"

    # Application limitations
    for application_limitations in session.query(ApplicationLimitations).filter(
        ApplicationLimitations.workflow == "jasen"
    ):
        application_limitations.workflow = "fastq"

    # Case Using underscore in the variable name to not clash with python case
    # keyword.
    for case_ in session.query(Case).filter(Case.data_analysis == "jasen"):
        case_.data_analysis = "fastq"

    # Order
    for order in session.query(Order).filter(Order.workflow == "jasen"):
        order.workflow = "fastq"

    session.commit()

    # Change column type to no longer include jasen
    op.alter_column("analysis", "workflow", type_=old_enum)
    op.alter_column("application_limitations", "workflow", type_=old_enum)
    op.alter_column("case", "data_analysis", type_=old_enum)
    op.alter_column("order", "workflow", type_=old_enum)
