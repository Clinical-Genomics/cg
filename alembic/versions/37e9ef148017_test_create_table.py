"""test create table

Revision ID: 37e9ef148017
Revises: 6d74453565f2
Create Date: 2021-02-04 15:16:15.917358

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "37e9ef148017"
down_revision = "6d74453565f2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "test",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("test", sa.String(50), nullable=False),
        sa.Column("description", sa.Unicode(200)),
    )


def downgrade():
    op.drop_table("test")
