"""Commands to finish up after a demultiplex run."""

import logging

import click

from cg.constants.constants import DRY_RUN
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(name="finish")
def finish_group():
    """Finish up after demultiplexing."""


@finish_group.command(name="flow-cell")
@click.argument("flow-cell-directory-name")
@OPTION_BCL_CONVERTER
@click.option("--force", is_flag=True)
@DRY_RUN
@click.pass_obj
def finish_flow_cell(
    context: CGConfig, flow_cell_directory_name: str, bcl_converter: str, force: bool, dry_run: bool
):
    """Command to finish up a flow cell after demultiplexing.

    flow-cell-name is full flow cell name, e.g. '201203_D00483_0200_AHVKJCDRXX'.
    """
    demux_post_processing_api = DemuxPostProcessingAPI(config=context)
    demux_post_processing_api.set_dry_run(dry_run=dry_run)
    demux_post_processing_api.finish_flow_cell(
        flow_cell_directory_name=flow_cell_directory_name,
        bcl_converter=bcl_converter,
        force=force,
    )


@finish_group.command(name="all")
@click.pass_obj
@DRY_RUN
def finish_all_cmd(context: CGConfig, dry_run: bool):
    """Command to finish up all demultiplexed flow cells."""

    demux_post_processing_api = DemuxPostProcessingAPI(config=context)
    demux_post_processing_api.set_dry_run(dry_run=dry_run)
    is_error_raised: bool = demux_post_processing_api.finish_all_flow_cells()
    if is_error_raised:
        raise click.Abort
