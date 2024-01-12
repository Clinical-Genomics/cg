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

old_options = set(Pipeline)
old_options.remove("mutant")
old_options.add("sars-cov-2")
new_options = set(Pipeline)

old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    op.alter_column("case", "data_analysis", type_=new_enum)
    op.alter_column("analysis", "pipeline", type_=new_enum)

    for case in session.query(Case).filter(Case.data_analysis == "sars-cov-2"):
        print(f"Altering case: {str(case)}")
        case.data_analysis = str(Pipeline.MUTANT)
        print(f"Altered case: {str(case)}")

    for analysis in session.query(Analysis).filter(Analysis.pipeline == "sars-cov-2"):
        print(f"Altering analysis: {str(analysis)}")
        analysis.pipeline = str(Pipeline.MUTANT)
        print(f"Altered analysis: {str(analysis)}")

    session.commit()


def downgrade():
    op.alter_column("case", "data_analysis", type_=old_enum)
    op.alter_column("analysis", "pipeline", type_=old_enum)
