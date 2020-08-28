"""Commands for compressing files, and cleaning uncompressed files"""
import logging

import click

from cg.apps import crunchy, hk
from cg.meta.compress import CompressAPI
from cg.store import Store

from .fastq import clean_fastq, decompress_spring, fastq_cmd, fix_spring

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def compress(context):
    """Compress files"""
    context.obj["db"] = Store(context.obj.get("database"))

    hk_api = hk.HousekeeperAPI(context.obj)
    crunchy_api = crunchy.CrunchyAPI(context.obj)

    compress_api = CompressAPI(hk_api=hk_api, crunchy_api=crunchy_api)
    context.obj["compress"] = compress_api


compress.add_command(fastq_cmd)


@compress.group()
def clean():
    """Clean uncompressed files"""


clean.add_command(clean_fastq)
clean.add_command(fix_spring)


@compress.group()
@click.pass_context
def decompress(context):
    """Decompress files"""
    context.obj["db"] = Store(context.obj.get("database"))

    hk_api = hk.HousekeeperAPI(context.obj)
    crunchy_api = crunchy.CrunchyAPI(context.obj)

    compress_api = CompressAPI(hk_api=hk_api, crunchy_api=crunchy_api)
    context.obj["compress"] = compress_api


decompress.add_command(decompress_spring)
