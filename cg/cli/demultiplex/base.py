import logging
from pathlib import Path
from typing import Iterable, Optional

import click
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.flowcell import Flowcell
from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cg.apps.lims import LimsAPI
from cg.apps.lims.samplesheet import LimsFlowcellSample, flowcell_samples
from cg.models.demultiplex.run_parameters import RunParameters
from cgmodels.demultiplex.sample_sheet import get_sample_sheet_from_file
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
@click.argument("sheet", type=click.Path(exists=True, dir_okay=False))
def validate_sample_sheet(sheet: click.Path):
    """Command to validate a sample sheet"""
    LOG.info("Validating sample sheet %s", sheet)
    sheet: Path = Path(sheet)
    if sheet.suffix != ".csv":
        LOG.warning("File %s seems to be in wrong format", sheet)
        LOG.warning("Suffix %s is not '.csv'", sheet.suffix)
        raise click.Abort
    try:
        get_sample_sheet_from_file(infile=sheet, sheet_type="S4")
    except ValidationError as err:
        LOG.warning(err)
        raise click.Abort
    LOG.info("Sample sheet looks fine")


@sample_sheet_commands.command(name="create")
@click.argument("flowcell", type=click.Path(exists=True, file_okay=False))
@click.option("--dry-run", is_flag=True)
@click.pass_context
def create_sample_sheet(context: Context, flowcell: click.Path, dry_run: bool):
    """Command to create a sample sheet

    Search the flowcell directory for run parameters and create a sample sheet based on the information
    """
    LOG.info("Creating sample sheet for flowcell %s", flowcell)
    flowcell: Path = Path(flowcell)
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
    if not lims_samples:
        LOG.warning("Could not find any samples in lims for %s", flowcell_object.flowcell_id)
        raise click.Abort

    sample_sheet_creator = SampleSheetCreator(
        flowcell_id=flowcell_object.flowcell_id,
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
@click.argument("flowcell-directory")
@click.option("--out-directory")
@click.option("--dry-run", is_flag=True)
@click.pass_context
def demultiplex_flowcell(
    context,
    flowcell_directory: str,
    out_directory: Optional[str],
    dry_run: bool,
):
    """Demultiplex a flowcell on slurm using CG"""
    flowcell_directory: Path = Path(flowcell_directory)
    LOG.info("Sending demultiplex job for flowcell %s", flowcell_directory.name)
    demultiplex_api: DemultiplexingAPI = context.obj["demultiplex_api"]
    if out_directory:
        out_directory: Path = Path(out_directory)
        LOG.info("Set out_dir to %s", out_directory)
        demultiplex_api.out_dir = out_directory
    demultiplex_api.set_dry_run(dry_run=dry_run)
    flowcell_obj = Flowcell(flowcell_path=flowcell_directory)

    if not flowcell_obj.is_demultiplexing_possible() and not dry_run:
        raise click.Abort

    if not flowcell_obj.validate_sample_sheet():
        LOG.warning(
            "Malformed sample sheet. Run cg samplesheet validate %s", flowcell_obj.sample_sheet_path
        )
        if not dry_run:
            raise click.Abort
    demultiplex_api.start_demultiplexing(flowcell=flowcell_obj)


demultiplex.add_command(demultiplex_flowcell)
demultiplex.add_command(sample_sheet_commands)

if __name__ == "__main__":
    demultiplex()
