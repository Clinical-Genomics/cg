"""Sync cg and statusdb

Revision ID: 936887038ba8
Revises: 5cb3ce4c3e39
Create Date: 2023-09-12 09:26:50.748369

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "936887038ba8"
down_revision = "5cb3ce4c3e39"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "application",
        "prep_category",
        existing_type=mysql.ENUM("cov", "mic", "rml", "tgs", "wes", "wgs", "wts"),
        nullable=False,
    )
    op.alter_column(
        "family",
        "priority",
        existing_type=mysql.ENUM("research", "standard", "priority", "express", "clinical_trials"),
        nullable=False,
    )
    op.alter_column("invoice", "customer_id", existing_type=mysql.INTEGER(), nullable=False)
    op.alter_column("invoice", "comment", existing_type=mysql.TEXT(), nullable=True)

    op.drop_index("customer_invoice_pk", table_name="invoice")
    op.create_foreign_key("invoice_customer_ibfk_1", "invoice", "customer", ["customer_id"], ["id"])
    op.alter_column(
        table_name="pool",
        column_name="invoice_id",
        existing_type=mysql.INTEGER(),
        type_=mysql.INTEGER(unsigned=True),
    )
    op.create_foreign_key("pool_invoice_ibfk_1", "pool", "invoice", ["invoice_id"], ["id"])
    op.alter_column(
        "sample",
        "priority",
        existing_type=mysql.ENUM("research", "standard", "priority", "express", "clinical_trials"),
        nullable=False,
    )
    op.alter_column(
        table_name="sample",
        column_name="invoice_id",
        existing_type=mysql.INTEGER(),
        type_=mysql.INTEGER(unsigned=True),
    )
    op.create_foreign_key("sample_invoice_ibfk_1", "sample", "invoice", ["invoice_id"], ["id"])
    op.drop_column("sample", "beaconized_at")
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "flow_cell_name",
        existing_type=mysql.VARCHAR(charset="latin1", collation="latin1_swedish_ci", length=32),
        nullable=False,
    )
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_internal_id",
        existing_type=mysql.VARCHAR(charset="latin1", collation="latin1_swedish_ci", length=32),
        nullable=False,
    )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_internal_id",
        existing_type=mysql.VARCHAR(charset="latin1", collation="latin1_swedish_ci", length=32),
        nullable=True,
    )
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "flow_cell_name",
        existing_type=mysql.VARCHAR(charset="latin1", collation="latin1_swedish_ci", length=32),
        nullable=True,
    )
    op.add_column("sample", sa.Column("beaconized_at", mysql.TEXT(), nullable=True))
    op.drop_constraint(
        constraint_name="sample_invoice_ibfk_1", table_name="sample", type_="foreignkey"
    )
    op.alter_column(
        "sample",
        "priority",
        existing_type=mysql.ENUM("research", "standard", "priority", "express", "clinical_trials"),
        nullable=True,
    )
    op.drop_constraint(constraint_name="pool_invoice_ibfk_1", table_name="pool", type_="foreignkey")
    op.alter_column(
        table_name="pool",
        column_name="invoice_id",
        existing_type=mysql.INTEGER(unsigned=True),
        type_=mysql.INTEGER(),
    )
    op.drop_constraint(
        constraint_name="invoice_customer_ibfk_1", table_name="invoice", type_="foreignkey"
    )
    op.create_index("customer_invoice_pk", "invoice", ["customer_id"], unique=False)
    op.alter_column("invoice", "comment", existing_type=mysql.TEXT(), nullable=False)
    op.alter_column("invoice", "customer_id", existing_type=mysql.INTEGER(), nullable=True)
    op.alter_column(
        "family",
        "priority",
        existing_type=mysql.ENUM("research", "standard", "priority", "express", "clinical_trials"),
        nullable=True,
    )
    op.alter_column(
        "application",
        "prep_category",
        existing_type=mysql.ENUM("cov", "mic", "rml", "tgs", "wes", "wgs", "wts"),
        nullable=True,
    )
