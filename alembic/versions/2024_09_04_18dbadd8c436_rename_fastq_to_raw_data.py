"""rename_fastq_to_raw_data

Revision ID: 18dbadd8c436
Revises: bb4c6dbad991
Create Date: 2024-09-04 13:15:11.876822

"""

from sqlalchemy import orm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from alembic import op

# revision identifiers, used by Alembic.
revision = "18dbadd8c436"
down_revision = "bb4c6dbad991"
branch_labels = None
depends_on = None


class Base(DeclarativeBase):
    pass


class Case(Base):
    __tablename__ = "case"
    id: Mapped[int] = mapped_column(primary_key=True)
    data_analysis: Mapped[str | None]


class Analysis(Base):
    __tablename__ = "analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow: Mapped[str | None]


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    try:
        session.query(Case).filter(Case.data_analysis == "fastq").update(
            {"data_analysis": "raw_data"}, synchronize_session="evaluate"
        )
        session.query(Analysis).filter(Analysis.workflow == "fastq").update(
            {"workflow": "raw_data"}, synchronize_session="evaluate"
        )
        session.commit()
    finally:
        session.close()


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    try:
        session.query(Case).filter(Case.data_analysis == "raw_data").update(
            {"data_analysis": "fastq"}, synchronize_session="evaluate"
        )
        session.query(Analysis).filter(Analysis.workflow == "raw_data").update(
            {"workflow": "fastq"}, synchronize_session="evaluate"
        )
        session.commit()
    finally:
        session.close()
