"""Modifies available delivery options

Revision ID: 2968d39ac35f
Revises: 9c9ca9407227
Create Date: 2022-07-19 13:34:18.685207

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, types, orm

revision = "2968d39ac35f"
down_revision = "9c9ca9407227"
branch_labels = None
depends_on = None

Base = declarative_base()
added_options = ("fastq-analysis", "fastq-analysis-scout", "analysis-scout", "fastq-scout")
removed_options = ("analysis-bam", "fastq_qc-analysis-cram", "fastq_qc-analysis-cram-scout")

old_options = (
    "analysis",
    "analysis-bam",
    "fastq",
    "fastq_qc",
    "fastq_qc-analysis",
    "fastq_qc-analysis-cram",
    "fastq_qc-analysis-cram-scout",
    "nipt-viewer",
    "scout",
    "statina",
)
new_options = sorted(
    ("analysis" "fastq", "fastq_qc", "fastq_qc-analysis", "nipt-viewer", "scout") + added_options
)
old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


update_map = {
    "analysis-bam": "analysis",
    "fastq_qc-analysis-cram": "fastq-analysis",
    "fastq_qc-analysis-cram-scout": "fastq-analysis-scout",
}
downgrade_map = {
    "fastq-analysis": "fastq_qc-analysis-cram",
    "fastq-analysis-scout": "fastq_qc-analysis-cram-scout",
}


class Family(Base):
    __tablename__ = "family"
    id = Column(types.Integer, primary_key=True)
    data_delivery = Column(types.VARCHAR(64))
    internal_id = Column(types.String(32), unique=True, nullable=False)


def upgrade():
    op.alter_column("family", "data_delivery", type_=types.VARCHAR(64))
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for case in session.query(Family):
        if case.data_delivery in removed_options:
            case.data_delivery = update_map[case.data_delivery]

    session.commit()


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for case in session.query(Family):
        if case.data_delivery == "":
            case.data_delivery = None
        if case.data_delivery in added_options:
            case.data_delivery = downgrade_map[case.data_delivery]
    session.commit()
    op.alter_column("family", "data_delivery", type_=old_enum)
