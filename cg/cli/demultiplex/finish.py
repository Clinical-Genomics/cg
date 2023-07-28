"""Commands to finish up after a demultiplex run."""
import logging

import click

from cg.constants.constants import DRY_RUN
from cg.meta.demultiplex.demux_post_processing import (
    DemuxPostProcessingAPI,
)
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(name="finish")
def finish_group():
    """Finish up after demultiplexing."""


@finish_group.command(name="all")
@DRY_RUN
@click.pass_obj
def finish_all_cmd(context: CGConfig, dry_run: bool) -> None:
    """Command to post-process all demultiplexed flow cells."""
    demux_post_processing_api: DemuxPostProcessingAPI = DemuxPostProcessingAPI(config=context)
    demux_post_processing_api.set_dry_run(dry_run=dry_run)
    is_error_raised: bool = demux_post_processing_api.finish_all_flow_cells()
    if is_error_raised:
        raise click.Abort


@finish_group.command(name="flow-cell")
@click.argument("flow-cell-name")
@DRY_RUN
@click.option("--force", is_flag=True)
@click.pass_obj
def finish_flow_cell(context: CGConfig, flow_cell_name: str, dry_run: bool, force: bool) -> None:
    """Command to finish up a flow cell after demultiplexing.

    flow-cell-name is full flow cell name, e.g. '201203_A00689_0200_AHVKJCDRXX'.
    """
    demux_post_processing_api_temp: DemuxPostProcessingAPI = DemuxPostProcessingAPI(config=context)
    demux_post_processing_api_temp.set_dry_run(dry_run)
    demux_post_processing_api_temp.finish_flow_cell(flow_cell_directory_name=flow_cell_name)
