"""start using genome column in bed version

Revision ID: 2c9a49ce5512
Revises: afe71f163d20
Create Date: 2026-02-04 11:33:44.131245

"""

from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "2c9a49ce5512"
down_revision = "afe71f163d20"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="bed_version",
        column_name="genome_version",
        existing_type=sa.VARCHAR(length=32),
        type_=mysql.ENUM("hg19", "hg38", "cfam3"),
        nullable=False,
    )
    op.create_unique_constraint(
        constraint_name="shortname_version_genome_version_uc",
        table_name="bed_version",
        columns=["shortname", "version", "genome_version"],
    )


def downgrade():
    op.drop_constraint(
        constraint_name="shortname_version_genome_version_uc",
        table_name="bed_version",
        type_="unique",
    )
    op.alter_column(
        table_name="bed_version",
        column_name="genome_version",
        existing_type=mysql.ENUM("hg19", "hg38", "cfam3"),
        type_=sa.VARCHAR(length=32),
        nullable=True,
    )
