import logging
from pathlib import Path

import click
from pydantic import ValidationError

from cg.apps.demultiplex.sample_sheet.api import SampleSheetAPI
from cg.constants.constants import DRY_RUN
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER
from cg.exc import SampleSheetError
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(name="samplesheet")
def sample_sheet_commands():
    """Command group for the sample sheet commands."""


@sample_sheet_commands.command(name="validate")
@click.argument("sheet", type=click.Path(exists=True, dir_okay=False))
@click.pass_obj
def validate_sample_sheet(context: CGConfig, sheet: click.Path):
    """
    Validate a sample sheet. The bcl converter would be determined from the sample sheet content.
    """
    LOG.info(f"Validating {sheet} sample sheet")
    sample_sheet_api: SampleSheetAPI = context.sample_sheet_api
    try:
        sample_sheet_api.validate_sample_sheet(Path(sheet))
    except (SampleSheetError, ValidationError) as error:
        LOG.error("Sample sheet failed validation")
        raise click.Abort from error
    LOG.info("Sample sheet passed validation")


@sample_sheet_commands.command(name="create")
@click.argument("flow-cell-name")
@OPTION_BCL_CONVERTER
@DRY_RUN
@click.option("--force", is_flag=True, help="Skips the validation of the sample sheet")
@click.pass_obj
def create_sheet(
    context: CGConfig,
    flow_cell_name: str,
    bcl_converter: str | None,
    dry_run: bool,
    force: bool = False,
):
    """Create a sample sheet or hard-link it from Housekeeper in the flow cell directory.

    flow-cell-name is the flow cell run directory name, e.g. '201203_D00483_0200_AHVKJCDRXX'

    Search the flow cell in the directory specified in config.
    """
    LOG.info(f"Getting a valid sample sheet for flow cell {flow_cell_name}")
    sample_sheet_api: SampleSheetAPI = context.sample_sheet_api
    sample_sheet_api.set_dry_run(dry_run)
    sample_sheet_api.set_force(force)
    sample_sheet_api.get_or_create_sample_sheet(
        flow_cell_name=flow_cell_name, bcl_converter=bcl_converter
    )


@sample_sheet_commands.command(name="create-all")
@DRY_RUN
@click.pass_obj
def create_all_sheets(context: CGConfig, dry_run: bool):
    """Command to create sample sheets for all flow cells that lack a sample sheet.

    Search flow cell directories for run parameters and create a sample sheets based on the
    information.
    """
    sample_sheet_api: SampleSheetAPI = context.sample_sheet_api
    sample_sheet_api.set_dry_run(dry_run)
    sample_sheet_api.set_force(force=False)
    sample_sheet_api.get_or_create_all_sample_sheets()
