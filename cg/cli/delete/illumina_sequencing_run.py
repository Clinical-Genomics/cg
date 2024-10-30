import click

from cg.constants.cli_options import DRY_RUN
from cg.services.illumina.post_processing.housekeeper_storage import (
    delete_sequencing_data_from_housekeeper,
)


@click.command("illumina-run")
@click.argument(
    "flow_cell_id",
    type=str,
)
@click.pass_context
def delete_illumina_run(context: click.Context, flow_cell_id: str):
    """
    Delete an Illumina sequencing run.

    Args:
        flow_cell_id (str): Give the flow cell id of the run to delete from statusdb and housekeeper.
    """
    delete_sequencing_data_from_housekeeper(
        flow_cell_id=flow_cell_id,
        hk_api=context.obj.housekeeper_api,
    )
    context.obj.status_db.delete_illumina_flow_cell(internal_id=flow_cell_id)
