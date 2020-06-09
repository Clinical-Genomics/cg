"""Commands for compressing files, and cleaning uncompressed files"""
import logging

import click

from cg.apps import crunchy, hk, scoutapi
from cg.meta.compress import CompressAPI
from cg.store import Store

from .bam import bam_cmd, clean_bam
from .fastq import clean_fastq, fastq_cmd

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def compress(context):
    """Compress files"""
    context.obj["db"] = Store(context.obj.get("database"))

    hk_api = hk.HousekeeperAPI(context.obj)
    scout_api = scoutapi.ScoutAPI(context.obj)
    crunchy_api = crunchy.CrunchyAPI(context.obj)

    compress_api = CompressAPI(hk_api=hk_api, crunchy_api=crunchy_api, scout_api=scout_api)
    context.obj["compress"] = compress_api


compress.add_command(bam_cmd)
compress.add_command(fastq_cmd)


@compress.group()
def clean():
    """Clean uncompressed files"""


clean.add_command(clean_bam)
clean.add_command(clean_fastq)
