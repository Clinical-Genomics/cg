"""Add tomte to analysis options

Revision ID: b2fcb2ada306
Revises: e6e6ead5b0c2
Create Date: 2024-03-14 17:10:09.156438

"""
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import declarative_base

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2fcb2ada306"
down_revision = "e6e6ead5b0c2"
branch_labels = None
depends_on = None

Base = declarative_base()

new_workflow = "tomte"
downgrade_workflow_to = "mip-rna"

old_options: list[str] = [
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
]


new_options = sorted(
    old_options
    + [
        new_workflow,
    ]
)

old_analysis_enum = mysql.ENUM(*old_options)
new_analysis_enum = mysql.ENUM(*new_options)


class Analysis(Base):
    __tablename__ = "analysis"
    id = sa.Column(sa.types.Integer, primary_key=True)
    workflow = sa.Column(sa.types.Enum(*new_options))


class Case(Base):
    __tablename__ = "case"
    id = sa.Column(sa.types.Integer, primary_key=True)
    data_analysis = sa.Column(sa.types.Enum(*new_options))
    internal_id = sa.Column(sa.types.String)


def upgrade():
    op.alter_column("case", "data_analysis", type_=new_analysis_enum)
    op.alter_column("analysis", "workflow", type_=new_analysis_enum)


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for analysis in session.query(Analysis).filter(Analysis.workflow == new_workflow):
        print(
            f"Changing workflow for Analysis {Analysis.case.internal_id}, {Analysis.completed_at} to {downgrade_workflow_to}"
        )
        analysis.workflow = downgrade_workflow_to
    for case in session.query(Case).filter(Case.data_analysis == new_workflow):
        print(f"Changing data_analysis for Case {case.internal_id} to {downgrade_workflow_to}")
        case.data_analysis = downgrade_workflow_to
    op.alter_column("case", "data_analysis", type_=old_analysis_enum)
    op.alter_column("analysis", "workflow", type_=old_analysis_enum)
    session.commit()
