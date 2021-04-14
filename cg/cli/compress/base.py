"""Commands for compressing files, and cleaning uncompressed files"""
import logging

import click
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig

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
@click.pass_obj
def compress(context: CGConfig):
    """Compress files"""

    hk_api = context.housekeeper_api
    crunchy_api = context.crunchy_api

    compress_api = CompressAPI(hk_api=hk_api, crunchy_api=crunchy_api)
    context.meta_apis["compress_api"] = compress_api


compress.add_command(fastq_cmd)


@compress.group()
def clean():
    """Clean uncompressed files"""


clean.add_command(clean_fastq)
clean.add_command(fix_spring)


@click.group()
@click.pass_obj
def decompress(context: CGConfig):
    """Decompress files"""
    hk_api = context.housekeeper_api
    crunchy_api = context.crunchy_api

    compress_api = CompressAPI(hk_api=hk_api, crunchy_api=crunchy_api)
    context.meta_apis["compress_api"] = compress_api
    LOG.info("Running decompress spring")


decompress.add_command(decompress_sample)
decompress.add_command(decompress_case)
decompress.add_command(decompress_ticket)
decompress.add_command(decompress_flowcell)
