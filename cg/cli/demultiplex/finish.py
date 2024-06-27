"""Commands to finish up after a demultiplex run."""

import logging
from pathlib import Path

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants.cli_options import DRY_RUN, FORCE
from cg.models.cg_config import CGConfig
from cg.services.illumina_services.illumina_post_processing_service.illumina_post_processing_service import (
    IlluminaPostProcessingService,
)

LOG = logging.getLogger(__name__)


@click.group(name="finish", context_settings=CLICK_CONTEXT_SETTINGS)
def finish_group():
    """Finish up after demultiplexing."""


@finish_group.command(name="illumina-run")
@click.argument("demultiplexed-run-dir-name")
@DRY_RUN
@FORCE
@click.pass_obj
def post_process_illumina_run(
    context: CGConfig, demultiplexed_run_dir_name: str, force: bool, dry_run: bool
):
    """Command to post-process an illumina run after demultiplexing.

    flow-cell-name is full flow cell name, e.g. '230912_A00187_1009_AHK33MDRX3'.
    """
    post_processing_service = IlluminaPostProcessingService(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        dry_run=dry_run,
        force=force,
        demultiplexed_runs_dir=Path(context.run_instruments.illumina.demultiplexed_runs_dir),
    )
    post_processing_service.post_process_illumina_flow_cell(
        sequencing_run_name=demultiplexed_run_dir_name,
    )


@finish_group.command(name="all")
@click.pass_obj
@DRY_RUN
def post_process_all_illumina_runs(context: CGConfig, dry_run: bool):
    """Command to post process all demultiplexed Illumina runs."""

    post_processing_service = IlluminaPostProcessingService(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        dry_run=dry_run,
        force=False,
        demultiplexed_runs_dir=Path(context.run_instruments.illumina.demultiplexed_runs_dir),
    )
    is_error_raised: bool = post_processing_service.post_process_all_runs()
    if is_error_raised:
        raise click.Abort
