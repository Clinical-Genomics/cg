"""“add-phenotype_groups-to-sample”

Revision ID: 1c27462b49f6
Revises: 7e344b9438bf
Create Date: 2021-06-30 10:24:45.767659

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "1c27462b49f6"
down_revision = "7e344b9438bf"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("family", "_synopsis", new_column_name="synopsis", existing_type=sa.Text())
    op.add_column("sample", sa.Column("_phenotype_groups", sa.Text(), nullable=True))
    op.add_column("sample", sa.Column("subject_id", sa.String(length=128), nullable=True))


def downgrade():
    op.alter_column("family", "synopsis", new_column_name="_synopsis", existing_type=sa.Text())
    op.drop_column("sample", "_phenotype_groups")
    op.drop_column("sample", "subject_id")
