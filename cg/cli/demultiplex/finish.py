"""Commands to finish up after a demultiplex run"""
import logging
from pathlib import Path

import click
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell
from tests.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI

LOG = logging.getLogger(__name__)


@click.group(name="finish")
def finish_group():
    pass


@finish_group.command(name="flowcell")
@click.argument("flowcell-directory", type=click.Path(file_okay=False, exists=True))
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def finish_flowcell(context: CGConfig, flowcell_directory: click.Path, dry_run: bool):
    """Command to finish up a flowcell after demultiplexing"""
    flowcell = Flowcell(Path(str(flowcell_directory)))
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    if not demultiplex_api.is_demultiplexing_completed(flowcell=flowcell):
        LOG.warning("Demultiplex is not ready!")
        raise click.Abort
    unaligned_dir: Path = demultiplex_api.unaligned_dir_path(flowcell=flowcell)
    demux_post_processing_api = DemuxPostProcessingAPI()
    demux_post_processing_api.rename_files(unaligned_dir=unaligned_dir, flowcell=flowcell)
