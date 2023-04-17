"""Drop Backuptape table

Revision ID: 99bff6c96e88
Revises: 76ffe802f615
Create Date: 2023-04-17 13:03:08.111829

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "99bff6c96e88"
down_revision = "76ffe802f615"
branch_labels = None
depends_on = None


def upgrade():
    table_name = "backuptape"
    if table_name in op.get_context().bind.table_names():
        op.drop_table(table_name)


def downgrade():
    op.create_table(
        "backuptape",
        sa.Column("backuptape_id", sa.Integer, primary_key=True),
        sa.Column("tapedir", sa.String(255)),
        sa.Column("nametext", sa.String(255)),
        sa.Column("tapedate", sa.DateTime),
    )
