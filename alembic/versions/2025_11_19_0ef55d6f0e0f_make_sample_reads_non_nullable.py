"""Make sample reads non-nullable

Revision ID: 0ef55d6f0e0f
Revises: 3874118753ff
Create Date: 2025-11-19 16:22:00.571238

"""

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from alembic import op
from cg.store.models import BigInt

# revision identifiers, used by Alembic.
revision = "0ef55d6f0e0f"
down_revision = "3874118753ff"
branch_labels = None
depends_on = None


class Base(DeclarativeBase):
    pass


class Sample(Base):
    __tablename__ = "sample"
    reads: Mapped[BigInt | None] = mapped_column(default=0)


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    for sample in session.query(Sample).filter(Sample.reads.is_(None)).all():
        sample.reads = 0
        session.add(sample)
    session.commit()
    op.alter_column(table_name="sample", column_name="reads", nullable=False)


def downgrade():
    op.alter_column(table_name="sample", column_name="reads", nullable=True)
