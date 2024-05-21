"""add_autoincrement_to_device_tables

Revision ID: 5fd7e8758fb1
Revises: fe23de4ed528
Create Date: 2024-05-21 09:25:47.751986

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "5fd7e8758fb1"
down_revision = "fe23de4ed528"
branch_labels = None
depends_on = None


def upgrade():
    # Modify illumina flow cell primary key
    op.drop_constraint(
        constraint_name="illumina_flow_cell_ibfk_1",
        table_name="illumina_flow_cell",
        type_="foreignkey",
    )
    op.drop_constraint(constraint_name="fk_device_id", table_name="run_metrics", type_="foreignkey")
    op.execute("ALTER TABLE run_device MODIFY COLUMN id INT NOT NULL AUTO_INCREMENT")
    # op.execute("ALTER TABLE illumina_flow_cell MODIFY COLUMN id INT NOT NULL AUTO_INCREMENT")
    op.create_foreign_key(
        constraint_name="fk_device_id",
        source_table="run_metrics",
        referent_table="run_device",
        local_cols=["device_id"],
        remote_cols=["id"],
    )
    op.create_foreign_key(
        constraint_name="illumina_flow_cell_ibfk_1",
        source_table="illumina_flow_cell",
        referent_table="run_device",
        local_cols=["id"],
        remote_cols=["id"],
    )
    # op.drop_constraint(
    #     "illumina_sample_run_metrics_ibfk_1", "illumina_sample_run_metrics", type_="foreignkey"
    # )
    # op.execute("ALTER TABLE run_metrics MODIFY COLUMN id INT NOT NULL AUTO_INCREMENT")
    # op.drop_constraint(
    #     "illumina_sequencing_metrics_ibfk_1", "illumina_sequencing_metrics", type_="foreignkey"
    # )
    # op.execute("ALTER TABLE sample_run_metrics MODIFY COLUMN id INT NOT NULL AUTO_INCREMENT")


def downgrade():
    op.drop_constraint(
        constraint_name="illumina_flow_cell_ibfk_1",
        table_name="illumina_flow_cell",
        type_="foreignkey",
    )
    op.drop_constraint(constraint_name="fk_device_id", table_name="run_metrics", type_="foreignkey")
    op.execute("ALTER TABLE run_device MODIFY COLUMN id INT NOT NULL")
    op.create_foreign_key(
        constraint_name="fk_device_id",
        source_table="run_metrics",
        referent_table="run_device",
        local_cols=["device_id"],
        remote_cols=["id"],
    )
    op.create_foreign_key(
        constraint_name="illumina_flow_cell_ibfk_1",
        source_table="illumina_flow_cell",
        referent_table="run_device",
        local_cols=["id"],
        remote_cols=["id"],
    )

    # op.execute("ALTER TABLE run_metrics MODIFY COLUMN id INT NOT NULL")
    # op.execute("ALTER TABLE sample_run_metrics MODIFY COLUMN id INT NOT NULL")
