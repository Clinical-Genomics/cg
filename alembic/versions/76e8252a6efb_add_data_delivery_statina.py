"""add data-delivery statina

Revision ID: 76e8252a6efb
Revises: c76d655c8edf
Create Date: 2022-02-10 15:28:48.027691

"""
from alembic import op
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "76e8252a6efb"
down_revision = "c76d655c8edf"
branch_labels = None
depends_on = None


old_options = (
    "analysis",
    "analysis-bam",
    "fastq",
    "fastq_qc",
    "fastq_qc-analysis",
    "fastq_qc-analysis-cram",
    "fastq_qc-analysis-cram-scout",
    "nipt-viewer",
    "scout",
)
new_options = sorted(old_options + ("statina",))
old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("family", "data_delivery", type_=new_enum)
    print("setting family.data_delivery to statina where currently nipt-viewer", flush=True)
    bind = op.get_bind()
    bind.execute(
        "update family "
        "set family.data_delivery = 'statina' "
        "where family.data_delivery = 'nipt-viewer';"
    )


def downgrade():
    bind = op.get_bind()
    print("setting family.data_delivery to nipt-viewer where currently statina", flush=True)
    bind.execute(
        "update family "
        "set family.data_delivery = 'nipt-viewer' "
        "where family.data_delivery = 'statina';"
    )
    op.alter_column("family", "data_delivery", type_=old_enum)
