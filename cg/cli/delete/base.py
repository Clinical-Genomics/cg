"""CLI for deleting records in statusDB """

import logging
import click

from cg.cli.delete.case import case
from cg.cli.delete.cases import cases
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def delete(context):
    """delete database records in CG."""
    LOG.info("Running CG delete")
    context.obj["status_db"] = Store(context.obj["database"])


delete.add_command(case)
delete.add_command(cases)
