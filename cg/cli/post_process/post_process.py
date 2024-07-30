"""CLI commands to post-process a sequencing run."""

import logging

import click

from cg.cli.post_process.utils import get_post_processing_service_from_run_name
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.models.cg_config import CGConfig
from cg.services.post_processing.abstract_classes import PostProcessingService

LOG = logging.getLogger(__name__)


@click.group(name="post-process", context_settings=CLICK_CONTEXT_SETTINGS)
def post_process_group():
    """Finish up after demultiplexing."""


@post_process_group.command(name="run")
@click.argument("run-name")
@click.pass_obj
def post_process_sequencing_run(context: CGConfig, run_name: str):
    """Command to post-process a sequencing run from any device.

    run-name is the full name of the sequencing unit of run. For example:
        PacBio: 'r84202_20240522_133539/1_A01'
    """
    post_processing_service: PostProcessingService = get_post_processing_service_from_run_name(
        context=context, run_name=run_name
    )
    post_processing_service.post_process(
        run_name=run_name, sequencing_dir=context.run_instruments.pacbio.data_dir
    )
