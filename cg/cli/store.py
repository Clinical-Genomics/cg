"""Code for store part of CLI"""

import logging

import click

from cg.apps import crunchy, hk
from cg.cli.compress.helpers import get_fastq_individuals, update_compress_api
from cg.exc import CaseNotFoundError
from cg.meta.compress import CompressAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Command for storing files"""
    hk_api = hk.HousekeeperAPI(context.obj)
    crunchy_api = crunchy.CrunchyAPI(context.obj)

    compress_api = CompressAPI(hk_api=hk_api, crunchy_api=crunchy_api)
    context.obj["compress"] = compress_api
    context.obj["db"] = Store(context.obj.get("database"))


@store.command("fastq")
@click.pass_context
@click.option("-d", "--dry-run", is_flag=True)
@click.argument("case-id")
def fastq_cmd(context, case_id, dry_run):
    """Store fastq files for a case in Housekeeper"""
    LOG.info("Running store fastq")

    compress_api = context.obj["compress"]
    cg_store = context.obj["db"]

    update_compress_api(compress_api, dry_run=dry_run)

    samples = get_fastq_individuals(cg_store, case_id)

    stored_individuals = 0
    try:
        for sample_id in samples:
            was_added = compress_api.add_decompressed_fastq(sample_id)
            if was_added is False:
                LOG.info("skipping individual %s", sample_id)
                continue
            stored_individuals += 1
    except CaseNotFoundError:
        return

    LOG.info("Stored fastq files for %s individuals", stored_individuals)
