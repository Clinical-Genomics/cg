"""support_novaseqx_flow_cell_table

Revision ID: 2fdb42ba801a
Revises: c3fdf3a8a5b3
Create Date: 2023-07-10 09:38:21.471980

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2fdb42ba801a"
down_revision = "c3fdf3a8a5b3"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="flowcell",
        column_name="sequencer_type",
        type_=sa.Enum("hiseqga", "hiseqx", "novaseq", "novaseqx"),
    )


def downgrade():
    op.alter_column(
        table_name="flowcell",
        column_name="sequencer_type",
        type_=sa.Enum("hiseqga", "hiseqx", "novaseq"),
    )
