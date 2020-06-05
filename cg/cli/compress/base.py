"""Commands for compressing files, and cleaning uncompressed files"""
import logging

import click

from cg.apps import crunchy, hk, scoutapi
from cg.meta.compress import CompressAPI
from cg.store import Store

from .bam import bam as bam_command
from .fastq import fastq_cmd

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


compress.add_command(bam_command)
compress.add_command(fastq_cmd)


@compress.group()
def clean():
    """Clean uncompressed files"""


@clean.command("bam")
@click.option("-c", "--case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def clean_bam(context, case_id, dry_run):
    """Remove compressed BAM files, and update links in scout and housekeeper
       to CRAM files"""
    compress_api = context.obj["compress"]
    store = context.obj["db"]
    cases = store.families()
    if case_id:
        cases = [context.obj["db"].family(case_id)]

    for case in cases:
        case_id = case.internal_id
        compress_api.clean_bams(case_id, dry_run=dry_run)
