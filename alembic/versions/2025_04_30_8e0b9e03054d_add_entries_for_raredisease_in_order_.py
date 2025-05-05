"""add entries for raredisease in order type application

Revision ID: 8e0b9e03054d
Revises: 039dbdf8af01
Create Date: 2025-04-30 09:56:53.670128

"""

import sqlalchemy as sa
from sqlalchemy.orm import Session, declarative_base

from alembic import op

Base = declarative_base()

# revision identifiers, used by Alembic.
revision = "8e0b9e03054d"
down_revision = "039dbdf8af01"
branch_labels = None
depends_on = None

bind: sa.Connection = op.get_bind()


class OrderTypeApplication(Base):
    __table__ = sa.Table("order_type_application", sa.MetaData(), autoload_with=bind)


def upgrade():
    session: Session = Session(bind=bind)
    mip_dna_rows: list[OrderTypeApplication] = (
        session.query(OrderTypeApplication).filter_by(order_type="MIP_DNA").all()
    )

    for row in mip_dna_rows:
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
