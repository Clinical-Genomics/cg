import logging
from pathlib import Path

import click

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER
from cg.exc import FlowcellError
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell

LOG = logging.getLogger(__name__)


@click.command(name="all")
@OPTION_BCL_CONVERTER
@click.option("--flowcells-directory", type=click.Path(exists=True, file_okay=False))
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def demultiplex_all(
    context: CGConfig,
    bcl_converter: str,
    flowcells_directory: click.Path,
    dry_run: bool,
):
    """Demultiplex all flowcells that are ready under the flowcells_directory"""
    LOG.info("Running cg demultiplex all, using %s.", bcl_converter)
    if flowcells_directory:
        flowcells_directory: Path = Path(str(flowcells_directory))
    else:
        flowcells_directory: Path = Path(context.demultiplex.run_dir)
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    tb_api: TrailblazerAPI = context.trailblazer_api
    LOG.info("Search for flowcells ready to demultiplex in %s", flowcells_directory)
    for sub_dir in flowcells_directory.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.info("Found directory %s", sub_dir)
        try:
            flowcell_obj = Flowcell(flowcell_path=sub_dir, bcl_converter=bcl_converter)
        except FlowcellError:
            continue
        if not demultiplex_api.is_demultiplexing_possible(flowcell=flowcell_obj) and not dry_run:
            continue

        if not flowcell_obj.validate_sample_sheet():
            LOG.warning(
                "Malformed sample sheet. Run cg demultiplex samplesheet validate %s",
                flowcell_obj.sample_sheet_path,
            )
            if not dry_run:
                continue
        slurm_job_id: int = demultiplex_api.start_demultiplexing(flowcell=flowcell_obj)
        demultiplex_api.add_to_trailblazer(
            tb_api=tb_api, slurm_job_id=slurm_job_id, flowcell=flowcell_obj
        )


@click.command(name="flowcell")
@click.argument("flowcell-id")
@OPTION_BCL_CONVERTER
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def demultiplex_flowcell(
    context: CGConfig,
    flowcell_id: str,
    bcl_converter: str,
    dry_run: bool,
):
    """Demultiplex a flowcell on slurm using CG

    flowcell-name is the flowcell run directory name, e.g. '201203_A00689_0200_AHVKJCDRXX'
    """

    LOG.info("Running cg demultiplex flowcell, using %s.", bcl_converter)
    flowcell_directory: Path = Path(context.demultiplex.run_dir) / flowcell_id
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    try:
        flowcell_obj = Flowcell(flowcell_path=flowcell_directory, bcl_converter=bcl_converter)
    except FlowcellError:
        raise click.Abort

    if not demultiplex_api.is_demultiplexing_possible(flowcell=flowcell_obj) and not dry_run:
        LOG.warning("Can not start demultiplexing!")
        return

    if not flowcell_obj.validate_sample_sheet():
        LOG.warning(
            "Malformed sample sheet. Run cg demultiplex samplesheet validate %s",
            flowcell_obj.sample_sheet_path,
        )
        if not dry_run:
            raise click.Abort
    slurm_job_id: int = demultiplex_api.start_demultiplexing(flowcell=flowcell_obj)
    tb_api: TrailblazerAPI = context.trailblazer_api
    demultiplex_api.add_to_trailblazer(
        tb_api=tb_api, slurm_job_id=slurm_job_id, flowcell=flowcell_obj
    )
