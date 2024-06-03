"""CLI for deleting records in statusDB """

import logging

import click

from cg.cli.delete.case import delete_case
from cg.cli.delete.cases import delete_cases
from cg.cli.delete.observations import (
    delete_available_observations,
    delete_observations,
)

LOG = logging.getLogger(__name__)


@click.group(context_settings=click_context_setting_max_content_width())
def delete():
    """delete database records in CG."""
    LOG.info("Running CG delete")


delete.add_command(delete_case)
delete.add_command(delete_cases)
delete.add_command(delete_observations)
delete.add_command(delete_available_observations)
