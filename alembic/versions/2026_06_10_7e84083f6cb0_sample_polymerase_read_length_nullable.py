"""Sample polymerase read length nullable

Revision ID: 7e84083f6cb0
Revises: 8cd14469c35f
Create Date: 2026-06-10 11:38:36.405971

"""

import sqlalchemy as sa
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from alembic import op

# revision identifiers, used by Alembic.
revision = "7e84083f6cb0"
down_revision = "8cd14469c35f"
branch_labels = None
depends_on = None


class PacbioSampleSequencingMetrics(DeclarativeBase):
    __tablename__ = "pacbio_sample_run_metrics"

    id: Mapped[int] = mapped_column(
        ForeignKey("sample_run_metrics.id", ondelete="CASCADE"), primary_key=True
    )
    polymerase_mean_read_length: Mapped[BigInteger | None]


def upgrade():
    op.alter_column(
        table_name="pacbio_sample_run_metrics",
        column_name="polymerase_mean_read_length",
        existing_type=sa.BIGINT,
        nullable=True,
    )


def downgrade():
    # Set a default value so that the downgrade works
    bind: sa.Connection = op.get_bind()
    session: Session = Session(bind=bind)
    for sample_metric in session.query(PacbioSampleSequencingMetrics).filter(
        PacbioSampleSequencingMetrics.polymerase_mean_read_length.is_(None)
    ):
        sample_metric.polymerase_mean_read_length = BIGINT(1)
    session.commit()
    op.alter_column(
        table_name="pacbio_sample_run_metrics",
        column_name="polymerase_mean_read_length",
        existing_type=sa.BIGINT,
        nullable=False,
    )
