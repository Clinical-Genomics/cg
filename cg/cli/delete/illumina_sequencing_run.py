import click

from cg.constants.cli_options import DRY_RUN
from cg.services.illumina.post_processing.housekeeper_storage import (
    delete_sequencing_data_from_housekeeper,
)


@click.command("illumina-run")
@DRY_RUN
@click.option(
    "--flow-cell-id",
    "flow_cell_id",
    type=str,
    multiple=False,
    help="Give the flow cell id of the run to delete from statusdb and housekeeper.",
)
@click.pass_context
def delete_illumina_run(context: click.Context, dry_run: bool, flow_cell_id: str):
    """Delete an Illumina sequencing run"""
    if dry_run:
        click.echo("Dry run: Would delete the Illumina sequencing run")
        return
    delete_sequencing_data_from_housekeeper(
        flow_cell_id=flow_cell_id,
        hk_api=context.obj.housekeeper_api,
    )
    context.obj.store.delete_illumina_flow_cell(internal_id=flow_cell_id)
