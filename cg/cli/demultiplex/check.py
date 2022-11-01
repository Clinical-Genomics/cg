"""Check for newly demultiplex runs."""
import logging

from typing import Generator, Any, List

import click

from cg.cli import transfer
from cg.constants.constants import DRY_RUN
from cg.constants.demultiplexing import BclConverter
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingHiseqXAPI
from cg.models.cg_config import CGConfig
from cg.utils import Process


@click.group(name="check")
def check_group():
    """Check for new Hiseq X demultiplexing."""


@click.command(name="check_new_demultiplex")
@DRY_RUN
@click.pass_obj
def check_new_demultiplex(context: CGConfig, dry_run: bool):
    """Command to check for new demultiplexed Hiseq X flow cells."""
    logging.debug("Checking for new Hiseq X demultiplexed flow cells")
    demux_post_processing_api = DemuxPostProcessingHiseqXAPI(config=context)
    demux_post_processing_api.set_dry_run(dry_run=dry_run)
    transfer_flow_cells: list[str] = demux_post_processing_api.finish_all_flowcells(
        bcl_converter=BclConverter.BCL2FASTQ.value
    )

    for flowcell in filter(None, transfer_flow_cells):
        print(flowcell)
        cg_transfer_parameters: List[str] = ["--config", context.hasta_config, flowcell]
        cgstats_process: Process = Process(binary=context.binary_path)
        logging.info(f"{context.binary_path} --config {context.hasta_config} {flowcell}")
        cgstats_process.run_command(parameters=cg_transfer_parameters, dry_run=dry_run)


#        today: str = datetime.datetime.strptime(datetime.date, "%Y-%m-%d")
