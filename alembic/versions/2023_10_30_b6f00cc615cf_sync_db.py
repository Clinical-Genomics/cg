"""Sync db

Revision ID: b6f00cc615cf
Revises: 392e49db40fc
Create Date: 2023-10-30 14:57:48.992414

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "b6f00cc615cf"
down_revision = "392e49db40fc"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "application", "min_sequencing_depth", existing_type=mysql.INTEGER(), nullable=False
    )
    op.drop_constraint(
        "application_limitations_ibfk_1", "application_limitations", type_="foreignkey"
    )
    op.create_foreign_key(
        None, "application_limitations", "application", ["application_id"], ["id"]
    )
    op.alter_column(
        "family",
        "action",
        existing_type=mysql.ENUM("analyze", "running", "hold"),
        type_=sa.Enum("analyze", "hold", "running"),
        existing_nullable=True,
    )
    op.alter_column(
        "family",
        "data_delivery",
        existing_type=mysql.VARCHAR(length=64),
        type_=sa.Enum(
            "analysis",
            "analysis-scout",
            "fastq",
            "fastq-scout",
            "fastq_qc",
            "fastq-analysis",
            "fastq_qc-analysis",
            "fastq-analysis-scout",
            "nipt-viewer",
            "no-delivery",
            "scout",
            "statina",
            name="datadelivery",
        ),
        existing_nullable=True,
    )
    op.alter_column(
        "flowcell",
        "status",
        existing_type=mysql.ENUM("ondisk", "processing", "removed", "requested", "retrieved"),
        type_=sa.Enum("ondisk", "removed", "requested", "processing", "retrieved"),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "flowcell",
        "status",
        existing_type=sa.Enum("ondisk", "removed", "requested", "processing", "retrieved"),
        type_=mysql.ENUM("ondisk", "processing", "removed", "requested", "retrieved"),
        existing_nullable=True,
    )
    op.alter_column(
        "family",
        "data_delivery",
        existing_type=sa.Enum(
            "analysis",
            "analysis-scout",
            "fastq",
            "fastq-scout",
            "fastq_qc",
            "fastq-analysis",
            "fastq_qc-analysis",
            "fastq-analysis-scout",
            "nipt-viewer",
            "no-delivery",
            "scout",
            "statina",
            name="datadelivery",
        ),
        type_=mysql.VARCHAR(length=64),
        existing_nullable=True,
    )
    op.alter_column(
        "family",
        "action",
        existing_type=sa.Enum("analyze", "hold", "running"),
        type_=mysql.ENUM("analyze", "running", "hold"),
        existing_nullable=True,
    )
    op.drop_constraint(None, "application_limitations", type_="foreignkey")
    op.create_foreign_key(
        "application_limitations_ibfk_1",
        "application_limitations",
        "application",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column(
        "application", "min_sequencing_depth", existing_type=mysql.INTEGER(), nullable=True
    )
