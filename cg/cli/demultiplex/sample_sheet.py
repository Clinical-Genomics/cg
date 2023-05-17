import logging
from pathlib import Path
from typing import List, Union

import click
from pydantic import ValidationError

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.sample_sheet.create import create_sample_sheet
from cg.apps.demultiplex.sample_sheet.validate import get_sample_sheet_from_file
from cg.apps.lims.samplesheet import (
    LimsFlowcellSample,
    LimsFlowcellSampleBcl2Fastq,
    LimsFlowcellSampleDragen,
    flowcell_samples,
)
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER, FlowCellMode, FLOW_CELL_MODES
from cg.exc import FlowCellError
from cg.io.controller import WriteFile
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCell

LOG = logging.getLogger(__name__)


@click.group(name="samplesheet")
def sample_sheet_commands():
    """Command group for the sample sheet commands."""


@sample_sheet_commands.command(name="validate")
@click.argument("sheet", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--flow-cell-mode",
    default=FlowCellMode.NOVASEQ,
    show_default=True,
    type=click.Choice(FLOW_CELL_MODES),
    help="Instrument sample sheet flow cell mode",
)
@OPTION_BCL_CONVERTER
def validate_sample_sheet(
    bcl_converter: str,
    sheet: click.Path,
    flow_cell_mode: str,
):
    """Validate a sample sheet."""
    LOG.info(
        f"Validating sample sheet {sheet}",
    )
    sheet: Path = Path(str(sheet))
    try:
        get_sample_sheet_from_file(
            infile=sheet, flow_cell_mode=flow_cell_mode, bcl_converter=bcl_converter
        )
    except ValidationError as error:
        LOG.warning(error)
        raise click.Abort from error
    LOG.info("Sample sheet passed validation")


@sample_sheet_commands.command(name="create")
@click.argument("flow-cell-name")
@OPTION_BCL_CONVERTER
@click.option("--dry-run", is_flag=True)
@click.option("--force", is_flag=True, help="Skips the validation of the sample sheet")
@click.pass_obj
def create_sheet(
    context: CGConfig, flow_cell_name: str, bcl_converter: str, dry_run: bool, force: bool = False
):
    """Command to create a sample sheet.
    flow-cell-name is the flow cell run directory name, e.g. '201203_A00689_0200_AHVKJCDRXX'

    Search the flow cell in the directory specified in config.
    """

    LOG.info(f"Creating sample sheet for flowcell {flow_cell_name}")
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    flowcell_path: Path = Path(demultiplex_api.run_dir, flow_cell_name)
    if not flowcell_path.exists():
        LOG.warning(f"Could not find flow cell {flowcell_path}")
        raise click.Abort
    try:
        flow_cell = FlowCell(flow_cell_path=flowcell_path, bcl_converter=bcl_converter)
    except FlowCellError as error:
        raise click.Abort from error
    lims_samples: List[Union[LimsFlowcellSampleBcl2Fastq, LimsFlowcellSampleDragen]] = list(
        flowcell_samples(
            lims=context.lims_api,
            flowcell_id=flow_cell.id,
            bcl_converter=bcl_converter,
        )
    )
    if not lims_samples:
        LOG.warning(f"Could not find any samples in lims for {flow_cell.id}")
        raise click.Abort
    try:
        sample_sheet_content: List[List[str]] = create_sample_sheet(
            bcl_converter=bcl_converter, flow_cell=flow_cell, lims_samples=lims_samples, force=force
        )
    except (FileNotFoundError, FileExistsError) as error:
        raise click.Abort from error

    if dry_run:
        click.echo(sample_sheet_content)
        return
    LOG.info(f"Writing sample sheet to {flow_cell.sample_sheet_path.resolve()}")
    WriteFile.write_file_from_content(
        content=sample_sheet_content,
        file_format=FileFormat.CSV,
        file_path=flow_cell.sample_sheet_path,
    )


@sample_sheet_commands.command(name="create-all")
@OPTION_BCL_CONVERTER
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def create_all_sheets(context: CGConfig, bcl_converter: str, dry_run: bool):
    """Command to create sample sheets for all flow cells that lack a sample sheet.

    Search flow cell directories for run parameters and create a sample sheets based on the
    information.
    """
    demux_api: DemultiplexingAPI = context.demultiplex_api
    flow_cells: Path = demux_api.run_dir
    for sub_dir in flow_cells.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.info(f"Found directory {sub_dir}")
        try:
            flow_cell = FlowCell(flow_cell_path=sub_dir, bcl_converter=bcl_converter)
        except FlowCellError:
            continue
        if flow_cell.sample_sheet_exists():
            LOG.info("Sample sheet already exists")
            continue
        LOG.info(f"Creating sample sheet for flowcell {flow_cell.id}")
        lims_samples: List[LimsFlowcellSample] = list(
            flowcell_samples(
                lims=context.lims_api,
                flowcell_id=flow_cell.id,
                bcl_converter=bcl_converter,
            )
        )
        if not lims_samples:
            LOG.warning(f"Could not find any samples in lims for {flow_cell.id}")
            continue

        try:
            sample_sheet_content: List[List[str]] = create_sample_sheet(
                flow_cell=flow_cell, lims_samples=lims_samples, bcl_converter=bcl_converter
            )
        except (FileNotFoundError, FileExistsError, ValidationError):
            continue

        if dry_run:
            click.echo(sample_sheet_content)
            return
        LOG.info(f"Writing sample sheet to {flow_cell.sample_sheet_path.resolve()}")
        WriteFile.write_file_from_content(
            content=sample_sheet_content,
            file_format=FileFormat.CSV,
            file_path=flow_cell.sample_sheet_path,
        )
