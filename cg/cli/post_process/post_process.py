"""CLI commands to post-process a sequencing run."""

import logging

import click

from cg.cli.post_process.utils import (
    UnprocessedRunInfo,
    get_post_processing_service_from_run_name,
    get_unprocessed_runs_info,
)
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants.cli_options import DRY_RUN
from cg.models.cg_config import CGConfig
from cg.services.run_devices.abstract_classes import PostProcessingService

LOG = logging.getLogger(__name__)


@click.group(name="post-process", context_settings=CLICK_CONTEXT_SETTINGS)
def post_process_group():
    """Post-process sequencing runs from the sequencing instruments."""
    LOG.info("Running cg post-processing.")


@post_process_group.command(name="run")
@DRY_RUN
@click.argument("run-name")
@click.pass_obj
def post_process_run(context: CGConfig, run_name: str, dry_run: bool) -> None:
    """Post-process a sequencing run from the PacBio instrument.

    run-name is the full name of the sequencing unit of run. For example:
        PacBio: 'r84202_20240522_133539/1_A01'
    """
    post_processing_service: PostProcessingService = get_post_processing_service_from_run_name(
        context=context, run_name=run_name
    )
    post_processing_service.post_process(run_name=run_name, dry_run=dry_run)


@post_process_group.command(name="all")
@DRY_RUN
@click.option(
    "--instrument",
    type=click.Choice(["pacbio", "all"]),
    default="all",
    show_default=True,
    help="The instrument for which the runs will be post-processed. Choose 'all' to post-process runs from all instruments.",
    required=False,
)
@click.pass_obj
def post_process_all_runs(context: CGConfig, instrument: str, dry_run: bool) -> None:
    """Post-process all available runs."""
    exit_success: bool = True
    unprocessed_runs: list[UnprocessedRunInfo] = get_unprocessed_runs_info(
        context=context, instrument=instrument
    )
    for run in unprocessed_runs:
        try:
            run.post_processing_service.post_process(run_name=run.name, dry_run=dry_run)
        except Exception as error:
            LOG.error(f"Could not post-process {run.instrument} run {run.name}: {error}")
            exit_success = False
    if not exit_success:
        raise click.Abort


post_process_group.add_command(post_process_run)
post_process_group.add_command(post_process_all_runs)
