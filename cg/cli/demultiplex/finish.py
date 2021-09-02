"""Commands to finish up after a demultiplex run"""
import logging

import click

from cg.constants.demultiplexing import OPTION_BCL_CONVERTER
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(name="finish")
def finish_group():
    """Finish up after demultiplexing"""


@finish_group.command(name="all")
@OPTION_BCL_CONVERTER
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def finish_all_cmd(context: CGConfig, bcl_converter: str, dry_run: bool):
    """Command to post process all demultiplexed flowcells"""
    demux_post_processing_api = DemuxPostProcessingAPI(config=context)
    demux_post_processing_api.set_dry_run(dry_run=dry_run)
    demux_post_processing_api.finish_all_flowcells(bcl_converter=bcl_converter)


@finish_group.command(name="flowcell")
@click.argument("flowcell-name")
@OPTION_BCL_CONVERTER
@click.option("--dry-run", is_flag=True)
@click.option("--force", is_flag=True)
@click.pass_obj
def finish_flowcell(
    context: CGConfig, flowcell_name: str, bcl_converter: str, dry_run: bool, force: bool
):
    """Command to finish up a flowcell after demultiplexing

    flowcell-name is full flowcell name, e.g. '201203_A00689_0200_AHVKJCDRXX'
    """

    demux_post_processing_api = DemuxPostProcessingAPI(config=context)
    demux_post_processing_api.set_dry_run(dry_run)
    demux_post_processing_api.finish_flowcell(
        flowcell_name=flowcell_name, force=force, bcl_converter=bcl_converter
    )
