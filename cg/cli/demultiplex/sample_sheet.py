import logging
from pathlib import Path

import click
from pydantic import ValidationError

from cg.apps.demultiplex.sample_sheet.api import IlluminaSampleSheetService
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants.cli_options import DRY_RUN, FORCE
from cg.exc import CgError
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(name="samplesheet", context_settings=CLICK_CONTEXT_SETTINGS)
def sample_sheet_commands():
    """Command group for the sample sheet commands."""


@sample_sheet_commands.command(name="validate")
@click.argument("sheet", type=click.Path(exists=True, dir_okay=False))
@click.pass_obj
def validate_sample_sheet(context: CGConfig, sheet: click.Path):
    """
    Validate a sample sheet.
    """
    LOG.info(f"Validating {sheet} sample sheet")
    sample_sheet_api: IlluminaSampleSheetService = context.sample_sheet_api
    try:
        sample_sheet_api.validate_sample_sheet(Path(sheet))
    except (CgError, ValidationError) as error:
        LOG.error("Sample sheet failed validation")
        raise click.Abort from error
    LOG.info("Sample sheet passed validation")


@sample_sheet_commands.command(name="translate")
@click.argument("flow-cell-name")
@DRY_RUN
@click.pass_obj
def translate_sample_sheet(context: CGConfig, flow_cell_name: str, dry_run: bool):
    """
    Translate a sample sheet from Bcl2Fastq to BclConvert format.
    'flow-cell-name' is the flow cell run directory name, e.g. '181005_D00410_0735_BHM2LNBCX2' with
    a Bcl2Fastq sample sheet in it.
    """
    LOG.info(f"Translating Bcl2Fastq sample sheet for flow cell {flow_cell_name}")
    sample_sheet_api: IlluminaSampleSheetService = context.sample_sheet_api
    sample_sheet_api.set_dry_run(dry_run)
    sample_sheet_api.translate_sample_sheet(flow_cell_name=flow_cell_name)


@sample_sheet_commands.command(name="create")
@click.argument("flow-cell-name")
@DRY_RUN
@FORCE
@click.pass_obj
def create_sheet(context: CGConfig, flow_cell_name: str, dry_run: bool, force: bool = False):
    """Create a sample sheet or hard-link it from Housekeeper in the flow cell directory.

    'flow-cell-name' is the flow cell run directory name, e.g. '181005_D00410_0735_BHM2LNBCX2'

    Search the flow cell in the directory specified in config.
    """
    LOG.info(f"Getting a valid sample sheet for flow cell {flow_cell_name}")
    sample_sheet_api: IlluminaSampleSheetService = context.sample_sheet_api
    sample_sheet_api.set_dry_run(dry_run)
    sample_sheet_api.set_force(force)
    sample_sheet_api.get_or_create_sample_sheet(flow_cell_name)


@sample_sheet_commands.command(name="create-all")
@DRY_RUN
@click.pass_obj
def create_all_sheets(context: CGConfig, dry_run: bool):
    """Command to create sample sheets for all flow cells that lack a sample sheet.

    Search flow cell directories for run parameters and create a sample sheets based on the
    information.
    """
    sample_sheet_api: IlluminaSampleSheetService = context.sample_sheet_api
    sample_sheet_api.set_dry_run(dry_run)
    sample_sheet_api.set_force(force=False)
    sample_sheet_api.get_or_create_all_sample_sheets()
