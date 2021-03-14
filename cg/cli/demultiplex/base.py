import logging
from pathlib import Path

import click
import click_pathlib
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI

LOG = logging.getLogger(__name__)


@click.command(name="demultiplex")
@click.option("--basemask", type=click_pathlib.Path(exists=True), required=True)
@click.option("--sample-sheet", type=click_pathlib.Path(exists=True), required=True)
@click.option("--flowcell-directory", type=click_pathlib.Path(exists=True), required=True)
@click.option("--out-directory", type=click_pathlib.Path(exists=True), required=True)
@click.pass_context
def demultiplex_command(
    context,
    basemask: Path,
    sample_sheet: Path,
    flowcell_directory: Path,
    out_directory: Path,
):
    """Demultiplex a flowcell on slurm using CG"""
    demultiplex_api: DemultiplexingAPI = DemultiplexingAPI(config=context.obj)
    LOG.info("Sending demultiplex job for flowcell %s", flowcell_directory.name)
    demultiplex_api.start_demultiplexing(
        flowcell=flowcell_directory,
        out_dir=out_directory,
        basemask=basemask,
        sample_sheet=sample_sheet,
    )
