"""Commands to finish up after a demultiplex run."""
import logging

import click
from cg.constants.constants import DRY_RUN
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER
from cg.meta.demultiplex.demux_post_processing import (
    DemuxPostProcessingAPI,
    DemuxPostProcessingHiseqXAPI,
    DemuxPostProcessingNovaseqAPI,
)
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(name="finish")
def finish_group():
    """Finish up after demultiplexing."""


@finish_group.command(name="all-old-flow")
@DRY_RUN
@click.pass_obj
def finish_all_cmd_old_flow(context: CGConfig, dry_run: bool) -> None:
    """Command to post-process all demultiplexed flow cells.
    The old flow uses the DemuxPostProcessingNovaseqAPI.
    """
    demux_post_processing_api: DemuxPostProcessingNovaseqAPI = DemuxPostProcessingNovaseqAPI(
        config=context
    )
    demux_post_processing_api.set_dry_run(dry_run=dry_run)
    demux_post_processing_api.finish_all_flow_cells()


@finish_group.command(name="flow-cell-old-flow")
@click.argument("flow-cell-name")
@OPTION_BCL_CONVERTER
@DRY_RUN
@click.option("--force", is_flag=True)
@click.pass_obj
def finish_flow_cell_old_flow(
    context: CGConfig, flow_cell_name: str, bcl_converter: str, dry_run: bool, force: bool
) -> None:
    """Command to finish up a flow cell after demultiplexing.
    flow-cell-name is full flow cell name, e.g. '201203_D00483_0200_AHVKJCDRXX'.
    The old flow uses the DemuxPostProcessingNovaseqAPI.
    """
    demux_post_processing_api: DemuxPostProcessingNovaseqAPI = DemuxPostProcessingNovaseqAPI(
        config=context
    )
    demux_post_processing_api.set_dry_run(dry_run)
    demux_post_processing_api.finish_flow_cell(
        flow_cell_name=flow_cell_name, force=force, bcl_converter=bcl_converter
    )


@finish_group.command(name="flow-cell")
@click.argument("flow-cell-directory-name")
@OPTION_BCL_CONVERTER
@click.option("--force", is_flag=True)
@click.pass_obj
def finish_flow_cell(
    context: CGConfig, flow_cell_directory_name: str, bcl_converter: str, force: bool
):
    """Command to finish up a flow cell after demultiplexing.

    flow-cell-name is full flow cell name, e.g. '201203_D00483_0200_AHVKJCDRXX'.
    """
    demux_post_processing_api: DemuxPostProcessingAPI = DemuxPostProcessingAPI(config=context)
    demux_post_processing_api.finish_flow_cell_temp(
        flow_cell_directory_name=flow_cell_directory_name, bcl_converter=bcl_converter, force=force
    )


@finish_group.command(name="all")
@click.pass_obj
@DRY_RUN
def finish_all_cmd(context: CGConfig, dry_run: bool):
    """Command to finish up all demultiplexed flow cells."""

    demux_post_processing_api_temp: DemuxPostProcessingAPI = DemuxPostProcessingAPI(config=context)
    demux_post_processing_api_temp.set_dry_run(dry_run=dry_run)
    is_error_raised: bool = demux_post_processing_api_temp.finish_all_flow_cells_temp()
    if is_error_raised:
        raise click.Abort


@finish_group.command(name="all-hiseq-x")
@DRY_RUN
@click.pass_obj
def finish_all_hiseq_x(context: CGConfig, dry_run: bool) -> None:
    """Command to post-process new demultiplexed Hiseq X flow cells."""
    logging.debug("Checking for new Hiseq X demultiplexed flow cells")
    demux_post_processing_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=context
    )
    demux_post_processing_api.set_dry_run(dry_run=dry_run)
    demux_post_processing_api.finish_all_flow_cells()
