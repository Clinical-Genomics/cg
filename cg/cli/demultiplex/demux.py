import logging
from pathlib import Path
from typing import Optional

import click
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell

LOG = logging.getLogger(__name__)


@click.command(name="all")
@click.argument("flowcells-directory", type=click.Path(exists=True, file_okay=False))
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def demultiplex_all(
    context: CGConfig,
    flowcells_directory: click.Path,
    dry_run: bool,
):
    """Demultiplex all flowcells that are ready under the flowcells_directory"""
    flowcells_directory: Path = Path(str(flowcells_directory))
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    for sub_dir in flowcells_directory.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.info("Found directory %s", sub_dir)
        flowcell_obj = Flowcell(flowcell_path=sub_dir)
        if not demultiplex_api.is_demultiplexing_possible(flowcell=flowcell_obj) and not dry_run:
            continue

        if not flowcell_obj.validate_sample_sheet():
            LOG.warning(
                "Malformed sample sheet. Run cg samplesheet validate %s",
                flowcell_obj.sample_sheet_path,
            )
            if not dry_run:
                continue
        demultiplex_api.start_demultiplexing(flowcell=flowcell_obj)


@click.command(name="flowcell")
@click.argument("flowcell-directory", type=click.Path(file_okay=False, exists=True))
@click.option("--out-directory")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def demultiplex_flowcell(
    context: CGConfig,
    flowcell_directory: click.Path,
    out_directory: Optional[str],
    dry_run: bool,
):
    """Demultiplex a flowcell on slurm using CG"""
    LOG.info("Running cg demultiplex flowcell")
    flowcell_directory: Path = Path(str(flowcell_directory))
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    if out_directory:
        out_directory: Path = Path(out_directory)
        LOG.info("Set out_dir to %s", out_directory)
        demultiplex_api.out_dir = out_directory
    demultiplex_api.set_dry_run(dry_run=dry_run)
    flowcell_obj = Flowcell(flowcell_path=flowcell_directory)

    if not demultiplex_api.is_demultiplexing_possible(flowcell=flowcell_obj) and not dry_run:
        LOG.warning("Can not start demultiplexing!")
        return

    if not flowcell_obj.validate_sample_sheet():
        LOG.warning(
            "Malformed sample sheet. Run cg samplesheet validate %s", flowcell_obj.sample_sheet_path
        )
        if not dry_run:
            raise click.Abort
    demultiplex_api.start_demultiplexing(flowcell=flowcell_obj)
