import logging
from pathlib import Path

import click
import click_pathlib
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def demultiplex(context):
    """Command group for the demultiplex commands"""
    demultiplex_api: DemultiplexingAPI = DemultiplexingAPI(config=context.obj)
    context.obj["demultiplex_api"] = demultiplex_api


@click.command(name="flowcell")
@click.option("--sample-sheet", type=click_pathlib.Path(exists=True), required=True)
@click.option("--flowcell-directory", type=click_pathlib.Path(exists=True), required=True)
@click.option("--out-directory", type=click_pathlib.Path(exists=True), required=True)
@click.pass_context
def demultiplex_flowcell(
    context,
    flowcell_directory: Path,
    out_directory: Path,
):
    """Demultiplex a flowcell on slurm using CG"""
    demultiplex_api: DemultiplexingAPI = context.obj["demultiplex_api"]
    LOG.info("Sending demultiplex job for flowcell %s", flowcell_directory.name)
    demultiplex_api.start_demultiplexing(
        flowcell=flowcell_directory,
        out_dir=out_directory,
    )


demultiplex.add_command(demultiplex_flowcell)
