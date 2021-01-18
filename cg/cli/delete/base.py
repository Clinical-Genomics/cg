"""CLI for deleting records in statusDB """

import logging
from pathlib import Path
from typing import List

import click

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.delete.case import case
from cg.store import Store
from cg.store.models import Family

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def delete(context):
    """delete files with CG."""
    LOG.info("Running CG delete")
    context.obj["status_db"] = Store(context.obj["database"])
    context.obj["housekeeper_api"] = HousekeeperAPI(context.obj)


delete.add_command(case)
