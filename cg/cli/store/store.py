"""Code for store part of CLI"""

import logging

import click
from cg.apps.crunchy.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.compress.compress import CompressAPI
from cg.models.cg_config import CGConfig

from .fastq import store_case, store_flowcell, store_sample, store_ticket

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_obj
def store(context: CGConfig):
    """Command for storing files"""
    LOG.info("Running CG store command")
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    crunchy_api: CrunchyAPI = context.crunchy_api

    compress_api = CompressAPI(
        hk_api=housekeeper_api, crunchy_api=crunchy_api, demux_root=context.demultiplex.out_dir
    )
    context.meta_apis["compress_api"] = compress_api


store.add_command(store_sample)
store.add_command(store_case)
store.add_command(store_ticket)
store.add_command(store_flowcell)
