"""Make all Pacbio model attributes non-nullable

Revision ID: 3503b53a9bc3
Revises: fd7c9d246255
Create Date: 2024-10-17 10:24:44.124036

"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "3503b53a9bc3"
down_revision = "fd7c9d246255"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="run_name",
        existing_type=mysql.VARCHAR(length=64),
        type_=sa.String(length=32),
        existing_nullable=True,
        nullable=False,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="started_at",
        existing_type=sa.DateTime(),
        existing_nullable=True,
        nullable=False,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="completed_at",
        existing_type=sa.DateTime(),
        existing_nullable=True,
        nullable=False,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="barcoded_hifi_reads",
        existing_type=mysql.BIGINT(),
        nullable=False,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="barcoded_hifi_reads_percentage",
        existing_type=mysql.FLOAT(),
        type_=sa.Numeric(precision=6, scale=2),
        existing_nullable=True,
        nullable=False,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="barcoded_hifi_yield",
        existing_type=mysql.BIGINT(),
        nullable=False,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="barcoded_hifi_yield_percentage",
        existing_type=mysql.FLOAT(),
        type_=sa.Numeric(precision=6, scale=2),
        existing_nullable=True,
        nullable=False,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="barcoded_hifi_mean_read_length",
        existing_type=mysql.BIGINT(),
        nullable=False,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="unbarcoded_hifi_reads",
        existing_type=mysql.BIGINT(),
        nullable=False,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="unbarcoded_hifi_yield",
        existing_type=mysql.BIGINT(),
        nullable=False,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="unbarcoded_hifi_mean_read_length",
        existing_type=mysql.BIGINT(),
        nullable=False,
    )
    op.alter_column(
        table_name="pacbio_sample_run_metrics",
        column_name="polymerase_mean_read_length",
        existing_type=sa.BIGINT(),
        existing_nullable=True,
        nullable=False,
    )


def downgrade():
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="run_name",
        existing_type=sa.String(length=32),
        type_=mysql.VARCHAR(length=64),
        nullable=True,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="started_at",
        existing_type=sa.DateTime(),
        nullable=True,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="completed_at",
        existing_type=sa.DateTime(),
        nullable=True,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="barcoded_hifi_reads",
        existing_type=mysql.BIGINT(),
        nullable=True,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="barcoded_hifi_reads_percentage",
        existing_type=sa.Numeric(precision=6, scale=2),
        type_=mysql.FLOAT(),
        nullable=True,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="barcoded_hifi_yield",
        existing_type=mysql.BIGINT(),
        nullable=True,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="barcoded_hifi_yield_percentage",
        existing_type=sa.Numeric(precision=6, scale=2),
        type_=mysql.FLOAT(),
        nullable=True,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="barcoded_hifi_mean_read_length",
        existing_type=mysql.BIGINT(),
        nullable=True,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="unbarcoded_hifi_reads",
        existing_type=mysql.BIGINT(),
        nullable=True,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="unbarcoded_hifi_yield",
        existing_type=mysql.BIGINT(),
        nullable=True,
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="unbarcoded_hifi_mean_read_length",
        existing_type=mysql.BIGINT(),
        nullable=True,
    )
    op.alter_column(
        table_name="pacbio_sample_run_metrics",
        column_name="polymerase_mean_read_length",
        existing_type=sa.BIGINT,
        nullable=True,
    )
