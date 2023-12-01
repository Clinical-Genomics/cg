"""Add dev priority

Revision ID: 3ac26865d2bf
Revises: b105b426af99
Create Date: 2023-12-01 11:39:35.273991

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "3ac26865d2bf"
down_revision = "b105b426af99"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE `case` MODIFY COLUMN priority ENUM('research', 'standard', 'priority', 'express', 'clinical_trials', 'development')"
    )


def downgrade():
    op.execute("UPDATE `case` SET priority = 'research' WHERE priority = 'development'")
    op.execute(
        "ALTER TABLE `case` MODIFY COLUMN priority ENUM('research', 'standard', 'priority', 'express', 'clinical_trials')"
    )
