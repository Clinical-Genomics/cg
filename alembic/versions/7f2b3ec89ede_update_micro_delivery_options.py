"""Update micro delivery options

Revision ID: 7f2b3ec89ede
Revises: 20750539a335
Create Date: 2022-11-10 16:20:01.745778

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
from cg.store.models import Family

revision = "7f2b3ec89ede"
down_revision = "20750539a335"
branch_labels = None
depends_on = None
changed_options = ("fastq_qc", "fastq_qc-analysis")


def upgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for case in session.query(Family):
        if case.data_delivery in changed_options and case.data_analysis == "microsalt":
            case.data_delivery = "fastq-analysis"
    session.commit()


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for case in session.query(Family):
        if case.data_delivery in "fastq-analysis" and case.data_analysis == "microsalt":
            case.data_delivery = "fastq_qc-analysis"
    session.commit()
