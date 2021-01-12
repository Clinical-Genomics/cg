"""Commands for compressing files, and cleaning uncompressed files"""
import logging

import click

from cg.apps.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.compress import CompressAPI
from cg.store import Store

from .fastq import (
    clean_fastq,
    decompress_case,
    decompress_flowcell,
    decompress_sample,
    decompress_ticket,
    fastq_cmd,
    fix_spring,
)

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def compress(context):
    """Compress files"""
    context.obj["status_db"] = Store(context.obj.get("database"))

    hk_api = HousekeeperAPI(context.obj)
    crunchy_api = CrunchyAPI(context.obj)

    compress_api = CompressAPI(hk_api=hk_api, crunchy_api=crunchy_api)
    context.obj["compress_api"] = compress_api


compress.add_command(fastq_cmd)


@compress.group()
def clean():
    """Clean uncompressed files"""


clean.add_command(clean_fastq)
clean.add_command(fix_spring)


@click.group()
@click.pass_context
def decompress(context):
    """Decompress files"""
    context.obj["status_db"] = Store(context.obj.get("database"))

    hk_api = HousekeeperAPI(context.obj)
    crunchy_api = CrunchyAPI(context.obj)

    compress_api = CompressAPI(hk_api=hk_api, crunchy_api=crunchy_api)
    context.obj["compress_api"] = compress_api
    LOG.info("Running decompress spring")


decompress.add_command(decompress_sample)
decompress.add_command(decompress_case)
decompress.add_command(decompress_ticket)
decompress.add_command(decompress_flowcell)
