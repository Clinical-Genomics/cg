"""add top-up case action

Revision ID: be6552c03d7f
Revises: 8e0b9e03054d
Create Date: 2025-05-13 15:25:24.572276

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "be6552c03d7f"
down_revision = "8e0b9e03054d"
branch_labels = None
depends_on = None

Base = sa.orm.declarative_base()

old_case_actions: list[str] = [
    "analyze",
    "hold",
    "running",
]

new_case_actions: list[str] = old_case_actions.copy()
new_case_actions.append("top-up")
new_case_actions.sort()


class Case(Base):
    __tablename__ = "case"
    id = sa.Column(sa.types.Integer, primary_key=True)
    action = sa.Column(sa.types.Enum(*new_case_actions), nullable=True)


def upgrade():
    op.alter_column(
        table_name="case",
        column_name="action",
        existing_type=sa.Enum(*old_case_actions),
        type_=sa.Enum(*new_case_actions),
        nullable=True,
    )


def downgrade():
    # Remove incompatible entries
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    for case in session.query(Case).filter(Case.action == "top-up"):
        case.action = "running"

    session.commit()

    op.alter_column(
        table_name="case",
        column_name="action",
        existing_type=sa.Enum(*new_case_actions),
        type_=sa.Enum(*old_case_actions),
        nullable=True,
    )
