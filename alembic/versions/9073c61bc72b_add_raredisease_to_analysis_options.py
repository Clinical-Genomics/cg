"""Add raredisease to analysis options

Revision ID: 9073c61bc72b
Revises: b6f00cc615cf
Create Date: 2023-10-31 12:23:09.239741

"""
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import declarative_base

from alembic import op
from cg.constants import Pipeline

# revision identifiers, used by Alembic.
revision = "9073c61bc72b"
down_revision = "b6f00cc615cf"
branch_labels = None
depends_on = None

Base = declarative_base()

old_analysis_options = (
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
    "taxprofiler",
)
new_analysis_options = sorted(old_analysis_options + ("raredisease",))

old_analysis_enum = mysql.ENUM(*old_analysis_options)
new_analysis_enum = mysql.ENUM(*new_analysis_options)


class Analysis(Base):
    __tablename__ = "analysis"
    id = sa.Column(sa.types.Integer, primary_key=True)
    pipeline = sa.Column(sa.types.Enum(*list(Pipeline)))


class Family(Base):
    __tablename__ = "family"
    id = sa.Column(sa.types.Integer, primary_key=True)
    data_analysis = sa.Column(sa.types.Enum(*list(Pipeline)))


def upgrade():
    op.alter_column("family", "data_analysis", type_=new_analysis_enum)
    op.alter_column("analysis", "pipeline", type_=new_analysis_enum)


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for analysis in session.query(Analysis).filter(Analysis.pipeline == "raredisease"):
        print(
            f"Changing pipeline for Analysis {Analysis.family.internal_id}, {Analysis.completed_at} to mip-dna"
        )
        analysis.pipeline = "mip-dna"
    for family in session.query(Family).filter(Family.data_analysis == "raredisease"):
        print(f"Changing data_analysis for Family {family.internal_id} to mip-dna")
        family.data_analysis = "mip-dna"
    op.alter_column("family", "data_analysis", type_=old_analysis_enum)
    op.alter_column("analysis", "pipeline", type_=old_analysis_enum)
    session.commit()
