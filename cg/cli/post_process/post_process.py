"""CLI commands to post-process a sequencing run."""

import logging

import click

from cg.cli.post_process.utils import get_post_processing_service_from_run_name
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants.cli_options import DRY_RUN
from cg.models.cg_config import CGConfig, PostProcessingServices
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
@click.pass_obj
def post_process_all_runs(context: CGConfig, dry_run: bool) -> None:
    """Post-process all runs from the instruments."""
    services: PostProcessingServices = context.post_processing_services
    are_all_services_successful: bool = True
    for service in [services.pacbio]:
        is_service_successful: bool = service.post_process_all(dry_run=dry_run)
        are_all_services_successful = are_all_services_successful and is_service_successful
    if not are_all_services_successful:
        raise click.Abort


post_process_group.add_command(post_process_run)
post_process_group.add_command(post_process_all_runs)
