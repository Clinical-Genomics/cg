"""fix-sars-cov-2-data-analysis-to-database

Revision ID: 432379a1adfa
Revises: 6d74453565f2
Create Date: 2021-03-16 12:05:13.275423

"""
from alembic import op
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = '432379a1adfa'
down_revision = '6d74453565f2'
branch_labels = None
depends_on = None


old_options = ("balsamic", "fastq", "fluffy", "microsalt", "mip-dna", "mip-rna")
new_options = sorted(old_options + ("sars-cov-2",))

old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("family", "data_analysis", type_=new_enum)


def downgrade():
    op.alter_column("family", "data_analysis", type_=old_enum)
