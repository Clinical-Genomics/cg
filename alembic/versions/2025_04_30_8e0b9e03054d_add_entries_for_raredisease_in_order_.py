"""add entries for raredisease in order type application

Revision ID: 8e0b9e03054d
Revises: 039dbdf8af01
Create Date: 2025-04-30 09:56:53.670128

"""

import sqlalchemy as sa
from sqlalchemy.orm import Session, declarative_base, mapped_column

from alembic import op

Base = declarative_base()

order_types = [
    "BALSAMIC_UMI",
    "BALSAMIC",
    "FASTQ",
    "FLUFFY",
    "METAGENOME",
    "MICROBIAL_FASTQ",
    "MICROSALT",
    "MIP_DNA",
    "MIP_RNA",
    "NALLO",
    "PACBIO_LONG_READ",
    "RAREDISEASE",
    "RML",
    "RNAFUSION",
    "SARS_COV_2",
    "TAXPROFILER",
    "TOMTE",
]

# revision identifiers, used by Alembic.
revision = "8e0b9e03054d"
down_revision = "039dbdf8af01"
branch_labels = None
depends_on = None


class OrderTypeApplication(Base):
    """Maps an order type to its allowed applications"""

    __tablename__ = "order_type_application"

    order_type = mapped_column(sa.Enum(*order_types), primary_key=True)
    application_id = mapped_column(
        sa.ForeignKey("application.id", ondelete="CASCADE"), primary_key=True
    )


def upgrade():
    bind: sa.Connection = op.get_bind()
    session: Session = Session(bind=bind)
    mip_dna_rows: list[OrderTypeApplication] = (
        session.query(OrderTypeApplication).filter_by(order_type="MIP_DNA").all()
    )

    for row in mip_dna_rows:
        exists: OrderTypeApplication | None = (
            session.query(OrderTypeApplication)
            .filter_by(order_type="RAREDISEASE", application_id=row.application_id)
            .first()
        )

        if not exists:
            rare_disease_row = OrderTypeApplication(
                order_type="RAREDISEASE",  # type: ignore
                application_id=row.application_id,  # type: ignore
            )
            session.add(rare_disease_row)

    session.commit()


def downgrade():
    # removing all RAREDISEASE entries from the order_type_application table at a later date
    # might have unintended consequences since they can be added in other ways than by this
    # migration, so there is no downgrade
    pass
