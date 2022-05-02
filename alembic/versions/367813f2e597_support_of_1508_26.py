"""support OF 1508:26

Revision ID: 367813f2e597
Revises: 0baf8309d227
Create Date: 2022-04-06 10:45:32.903682

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "367813f2e597"
down_revision = "0baf8309d227"
branch_labels = None
depends_on = None


old_options = ("balsamic", "fastq", "fluffy", "microsalt", "mip-dna", "mip-rna", "sars-cov-2")
new_options = sorted(old_options + ("balsamic-umi",))

old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.drop_column("sample", "time_point")
    op.alter_column("family", "data_analysis", type_=new_enum)
    op.alter_column("analysis", "pipeline", type_=new_enum)


def downgrade():
    op.add_column("sample", sa.Column("time_point", sa.Integer))
    op.alter_column("family", "data_analysis", type_=old_enum)
    op.alter_column("analysis", "pipeline", type_=old_enum)
