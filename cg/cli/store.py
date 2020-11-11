"""Code for store part of CLI"""

import logging

import click

from cg.apps.crunchy import CrunchyAPI
from cg.apps.hk import HousekeeperAPI
from cg.cli.compress.helpers import get_fastq_individuals, update_compress_api
from cg.exc import CaseNotFoundError
from cg.meta.compress import CompressAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Command for storing files"""
    housekeeper_api = HousekeeperAPI(context.obj)
    crunchy_api = CrunchyAPI(context.obj)

    compress_api = CompressAPI(hk_api=housekeeper_api, crunchy_api=crunchy_api)
    context.obj["compress_api"] = compress_api
    context.obj["status_db"] = Store(context.obj.get("database"))


@store.command("sample")
@click.argument("sample-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def store_sample(context, sample_id, dry_run):
    compress_api = context.obj["compress_api"]
    update_compress_api(compress_api, dry_run=dry_run)

    was_decompressed = compress_api.add_decompressed_fastq(sample_id)
    if was_decompressed is False:
        LOG.info(f"Skipping sample {sample_id}")
        return 0
    LOG.info(f"Stored fastq files for {sample_id}")
    return 1


@store.command("case")
@click.argument("case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def store_case(context, case_id, dry_run):
    """Decompress SPRING file, and include links to FASTQ files in housekeeper"""

    status_db = context.obj["status_db"]
    try:
        samples = get_fastq_individuals(status_db, case_id)
        stored_inds = 0
        for sample_id in samples:
            stored_count = context.invoke(store_sample, sample_id=sample_id, dry_run=dry_run)
            stored_inds += stored_count
    except CaseNotFoundError:
        return
    LOG.info(f"Stored fastq files for {stored_inds} samples")


@store.command("flowcell")
@click.argument("flowcell_id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def store_flowcell(context, flowcell_id, dry_run):
    """Decompress SPRING file, and include links to FASTQ files in housekeeper"""

    status_db = context.obj["status_db"]
    samples = status_db.get_samples_from_flowcell(flowcell_id=flowcell_id)
    stored_inds = 0
    for sample in samples:
        stored_count = context.invoke(store_sample, sample_id=sample.internal_id, dry_run=dry_run)
        stored_inds += stored_count
    LOG.info(f"Stored fastq files for {stored_inds} samples")


@store.command("ticket")
@click.argument("ticket_id", type=int)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def store_ticket(context, ticket_id, dry_run):
    """Decompress SPRING file, and include links to FASTQ files in housekeeper"""
    status_db = context.obj["status_db"]
    samples = status_db.get_samples_from_ticket(ticket_id=ticket_id)
    stored_inds = 0
    for sample in samples:
        stored_count = context.invoke(store_sample, sample_id=sample.internal_id, dry_run=dry_run)
        stored_inds += stored_count
    LOG.info(f"Stored fastq files for {stored_inds} samples")
