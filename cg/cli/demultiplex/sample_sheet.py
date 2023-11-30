import logging
import os
from pathlib import Path

import click
from pydantic import ValidationError

from cg.apps.demultiplex.sample_sheet.create import create_sample_sheet
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import get_sample_sheet_from_file
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims.sample_sheet import get_flow_cell_samples
from cg.constants.constants import DRY_RUN, FileFormat
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER
from cg.exc import FlowCellError, HousekeeperFileMissingError, SampleSheetError
from cg.io.controller import WriteFile, WriteStream
from cg.meta.demultiplex.housekeeper_storage_functions import add_sample_sheet_path_to_housekeeper
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData

LOG = logging.getLogger(__name__)


@click.group(name="samplesheet")
def sample_sheet_commands():
    """Command group for the sample sheet commands."""


@sample_sheet_commands.command(name="validate")
@click.argument("sheet", type=click.Path(exists=True, dir_okay=False))
def validate_sample_sheet(sheet: click.Path):
    """Validate a sample sheet."""
    LOG.info(f"Validating {sheet} sample sheet")
    try:
        get_sample_sheet_from_file(Path(sheet))
    except ValidationError as error:
        LOG.warning(error)
        raise click.Abort from error
    LOG.info("Sample sheet passed validation")


@sample_sheet_commands.command(name="create")
@click.argument("flow-cell-name")
@OPTION_BCL_CONVERTER
@DRY_RUN
@click.option("--force", is_flag=True, help="Skips the validation of the sample sheet")
@click.pass_obj
def create_sheet(
    context: CGConfig, flow_cell_name: str, bcl_converter: str, dry_run: bool, force: bool = False
):
    """Create a sample sheet or hard-link it from Housekeeper in the flow cell directory.

    flow-cell-name is the flow cell run directory name, e.g. '201203_D00483_0200_AHVKJCDRXX'

    Search the flow cell in the directory specified in config.
    """
    LOG.info(f"Creating sample sheet for flow cell {flow_cell_name}")
    hk_api: HousekeeperAPI = context.housekeeper_api
    flow_cell_path: Path = Path(context.flow_cells_dir, flow_cell_name)
    if not flow_cell_path.exists():
        LOG.warning(f"Could not find flow cell {flow_cell_path}")
        raise click.Abort
    try:
        flow_cell = FlowCellDirectoryData(
            flow_cell_path=flow_cell_path, bcl_converter=bcl_converter
        )
    except FlowCellError as error:
        raise click.Abort from error
    flow_cell_id: str = flow_cell.id

    try:
        sample_sheet_path: Path = hk_api.get_sample_sheet_path(flow_cell_id)
    except HousekeeperFileMissingError:
        sample_sheet_path = None

    if flow_cell.sample_sheet_exists():
        LOG.info("Sample sheet already exists in flow cell directory")
        if not dry_run:
            add_sample_sheet_path_to_housekeeper(
                flow_cell_directory=flow_cell_path, flow_cell_name=flow_cell_id, hk_api=hk_api
            )
        return
    elif sample_sheet_path:
        LOG.debug(
            "Sample sheet already exists in Housekeeper. Hard-linking it to flow cell directory"
        )
        if not dry_run:
            os.link(src=sample_sheet_path, dst=flow_cell.sample_sheet_path)
        return
    lims_samples: list[FlowCellSample] = list(
        get_flow_cell_samples(
            lims=context.lims_api,
            flow_cell_id=flow_cell_id,
            flow_cell_sample_type=flow_cell.sample_type,
        )
    )
    if not lims_samples:
        LOG.warning(f"Could not find any samples in LIMS for {flow_cell_id}")
        raise click.Abort
    try:
        sample_sheet_content: list[list[str]] = create_sample_sheet(
            flow_cell=flow_cell,
            lims_samples=lims_samples,
            force=force,
        )
    except (FileNotFoundError, FileExistsError, FlowCellError) as error:
        raise click.Abort from error

    if dry_run:
        click.echo(
            WriteStream.write_stream_from_content(
                file_format=FileFormat.CSV, content=sample_sheet_content
            )
        )
        return
    LOG.info(f"Writing sample sheet to {flow_cell.sample_sheet_path.resolve()}")
    WriteFile.write_file_from_content(
        content=sample_sheet_content,
        file_format=FileFormat.CSV,
        file_path=flow_cell.sample_sheet_path,
    )
    LOG.info("Adding sample sheet to Housekeeper")
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=flow_cell_path, flow_cell_name=flow_cell_id, hk_api=hk_api
    )


@sample_sheet_commands.command(name="create-all")
@DRY_RUN
@click.pass_obj
def create_all_sheets(context: CGConfig, dry_run: bool):
    """Command to create sample sheets for all flow cells that lack a sample sheet.

    Search flow cell directories for run parameters and create a sample sheets based on the
    information.
    """
    hk_api: HousekeeperAPI = context.housekeeper_api
    flow_cell_runs_dir: Path = Path(context.flow_cells_dir)
    for sub_dir in flow_cell_runs_dir.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.debug(f"Found directory {sub_dir}")
        try:
            flow_cell = FlowCellDirectoryData(flow_cell_path=sub_dir)
        except FlowCellError:
            continue
        flow_cell_id: str = flow_cell.id

        try:
            sample_sheet_path: Path | None = hk_api.get_sample_sheet_path(flow_cell_id)
        except HousekeeperFileMissingError:
            sample_sheet_path = None

        if flow_cell.sample_sheet_exists():
            LOG.debug("Sample sheet already exists in flow cell directory")
            if not dry_run:
                add_sample_sheet_path_to_housekeeper(
                    flow_cell_directory=sub_dir, flow_cell_name=flow_cell_id, hk_api=hk_api
                )
            continue
        elif sample_sheet_path:
            LOG.debug(
                "Sample sheet already exists in Housekeeper. Copying it to flow cell directory"
            )
            if not dry_run:
                os.link(src=sample_sheet_path, dst=flow_cell.sample_sheet_path)
            continue
        LOG.info(f"Creating sample sheet for flow cell {flow_cell.id}")
        lims_samples: list[FlowCellSample] = list(
            get_flow_cell_samples(
                lims=context.lims_api,
                flow_cell_id=flow_cell_id,
                flow_cell_sample_type=flow_cell.sample_type,
            )
        )
        if not lims_samples:
            LOG.warning(f"Could not find any samples in LIMS for {flow_cell_id}")
            continue

        try:
            sample_sheet_content: list[list[str]] = create_sample_sheet(
                flow_cell=flow_cell,
                lims_samples=lims_samples,
            )
        except (
            FileNotFoundError,
            FileExistsError,
            ValidationError,
            FlowCellError,
            SampleSheetError,
        ) as exc:
            LOG.warning(f"Sample sheet generation failed for flow cell {flow_cell_id} due to {exc}")
            continue

        if dry_run:
            click.echo(
                WriteStream.write_stream_from_content(
                    file_format=FileFormat.CSV, content=sample_sheet_content
                )
            )
            continue
        LOG.info(f"Writing sample sheet to {flow_cell.sample_sheet_path.resolve()}")
        WriteFile.write_file_from_content(
            content=sample_sheet_content,
            file_format=FileFormat.CSV,
            file_path=flow_cell.sample_sheet_path,
        )
        LOG.info("Adding sample sheet to Housekeeper")
        add_sample_sheet_path_to_housekeeper(
            flow_cell_directory=sub_dir, flow_cell_name=flow_cell_id, hk_api=hk_api
        )
