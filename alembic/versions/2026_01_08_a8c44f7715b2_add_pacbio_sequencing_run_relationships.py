"""add pacbio sequencing run relationships

Revision ID: a8c44f7715b2
Revises: 8ae1f94131ba
Create Date: 2026-01-08 11:26:17.226089

"""

from enum import StrEnum
from typing import Annotated

import sqlalchemy as sa
from sqlalchemy import BLOB, DECIMAL, VARCHAR, BigInteger, ForeignKey, Numeric, String
from sqlalchemy import Text as SQLText
from sqlalchemy import types
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from alembic import op

# revision identifiers, used by Alembic.
revision = "a8c44f7715b2"
down_revision = "8ae1f94131ba"
branch_labels = None
depends_on = None

BigInt = Annotated[int, None]
Blob = Annotated[bytes, None]
Decimal = Annotated[float, None]
Num_6_2 = Annotated[float, 6]
Str32 = Annotated[str, 32]
Str64 = Annotated[str, 64]
Str128 = Annotated[str, 128]
Str255 = Annotated[str, 255]
Str256 = Annotated[str, 256]
Text = Annotated[str, None]
VarChar128 = Annotated[str, 128]

PrimaryKeyInt = Annotated[int, mapped_column(primary_key=True)]
UniqueStr = Annotated[str, mapped_column(String(32), unique=True)]
UniqueStr64 = Annotated[str, mapped_column(String(64), unique=True)]


class RevioNames(StrEnum):
    BETTY = "Betty"
    WILMA = "Wilma"


class Base(DeclarativeBase):
    type_annotation_map = {
        BigInt: BigInteger,
        Blob: BLOB,
        Decimal: DECIMAL,
        Num_6_2: Numeric(6, 2),
        Str32: String(32),
        Str64: String(64),
        Str128: String(128),
        Str255: String(255),
        Str256: String(256),
        Text: SQLText,
        VarChar128: VARCHAR(128),
    }


class PacbioSequencingRun(Base):
    """PacBio sequencing run, consisting of a set of SMRT-cells sequenced simultaneously."""

    __tablename__ = "pacbio_sequencing_run"

    id: Mapped[PrimaryKeyInt]
    run_name: Mapped[Str64] = mapped_column(unique=True)
    processed: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[Text] = mapped_column(default="")
    instrument_name: Mapped[RevioNames] = mapped_column(
        types.Enum(*(revio_name.value for revio_name in RevioNames))
    )


class InstrumentRun(Base):
    """Parent model for the different types of instrument runs."""

    __tablename__ = "instrument_run"

    id: Mapped[PrimaryKeyInt]


class PacbioSMRTCellMetrics(InstrumentRun):
    __tablename__ = "pacbio_smrt_cell_metrics"

    id: Mapped[int] = mapped_column(
        ForeignKey("instrument_run.id", ondelete="CASCADE"), primary_key=True
    )
    pacbio_sequencing_run_id: Mapped[int] = mapped_column(ForeignKey("pacbio_sequencing_run.id"))
    run_name: Mapped[Str32]


def upgrade():
    bind: sa.Connection = op.get_bind()
    session = Session(bind=bind)
    op.add_column(
        "pacbio_smrt_cell_metrics",
        sa.Column(
            "pacbio_sequencing_run_id",
            sa.Integer,
            sa.ForeignKey(
                "pacbio_sequencing_run.id", name="pacbio_smrt_cell_metrics_pacbio_sequencing_run_fk"
            ),
            nullable=True,
        ),
    )
    for smrt_cell_metric in session.query(PacbioSMRTCellMetrics).all():
        pacbio_run = (
            session.query(PacbioSequencingRun).filter_by(run_name=smrt_cell_metric.run_name).one()
        )
        smrt_cell_metric.pacbio_sequencing_run_id = pacbio_run.id
    session.commit()
    op.alter_column(
        "pacbio_smrt_cell_metrics",
        "pacbio_sequencing_run_id",
        existing_type=sa.Integer,
        nullable=False,
    )
    op.drop_column("pacbio_smrt_cell_metrics", "run_name")
    session.close()


def downgrade():
    bind: sa.Connection = op.get_bind()
    session = Session(bind=bind)
    op.add_column(
        "pacbio_smrt_cell_metrics", sa.Column("run_name", sa.String(length=32), nullable=True)
    )
    for smrt_cell_metric in session.query(PacbioSMRTCellMetrics).all():
        pacbio_run = (
            session.query(PacbioSequencingRun)
            .filter_by(id=smrt_cell_metric.pacbio_sequencing_run_id)
            .one()
        )
        smrt_cell_metric.run_name = pacbio_run.run_name
    session.commit()
    op.alter_column(
        "pacbio_smrt_cell_metrics", "run_name", existing_type=sa.String(length=32), nullable=False
    )
    op.drop_constraint(
        constraint_name="pacbio_smrt_cell_metrics_pacbio_sequencing_run_fk",
        table_name="pacbio_smrt_cell_metrics",
        type_="foreignkey",
    )
    op.drop_column("pacbio_smrt_cell_metrics", "pacbio_sequencing_run_id")
    session.close()
