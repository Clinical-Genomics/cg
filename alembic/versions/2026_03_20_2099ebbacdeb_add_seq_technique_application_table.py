"""add_seq_technique_application_table

Revision ID: 2099ebbacdeb
Revises: 2c9a49ce5512
Create Date: 2026-03-20 14:39:55.100307

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2099ebbacdeb"
down_revision = "2c9a49ce5512"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "application",
        sa.Column(
            "read_type",
            sa.Enum("long-read", "short-read", "optical-mapping"),
            nullable=False,
            server_default="short-read",
        ),
    )
    op.alter_column("application", "read_type", server_default=None)


def downgrade():
    op.drop_column("application", "read_type")
