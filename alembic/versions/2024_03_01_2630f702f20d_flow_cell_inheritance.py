"""flow_cell_inheritance

Revision ID: 2630f702f20d
Revises: e6e6ead5b0c2
Create Date: 2024-03-01 15:29:53.132689

"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from alembic import op

# revision identifiers, used by Alembic.
revision = "2630f702f20d"
down_revision = "e6e6ead5b0c2"
branch_labels = None
depends_on = None


class Base(DeclarativeBase):
    pass


class OldFlowCell(Base):
    __tablename__ = "flowcell"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    sequencer_type: Mapped[str | None] = mapped_column(
        types.Enum("hiseqga", "hiseqx", "novaseq", "novaseqx")
    )
    sequencer_name: Mapped[str | None]
    sequenced_at: Mapped[datetime | None]
    status: Mapped[str | None] = mapped_column(default="ondisk")
    archived_at: Mapped[datetime | None]
    has_backup: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=datetime.now)


class SequencingUnit(Base):
    __tablename__ = "sequencing_unit"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(types.String(32), unique=True)
    type: Mapped[str] = mapped_column(types.Enum("ILLUMINA"))

    __mapper_args__ = {
        "polymorphic_identity": "sequencing_unit",
        "polymorphic_on": "type",
    }


class IlluminaFlowCell(SequencingUnit):
    __tablename__ = "illumina_flow_cell"
    id: Mapped[int] = mapped_column(ForeignKey("sequencing_unit.id"), primary_key=True)
    sequencer_type: Mapped[str | None] = mapped_column(
        types.Enum("hiseqga", "hiseqx", "novaseq", "novaseqx")
    )
    sequencer_name: Mapped[str | None] = mapped_column(types.String(32))
    sequenced_at: Mapped[datetime | None]
    status: Mapped[str | None] = mapped_column(
        types.Enum("ondisk", "removed", "requested", "processing", "retrieved"),
        default="ondisk",
    )
    archived_at: Mapped[datetime | None]
    has_backup: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=datetime.now)

    __mapper_args__ = {
        "polymorphic_identity": "ILLUMINA",
    }


def get_session() -> Session:
    bind = op.get_bind()
    return Session(bind=bind)


def create_tables():
    Base.metadata.create_all(bind=op.get_bind())


def upgrade():
    session: Session = get_session()
    create_tables()

    for flow_cell in session.query(OldFlowCell):
        session.add(
            IlluminaFlowCell(
                id=flow_cell.id,
                name=flow_cell.name,
                sequencer_type=flow_cell.sequencer_type,
                sequencer_name=flow_cell.sequencer_name,
                sequenced_at=flow_cell.sequenced_at,
                status=flow_cell.status,
                archived_at=flow_cell.archived_at,
                has_backup=flow_cell.has_backup,
                updated_at=flow_cell.updated_at,
            )
        )
    session.commit()


def downgrade():
    op.drop_table("illumina_flow_cell")
    op.drop_table("nanopore_flow_cell")
    op.drop_table("sequencing_unit")
