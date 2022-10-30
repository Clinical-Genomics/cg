"""Check for newly demultiplex runs."""
import logging

from typing import Generator, Any

import click

from cg.cli import transfer
from cg.constants.constants import DRY_RUN
from cg.constants.demultiplexing import BclConverter
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingHiseqXAPI
from cg.models.cg_config import CGConfig


@click.group(name="check")
def check_group():
    """Check for new demultiplexing."""


@click.command(name="check_new_demultiplex")
@DRY_RUN
@click.pass_obj
def check_new_demultiplex(context: CGConfig, dry_run: bool):
    """Command to check for new demultiplexed flow cells prior to Novaseq."""
    logging.debug("Checking for new Hiseq X demultiplexed flowcells")
    demux_post_processing_api = DemuxPostProcessingHiseqXAPI(config=context)
    demux_post_processing_api.set_dry_run(dry_run=dry_run)
    transfer_flow_cells: list[str] = demux_post_processing_api.finish_all_flowcells(
        bcl_converter=BclConverter.BCL2FASTQ.value
    )

    for flowcell in transfer_flow_cells:
        print(flowcell)
        #        context.invoke(flowcell, content=context.forward(transfer))
        pass


#        today: str = datetime.datetime.strptime(datetime.date, "%Y-%m-%d")
