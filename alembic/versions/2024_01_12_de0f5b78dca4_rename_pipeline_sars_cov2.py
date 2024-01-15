"""rename_pipeline_sars-cov2

Revision ID: de0f5b78dca4
Revises: 584840c706a0
Create Date: 2024-01-12 14:25:36.338102

"""
from sqlalchemy import orm
from sqlalchemy.dialects import mysql

from alembic import op
from cg.constants import Pipeline
from cg.store.models import Analysis, Case

# revision identifiers, used by Alembic.
revision = "de0f5b78dca4"
down_revision = "584840c706a0"
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

old_enum = mysql.ENUM(*list(old_options))
new_enum = mysql.ENUM(*list(new_options))


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    op.alter_column("case", "data_analysis", type_=mysql.VARCHAR(64))
    op.alter_column("analysis", "pipeline", type_=mysql.VARCHAR(64))

    for case in session.query(Case).filter(Case.data_analysis == "sars-cov-2"):
        print(f"Altering case: {str(case)}")
        case.data_analysis = str(Pipeline.MUTANT)
        print(f"Altered case: {str(case)}")

    for analysis in session.query(Analysis).filter(Analysis.pipeline == "sars-cov-2"):
        print(f"Altering analysis: {str(analysis)}")
        analysis.pipeline = str(Pipeline.MUTANT)
        print(f"Altered analysis: {str(analysis)}")

    op.alter_column("case", "data_analysis", type_=new_enum)
    op.alter_column("analysis", "pipeline", type_=new_enum)
    session.commit()


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    op.alter_column("case", "data_analysis", type_=mysql.VARCHAR(64))
    op.alter_column("analysis", "pipeline", type_=mysql.VARCHAR(64))

    for case in session.query(Case).filter(Case.data_analysis == Pipeline.MUTANT):
        print(f"Altering case: {str(case)}")
        case.data_analysis = "sars-cov-2"
        print(f"Altered case: {str(case)}")

    for analysis in session.query(Analysis).filter(Analysis.pipeline == Pipeline.MUTANT):
        print(f"Altering analysis: {str(analysis)}")
        analysis.pipeline = "sars-cov-2"
        print(f"Altered analysis: {str(analysis)}")

    op.alter_column("case", "data_analysis", type_=old_enum)
    op.alter_column("analysis", "pipeline", type_=old_enum)
    session.commit()
