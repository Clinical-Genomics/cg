"""Modifies available delivery options

Revision ID: 2968d39ac35f
Revises: ddc94088be4d
Create Date: 2022-07-19 13:34:18.685207

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, types, orm

revision = "2968d39ac35f"
down_revision = "ddc94088be4d"
branch_labels = None
depends_on = None

Base = declarative_base()
added_options = ("fastq_analysis", "fastq_analysis_scout", "analysis_scout")
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
    "fastq_qc-analysis-cram": "fastq_analysis",
    "fastq_qc-analysis-cram-scout": "fastq_analysis_scout",
}
downgrade_map = {
    "fastq_analysis": "fastq_qc-analysis-cram",
    "fastq_analysis_scout": "fastq_qc-analysis-cram-scout",
}


class Family(Base):
    __tablename__ = "family"
    data_delivery = Column(types.VARCHAR(64))


def upgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for case in session.query(Family).filter(Family.data_delivery in removed_options):
        case.data_delivery = update_map[case.data_delivery]
    session.commit()
    op.alter_column("family", "data_delivery", type_=types.VARCHAR(64))


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for case in session.query(Family).filter(Family.data_delivery in added_options):
        case.data_delivery = downgrade_map[case.data_delivery]
    session.commit()
    op.alter_column("family", "data_delivery", type_=old_enum)
