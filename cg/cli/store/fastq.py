import logging

import click

from cg.cli.compress.helpers import get_fastq_individuals, update_compress_api
from cg.exc import CaseNotFoundError

LOG = logging.getLogger(__name__)


@click.command("sample")
@click.argument("sample-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def store_sample(context, sample_id, dry_run):
    """Include links to decompressed FASTQ files belonging to this sample in housekeeper"""
    compress_api = context.obj["compress_api"]
    update_compress_api(compress_api, dry_run=dry_run)

    was_decompressed = compress_api.add_decompressed_fastq(sample_id)
    if was_decompressed is False:
        LOG.info(f"Skipping sample {sample_id}")
        return 0
    LOG.info(f"Stored fastq files for {sample_id}")
    return 1


@click.command("case")
@click.argument("case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def store_case(context, case_id, dry_run):
    """Include links to decompressed FASTQ files belonging to this case in housekeeper"""

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


@click.command("flowcell")
@click.argument("flowcell_id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def store_flowcell(context, flowcell_id, dry_run):
    """Include links to decompressed FASTQ files belonging to this flowcell in housekeeper"""

    status_db = context.obj["status_db"]
    samples = status_db.get_samples_from_flowcell(flowcell_id=flowcell_id)
    stored_inds = 0
    for sample in samples:
        stored_count = context.invoke(store_sample, sample_id=sample.internal_id, dry_run=dry_run)
        stored_inds += stored_count
    LOG.info(f"Stored fastq files for {stored_inds} samples")


@click.command("ticket")
@click.argument("ticket_id", type=int)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def store_ticket(context, ticket_id, dry_run):
    """Include links to decompressed FASTQ files belonging to this ticket in housekeeper"""
    status_db = context.obj["status_db"]
    samples = status_db.get_samples_from_ticket(ticket_id=ticket_id)
    stored_inds = 0
    for sample in samples:
        stored_count = context.invoke(store_sample, sample_id=sample.internal_id, dry_run=dry_run)
        stored_inds += stored_count
    LOG.info(f"Stored fastq files for {stored_inds} samples")
