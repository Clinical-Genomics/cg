"""Wider workflow version column

Revision ID: 636b19c06a3e
Revises: f7b8a0627abe
Create Date: 2025-06-26 10:19:41.528568

"""

from enum import StrEnum

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "636b19c06a3e"
down_revision = "f7b8a0627abe"
branch_labels = None
depends_on = None


class Workflow(StrEnum):
    BALSAMIC = "balsamic"
    BALSAMIC_PON = "balsamic-pon"
    BALSAMIC_UMI = "balsamic-umi"
    DEMULTIPLEX = "demultiplex"
    FLUFFY = "fluffy"
    JASEN = "jasen"
    MICROSALT = "microsalt"
    MIP_DNA = "mip-dna"
    MIP_RNA = "mip-rna"
    MUTANT = "mutant"
    NALLO = "nallo"
    RAREDISEASE = "raredisease"
    RAW_DATA = "raw-data"
    RNAFUSION = "rnafusion"
    RSYNC = "rsync"
    SPRING = "spring"
    TAXPROFILER = "taxprofiler"
    TOMTE = "tomte"


Base = sa.orm.declarative_base()


class Case(Base):
    __tablename__ = "case"
    id = sa.Column(sa.types.Integer, primary_key=True)
    data_analysis = sa.Column(
        sa.types.Enum(*(workflow.value for workflow in Workflow)), nullable=False
    )


def upgrade():
    op.alter_column(
        table_name="analysis",
        column_name="workflow_version",
        type_=sa.VARCHAR(length=64),
        existing_type=sa.VARCHAR(length=32),
    )
    op.alter_column(
        table_name="case",
        column_name="data_analysis",
        nullable=False,
        existing_nullable=True,
        existing_type=sa.types.Enum(*(workflow.value for workflow in Workflow)),
    )


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    op.alter_column(
        table_name="case",
        column_name="data_analysis",
        nullable=True,
        existing_nullable=False,
        existing_type=sa.types.Enum(*(workflow.value for workflow in Workflow)),
    )

    for case in session.query(Case).filter(len(Case.data_analysis) > 32).all():
        # Replace with placeholder value
        case.data_analysis = "0.0.0"

    op.alter_column(
        table_name="analysis",
        column_name="workflow_version",
        type_=sa.VARCHAR(length=32),
        existing_type=sa.VARCHAR(length=64),
    )
