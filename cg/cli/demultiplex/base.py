import logging
from pathlib import Path
from typing import Iterable

import click
import click_pathlib
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.flowcell import Flowcell
from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cg.apps.lims import LimsAPI
from cg.apps.lims.samplesheet import LimsFlowcellSample, flowcell_samples
from cg.models.demultiplex.run_parameters import RunParameters
from cgmodels.demultiplex.sample_sheet import SampleSheet, get_sample_sheet
from click import Context
from pydantic import ValidationError

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def demultiplex(context: Context):
    """Command group for the demultiplex commands"""
    context.obj["demultiplex_api"] = DemultiplexingAPI(config=context.obj)


@click.group(name="samplesheet")
@click.pass_context
def sample_sheet_commands(context: Context):
    """Command group for the sample sheet commands"""
    context.obj["lims_api"] = LimsAPI(config=context.obj)


@sample_sheet_commands.command(name="validate")
@click.argument("sheet", type=click_pathlib.Path(exists=True))
def validate_sample_sheet(sheet: Path):
    """Command to validate a sample sheet"""
    LOG.info("Validating sample sheet %s", sheet)
    if sheet.suffix != ".csv":
        LOG.warning("File %s seems to be in wrong format", sheet)
        LOG.warning("Suffix %s is not '.csv'", sheet.suffix)
        raise click.Abort
    try:
        get_sample_sheet(sheet, sheet_type="S4")
    except ValidationError as err:
        LOG.warning(err)
        raise click.Abort
    LOG.info("Sample sheet looks fine")


@sample_sheet_commands.command(name="create")
@click.argument("flowcell", type=click_pathlib.Path(exists=True))
@click.option("--dry-run", is_flag=True)
@click.pass_context
def create_sample_sheet(context: Context, flowcell: Path, dry_run: bool):
    """Command to create a sample sheet

    Search the flowcell directory for run parameters and create a sample sheet based on the information
    """
    LOG.info("Creating sample sheet for flowcell %s", flowcell)
    flowcell_object = Flowcell(flowcell_path=flowcell)
    if flowcell_object.sample_sheet_path.exists():
        LOG.warning("Sample sheet %s already exists!", flowcell_object.sample_sheet_path)
        raise click.Abort

    if not flowcell_object.run_parameters_path.exists():
        LOG.warning("Run parameters is missing, can not create sample sheet")
        raise click.Abort

    run_parameters_object: RunParameters = flowcell_object.run_parameters_object
    if run_parameters_object.flowcell_type != "novaseq":
        LOG.warning("Can only demultiplex novaseq with cg")
        raise click.Abort

    lims_samples: Iterable[LimsFlowcellSample] = flowcell_samples(
        lims=context.obj["lims_api"], flowcell_id=flowcell_object.flowcell_id
    )
    sample_sheet_creator = SampleSheetCreator(
        flowcell=flowcell_object.flowcell_id,
        lims_samples=list(lims_samples),
        run_parameters=flowcell_object.run_parameters_object,
    )
    sample_sheet: str = sample_sheet_creator.construct_sample_sheet()
    if dry_run:
        click.echo(sample_sheet)
        return
    LOG.info("Writing sample sheet to %s", flowcell_object.sample_sheet_path.resolve())
    with open(flowcell_object.sample_sheet_path, "w") as outfile:
        outfile.write(sample_sheet)


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
    LOG.info("Sending demultiplex job for flowcell %s", flowcell_directory.name)
    demultiplex_api: DemultiplexingAPI = context.obj["demultiplex_api"]
    flowcell_obj = Flowcell(flowcell_path=flowcell_directory)
    demultiplex_api.start_demultiplexing(
        flowcell=flowcell_obj,
        out_dir=out_directory,
    )


demultiplex.add_command(demultiplex_flowcell)
demultiplex.add_command(sample_sheet_commands)

if __name__ == "__main__":
    demultiplex()
