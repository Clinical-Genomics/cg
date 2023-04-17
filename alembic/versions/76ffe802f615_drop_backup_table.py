"""Drop Backup table

Revision ID: 76ffe802f615
Revises: 554140bc13e4
Create Date: 2023-04-17 13:02:09.449179

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "76ffe802f615"
down_revision = "554140bc13e4"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("backup")


def downgrade():
    op.create_table(
        "backup",
        sa.Column("runname", sa.String(255), primary_key=True),
        sa.Column("startdate", sa.Date, nullable=False),
        sa.Column("nas", sa.String(255)),
        sa.Column("nasdir", sa.String(255)),
        sa.Column("starttonas", sa.DateTime),
        sa.Column("endtonas", sa.DateTime),
        sa.Column("preproc", sa.String(255)),
        sa.Column("preprocdir", sa.String(255)),
        sa.Column("startpreproc", sa.DateTime),
        sa.Column("endpreproc", sa.DateTime),
        sa.Column("frompreproc", sa.DateTime),
        sa.Column("analysis", sa.String(255)),
        sa.Column("analysisdir", sa.String(255)),
        sa.Column("toanalysis", sa.DateTime),
        sa.Column("fromanalysis", sa.DateTime),
        sa.Column("inbackupdir", sa.Integer),
        sa.Column(
            "backuptape_id", sa.Integer, sa.ForeignKey("backuptape.backuptape_id"), nullable=False
        ),
        sa.Column("backupdone", sa.DateTime),
        sa.Column("md5done", sa.DateTime),
    )
