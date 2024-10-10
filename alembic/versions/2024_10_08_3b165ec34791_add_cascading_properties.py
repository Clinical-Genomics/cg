"""Add cascading properties

Revision ID: 3b165ec34791
Revises: d6474325c722
Create Date: 2024-10-08 13:53:19.792628

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "3b165ec34791"
down_revision = "d6474325c722"
branch_labels = None
depends_on = None

illumina_flow_cell_fk_name = "illumina_flow_cell_ibfk_1"
pacbio_smrt_cell_fk_name = "pacbio_smrt_cell_ibfk_1"
instrument_run_fk_name = "fk_device_id"
illumina_sequencing_run_fk_name = "illumina_sequencing_run_ibfk_1"
pacbio_sequencing_run_fk_name = "pacbio_sequencing_run_ibfk_1"
sample_run_metrics_fk_name = "fk_run_metrics_id"
illumina_sample_sequencing_metrics_fk_name = "illumina_sample_sequencing_metrics_ibfk_1"
pacbio_sample_run_metrics_fk_name = "pacbio_sample_run_metrics_ibfk_1"


def upgrade():
    op.drop_constraint(
        table_name="illumina_flow_cell",
        type_="foreignkey",
        constraint_name=illumina_flow_cell_fk_name,
    )
    op.create_foreign_key(
        constraint_name=illumina_flow_cell_fk_name,
        source_table="illumina_flow_cell",
        referent_table="run_device",
        ondelete="CASCADE",
        local_cols=["id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="pacbio_smrt_cell", type_="foreignkey", constraint_name=pacbio_smrt_cell_fk_name
    )
    op.create_foreign_key(
        constraint_name=pacbio_smrt_cell_fk_name,
        source_table="pacbio_smrt_cell",
        referent_table="run_device",
        ondelete="CASCADE",
        local_cols=["id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="instrument_run", type_="foreignkey", constraint_name=instrument_run_fk_name
    )
    op.create_foreign_key(
        constraint_name=instrument_run_fk_name,
        source_table="instrument_run",
        referent_table="run_device",
        ondelete="CASCADE",
        local_cols=["device_id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="illumina_sequencing_run",
        type_="foreignkey",
        constraint_name=illumina_sequencing_run_fk_name,
    )
    op.create_foreign_key(
        constraint_name=illumina_sequencing_run_fk_name,
        source_table="illumina_sequencing_run",
        referent_table="instrument_run",
        ondelete="CASCADE",
        local_cols=["id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="pacbio_sequencing_run",
        type_="foreignkey",
        constraint_name=pacbio_sequencing_run_fk_name,
    )
    op.create_foreign_key(
        constraint_name=pacbio_sequencing_run_fk_name,
        source_table="pacbio_sequencing_run",
        referent_table="instrument_run",
        ondelete="CASCADE",
        local_cols=["id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="sample_run_metrics",
        type_="foreignkey",
        constraint_name=sample_run_metrics_fk_name,
    )
    op.create_foreign_key(
        constraint_name=sample_run_metrics_fk_name,
        source_table="sample_run_metrics",
        referent_table="instrument_run",
        ondelete="CASCADE",
        local_cols=["instrument_run_id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="illumina_sample_sequencing_metrics",
        type_="foreignkey",
        constraint_name=illumina_sample_sequencing_metrics_fk_name,
    )
    op.create_foreign_key(
        constraint_name=illumina_sample_sequencing_metrics_fk_name,
        source_table="illumina_sample_sequencing_metrics",
        referent_table="sample_run_metrics",
        ondelete="CASCADE",
        local_cols=["id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="pacbio_sample_run_metrics",
        type_="foreignkey",
        constraint_name=pacbio_sample_run_metrics_fk_name,
    )
    op.create_foreign_key(
        constraint_name=pacbio_sample_run_metrics_fk_name,
        source_table="pacbio_sample_run_metrics",
        referent_table="sample_run_metrics",
        ondelete="CASCADE",
        local_cols=["id"],
        remote_cols=["id"],
    )


def downgrade():
    op.drop_constraint(
        table_name="pacbio_sample_run_metrics",
        type_="foreignkey",
        constraint_name=pacbio_sample_run_metrics_fk_name,
    )
    op.create_foreign_key(
        constraint_name=pacbio_sample_run_metrics_fk_name,
        source_table="pacbio_sample_run_metrics",
        referent_table="sample_run_metrics",
        local_cols=["id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="illumina_sample_sequencing_metrics",
        type_="foreignkey",
        constraint_name=illumina_sample_sequencing_metrics_fk_name,
    )
    op.create_foreign_key(
        constraint_name=illumina_sample_sequencing_metrics_fk_name,
        source_table="illumina_sample_sequencing_metrics",
        referent_table="sample_run_metrics",
        local_cols=["id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="sample_run_metrics",
        type_="foreignkey",
        constraint_name=sample_run_metrics_fk_name,
    )
    op.create_foreign_key(
        constraint_name=sample_run_metrics_fk_name,
        source_table="sample_run_metrics",
        referent_table="instrument_run",
        local_cols=["instrument_run_id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="pacbio_sequencing_run",
        type_="foreignkey",
        constraint_name=pacbio_sequencing_run_fk_name,
    )
    op.create_foreign_key(
        constraint_name=pacbio_sequencing_run_fk_name,
        source_table="pacbio_sequencing_run",
        referent_table="instrument_run",
        local_cols=["id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="illumina_sequencing_run",
        type_="foreignkey",
        constraint_name=illumina_sequencing_run_fk_name,
    )
    op.create_foreign_key(
        constraint_name=illumina_sequencing_run_fk_name,
        source_table="illumina_sequencing_run",
        referent_table="instrument_run",
        local_cols=["id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="instrument_run", type_="foreignkey", constraint_name=instrument_run_fk_name
    )
    op.create_foreign_key(
        constraint_name=instrument_run_fk_name,
        source_table="instrument_run",
        referent_table="run_device",
        local_cols=["device_id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="pacbio_smrt_cell", type_="foreignkey", constraint_name=pacbio_smrt_cell_fk_name
    )
    op.create_foreign_key(
        constraint_name=pacbio_smrt_cell_fk_name,
        source_table="pacbio_smrt_cell",
        referent_table="run_device",
        local_cols=["id"],
        remote_cols=["id"],
    )

    op.drop_constraint(
        table_name="illumina_flow_cell",
        type_="foreignkey",
        constraint_name=illumina_flow_cell_fk_name,
    )
    op.create_foreign_key(
        constraint_name=illumina_flow_cell_fk_name,
        source_table="illumina_flow_cell",
        referent_table="run_device",
        local_cols=["id"],
        remote_cols=["id"],
    )
