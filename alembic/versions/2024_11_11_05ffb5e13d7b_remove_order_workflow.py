"""remove_order_workflow

Revision ID: 05ffb5e13d7b
Revises: 3503b53a9bc3
Create Date: 2024-11-11 09:35:33.020098

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "05ffb5e13d7b"
down_revision = "3503b53a9bc3"
branch_labels = None
depends_on = None
workflows = [
    "balsamic",
    "balsamic-pon",
    "balsamic-qc",
    "balsamic-umi",
    "demultiplex",
    "raw-data",
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
    "jasen",
]


def upgrade():
    op.drop_column(table_name="order", column_name="workflow")


def downgrade():
    op.add_column(
        "order",
        sa.Column(
            "workflow",
            type_=sa.Enum(*workflows),
        ),
    )
