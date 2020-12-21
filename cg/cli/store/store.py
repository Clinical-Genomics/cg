"""Code for store part of CLI"""

import logging

import click

from cg.apps.crunchy.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.compress.compress import CompressAPI
from cg.store import Store

from .fastq import store_case, store_flowcell, store_sample, store_ticket

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Command for storing files"""
    LOG.info("Running CG store command")
    housekeeper_api = HousekeeperAPI(context.obj)
    crunchy_api = CrunchyAPI(context.obj)

    compress_api = CompressAPI(hk_api=housekeeper_api, crunchy_api=crunchy_api)
    context.obj["compress_api"] = compress_api
    context.obj["status_db"] = Store(context.obj.get("database"))


store.add_command(store_sample)
store.add_command(store_case)
store.add_command(store_ticket)
store.add_command(store_flowcell)
