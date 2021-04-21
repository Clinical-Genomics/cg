"""CLI for deleting records in statusDB """

import logging

import click
from cg.cli.delete.case import case
from cg.cli.delete.cases import cases
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
def delete():
    """delete database records in CG."""
    LOG.info("Running CG delete")


delete.add_command(case)
delete.add_command(cases)
