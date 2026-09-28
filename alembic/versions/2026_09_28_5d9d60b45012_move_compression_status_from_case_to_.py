"""Move compression status from Case to Sample

Revision ID: 5d9d60b45012
Revises: ac66c84f0449
Create Date: 2026-09-28 09:43:05.188646

"""

from typing import Annotated

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from alembic import op

# revision identifiers, used by Alembic.
revision = "5d9d60b45012"
down_revision = "ac66c84f0449"
branch_labels = None
depends_on = None

PrimaryKeyInt = Annotated[int, mapped_column(primary_key=True)]
Str32 = Annotated[str, 32]
Str64 = Annotated[str, 64]


class Base(DeclarativeBase):
    type_annotation_map = {
        Str32: sa.String(32),
        Str64: sa.String(64),
    }


class Case(Base):
    __tablename__ = "case"
    id: Mapped[PrimaryKeyInt]
    is_compressible: bool
    links: Mapped[list["CaseSample"]] = relationship(back_populates="case")

    @property
    def samples(self) -> list["Sample"]:
        """Return case samples."""
        return [link.sample for link in self.links]


class CaseSample(Base):
    __tablename__ = "case_sample"
    id: Mapped[PrimaryKeyInt]
    case_id: Mapped[str] = mapped_column(
        sa.ForeignKey("case.id", ondelete="CASCADE"), nullable=False
    )
    sample_id: Mapped[int] = mapped_column(
        sa.ForeignKey("sample.id", ondelete="CASCADE"), nullable=False
    )
    case: Mapped[Case] = relationship(back_populates="links")
    sample: Mapped["Sample"] = relationship(foreign_keys=[sample_id], back_populates="links")


class Sample(Base):
    __tablename__ = "sample"
    id: Mapped[PrimaryKeyInt]
    links: Mapped[list[CaseSample]] = relationship(back_populates="sample")
    skip_compression: bool


def upgrade():
    bind: sa.Connection = op.get_bind()
    session = Session(bind=bind)
    # Add the new column "skip_compression" on "sample" table (defaults to False)
    op.add_column(
        table_name="sample",
        column=sa.Column(
            name="skip_compression",
            type_=sa.Boolean,
            nullable=False,
            default=False,
        ),
    )

    # Loop through all cases with "is_compressible" = False
    cases = session.query(Case).all()
    for case in cases:
        if case.is_compressible == False:
            # For all samples such cases, set "skip_compression" to True
            for sample in case.samples:
                sample.skip_compression = True

    # Remove the "is_compressible" column from "case" table
    op.drop_column("case", "is_compressible")


def downgrade():
    bind: sa.Connection = op.get_bind()
    session = Session(bind=bind)
    # Add the "is_compressible" column to the "case" table (defaults to True)
    op.add_column(
        table_name="case", column=sa.Column(name="is_compressible", type_=sa.Boolean, default=True)
    )

    samples = session.query(Sample).where(Sample.skip_compression == True).all()
    # Loop over all samples with "skip_compression" = True
    # For all cases of these samples, set "is_compressible" to False

    # Drop the "skip_compression" column from "sample" table
    pass
