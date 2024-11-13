"""CLI for deleting records in statusDB """

import logging

import click

from cg.cli.delete.case import delete_case
from cg.cli.delete.cases import delete_cases
from cg.cli.delete.illumina_sequencing_run import delete_illumina_run
from cg.cli.delete.observations import (
    delete_available_observations,
    delete_observations,
)
from cg.cli.utils import CLICK_CONTEXT_SETTINGS

LOG = logging.getLogger(__name__)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def delete():
    """delete database records in CG."""
    LOG.info("Running CG delete")


delete.add_command(delete_case)
delete.add_command(delete_cases)
delete.add_command(delete_observations)
delete.add_command(delete_available_observations)
delete.add_command(delete_illumina_run)
