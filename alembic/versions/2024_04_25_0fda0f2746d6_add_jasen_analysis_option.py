"""Add Jasen analysis option

Revision ID: 0fda0f2746d6
Revises: f7a1394cf7cd
Create Date: 2024-04-25 12:17:39.250700

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


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


def upgrade():
    op.alter_column("analysis", "workflow", type_=new_enum)
    op.alter_column("application_limitations", "workflow", type_=new_enum)
    op.alter_column("case", "data_analysis", type_=new_enum)
    op.alter_column("order", "workflow", type_=new_enum)


def downgrade():
    op.alter_column("analysis", "workflow", type_=old_enum)
    op.alter_column("application_limitations", "workflow", type_=old_enum)
    op.alter_column("case", "data_analysis", type_=old_enum)
    op.alter_column("order", "workflow", type_=old_enum)
