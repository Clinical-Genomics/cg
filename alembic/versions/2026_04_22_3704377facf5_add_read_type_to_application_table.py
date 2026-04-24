"""add_read_type_to_application_table

Revision ID: 3704377facf5
Revises: 96667267134e
Create Date: 2026-04-22 20:54:29.709306

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "3704377facf5"
down_revision = "96667267134e"
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
