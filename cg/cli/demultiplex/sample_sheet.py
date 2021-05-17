import logging
from pathlib import Path
from typing import List

import click
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.sample_sheet.create import create_sample_sheet
from cg.apps.lims.samplesheet import LimsFlowcellSample, flowcell_samples
from cg.exc import FlowcellError
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell
from cgmodels.demultiplex.sample_sheet import get_sample_sheet_from_file
from pydantic import ValidationError

LOG = logging.getLogger(__name__)


@click.group(name="samplesheet")
def sample_sheet_commands():
    """Command group for the sample sheet commands"""
    pass


@sample_sheet_commands.command(name="validate")
@click.argument("sheet", type=click.Path(exists=True, dir_okay=False))
def validate_sample_sheet(sheet: click.Path):
    """Command to validate a sample sheet"""
    LOG.info("Validating sample sheet %s", sheet)
    sheet: Path = Path(str(sheet))
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
@click.argument("flowcell-name")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def create_sheet(context: CGConfig, flowcell_name: str, dry_run: bool):
    """Command to create a sample sheet

    Search the flowcell in the directory specified in config
    """
    LOG.info("Creating sample sheet for flowcell %s", flowcell_name)
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    flowcell_path: Path = demultiplex_api.run_dir / flowcell_name
    if not flowcell_path.exists():
        LOG.warning("Could not find flowcell %s", flowcell_path)
        raise click.Abort
    try:
        flowcell_object = Flowcell(flowcell_path=flowcell_path)
    except FlowcellError:
        raise click.Abort
    lims_samples: List[LimsFlowcellSample] = list(
        flowcell_samples(lims=context.lims_api, flowcell_id=flowcell_object.flowcell_id)
    )
    if not lims_samples:
        LOG.warning("Could not find any samples in lims for %s", flowcell_object.flowcell_id)
        raise click.Abort

    try:
        sample_sheet: str = create_sample_sheet(flowcell=flowcell_object, lims_samples=lims_samples)
    except (FileNotFoundError, FileExistsError):
        raise click.Abort

    if dry_run:
        click.echo(sample_sheet)
        return
    LOG.info("Writing sample sheet to %s", flowcell_object.sample_sheet_path.resolve())
    with open(flowcell_object.sample_sheet_path, "w") as outfile:
        outfile.write(sample_sheet)


@sample_sheet_commands.command(name="create-all")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def create_all_sheets(context: CGConfig, dry_run: bool):
    """Command to create sample sheets for all flowcells that lack a sample sheet

    Search flowcell directories for run parameters and create a sample sheets based on the information
    """
    demux_api: DemultiplexingAPI = context.demultiplex_api
    flowcells: Path = demux_api.run_dir
    for sub_dir in flowcells.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.info("Found directory %s", sub_dir)
        try:
            flowcell_object = Flowcell(flowcell_path=sub_dir)
        except FlowcellError:
            continue
        if flowcell_object.sample_sheet_exists():
            LOG.info("Sample sheet already exists")
            continue
        LOG.info("Creating sample sheet for flowcell %s", flowcell_object.flowcell_id)
        lims_samples: List[LimsFlowcellSample] = list(
            flowcell_samples(lims=context.lims_api, flowcell_id=flowcell_object.flowcell_id)
        )
        if not lims_samples:
            LOG.warning("Could not find any samples in lims for %s", flowcell_object.flowcell_id)
            continue

        try:
            sample_sheet: str = create_sample_sheet(
                flowcell=flowcell_object, lims_samples=lims_samples
            )
        except (FileNotFoundError, FileExistsError):
            continue

        if dry_run:
            click.echo(sample_sheet)
            return
        LOG.info("Writing sample sheet to %s", flowcell_object.sample_sheet_path.resolve())
        with open(flowcell_object.sample_sheet_path, "w") as outfile:
            outfile.write(sample_sheet)
