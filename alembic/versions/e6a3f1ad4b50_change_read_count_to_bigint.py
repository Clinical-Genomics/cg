"""Change read count to BigInt

Revision ID: e6a3f1ad4b50
Revises: f5e0db62a5a7
Create Date: 2023-06-01 16:48:37.134267

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e6a3f1ad4b50'
down_revision = 'f5e0db62a5a7'
branch_labels = None
depends_on = None


def upgrade():
    # Alter the column to use BigInteger
    op.alter_column('sample_lane_sequencing_metrics', 'sample_total_reads_in_lane', type_=sa.BigInteger)


def downgrade():
    # Alter the column to use Integer
    op.alter_column('sample_lane_sequencing_metrics', 'sample_total_reads_in_lane', type_=sa.Integer)