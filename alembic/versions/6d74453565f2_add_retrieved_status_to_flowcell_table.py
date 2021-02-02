"""add retrieved status to flowcell table

Revision ID: 6d74453565f2
Revises: 
Create Date: 2021-02-02 11:11:59.273754

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6d74453565f2"
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.dialects import mysql

old_options = ("ondisk", "removed", "requested", "processing")
new_options = sorted(old_options + ("retrieved",))

old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("flowcell", "status", existing_type=new_enum)


def downgrade():
    op.alter_column("flowcell", "status", existing_type=old_enum)
