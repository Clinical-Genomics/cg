"""add uploaded to vogue column to analysis

Revision ID: 49ded71bd1a1
Revises: 6d74453565f2
Create Date: 2021-03-10 13:32:40.247574

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '49ded71bd1a1'
down_revision = '6d74453565f2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('analysis', sa.Column('uploaded_to_vogue_at', sa.DateTime(), nullable=True))
    pass


def downgrade():
    op.drop_column('analysis', 'uploaded_to_vogue')
    pass
