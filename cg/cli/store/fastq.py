import logging
from typing import Iterable, List

import click
from cg.cli.compress.helpers import get_fastq_individuals, update_compress_api
from cg.exc import CaseNotFoundError
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models

LOG = logging.getLogger(__name__)


@click.command("sample")
@click.argument("sample-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_obj
def store_sample(context: CGConfig, sample_id: str, dry_run: bool):
    """Include links to decompressed FASTQ files belonging to this sample in housekeeper"""
    compress_api: CompressAPI = context.meta_apis["compress_api"]
    update_compress_api(compress_api, dry_run=dry_run)

    was_decompressed: bool = compress_api.add_decompressed_fastq(sample_id)
    if not was_decompressed:
        LOG.info(f"Skipping sample {sample_id}")
        return 0
    LOG.info(f"Stored fastq files for {sample_id}")
    return 1


@click.command("case")
@click.argument("case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def store_case(context: click.Context, case_id: str, dry_run: bool):
    """Include links to decompressed FASTQ files belonging to this case in housekeeper"""

    status_db: Store = context.obj.status_db
    try:
        samples: Iterable[str] = get_fastq_individuals(status_db, case_id)
        stored_individuals = 0
        for sample_id in samples:
            stored_count: int = context.invoke(store_sample, sample_id=sample_id, dry_run=dry_run)
            stored_individuals += stored_count
    except CaseNotFoundError:
        return
    LOG.info(f"Stored fastq files for {stored_individuals} samples")


@click.command("flowcell")
@click.argument("flowcell_id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def store_flowcell(context: click.Context, flowcell_id: str, dry_run: bool):
    """Include links to decompressed FASTQ files belonging to this flowcell in housekeeper"""

    status_db: Store = context.obj.status_db
    samples: List[models.Sample] = status_db.get_samples_from_flowcell(flowcell_id=flowcell_id)
    stored_individuals = 0
    for sample in samples:
        stored_count: int = context.invoke(
            store_sample, sample_id=sample.internal_id, dry_run=dry_run
        )
        stored_individuals += stored_count
    LOG.info(f"Stored fastq files for {stored_individuals} samples")


@click.command("ticket")
@click.argument("ticket_id", type=int)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def store_ticket(context: click.Context, ticket_id: int, dry_run: bool):
    """Include links to decompressed FASTQ files belonging to this ticket in housekeeper"""
    status_db: Store = context.obj.status_db
    samples: List[models.Sample] = status_db.get_samples_from_ticket(ticket_id=ticket_id)
    stored_individuals = 0
    for sample in samples:
        stored_count: int = context.invoke(
            store_sample, sample_id=sample.internal_id, dry_run=dry_run
        )
        stored_individuals += stored_count
    LOG.info(f"Stored fastq files for {stored_individuals} samples")
