import logging
from typing import Iterable, List

import click
from cg.cli.compress.helpers import get_fastq_individuals, update_compress_api
from cg.constants.constants import DRY_RUN
from cg.exc import CaseNotFoundError
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Sample

LOG = logging.getLogger(__name__)


@click.command("sample")
@click.argument("sample-id", type=str)
@DRY_RUN
@click.pass_obj
def store_sample(context: CGConfig, sample_id: str, dry_run: bool):
    """Include links to decompressed FASTQ files belonging to this sample in Housekeeper."""
    compress_api: CompressAPI = context.meta_apis["compress_api"]
    status_db: Store = context.status_db
    update_compress_api(compress_api, dry_run=dry_run)
    sample_obj = status_db.sample(internal_id=sample_id)
    if not sample_obj:
        LOG.warning(f"Could not find {sample_id}")
        return 0
    was_decompressed: bool = compress_api.add_decompressed_fastq(sample_obj)
    if not was_decompressed:
        LOG.info(f"Skipping sample {sample_id}")
        return 0
    LOG.info(f"Stored fastq files for {sample_id}")
    return 1


def invoke_store_samples(context: click.Context, sample_ids: List[str], dry_run: bool) -> int:
    """Invoke store sample for sample_ids."""
    stored_individuals: int = 0
    for sample_id in sample_ids:
        stored_count: int = context.invoke(store_sample, sample_id=sample_id, dry_run=dry_run)
        stored_individuals += stored_count
    return stored_individuals


@click.command("case")
@click.argument("case-id", type=str)
@DRY_RUN
@click.pass_context
def store_case(context: click.Context, case_id: str, dry_run: bool):
    """Include links to decompressed FASTQ files belonging to this case in Housekeeper."""

    status_db: Store = context.obj.status_db
    try:
        samples: Iterable[str] = get_fastq_individuals(status_db, case_id)
        stored_individuals: int = invoke_store_samples(
            context=context, dry_run=dry_run, sample_ids=samples
        )
    except CaseNotFoundError:
        return
    LOG.info(f"Stored fastq files for {stored_individuals} samples")


@click.command("flow-cell")
@click.argument("flow-cell-id", type=str)
@DRY_RUN
@click.pass_context
def store_flow_cell(context: click.Context, flow_cell_id: str, dry_run: bool):
    """Include links to decompressed FASTQ files belonging to this flow cell in Housekeeper."""

    status_db: Store = context.obj.status_db
    samples: List[Sample] = status_db.get_samples_from_flow_cell(flow_cell_id=flow_cell_id)
    stored_individuals: int = invoke_store_samples(
        context=context, dry_run=dry_run, sample_ids=[sample.internal_id for sample in samples]
    )
    LOG.info(f"Stored fastq files for {stored_individuals} samples")


@click.command("ticket")
@click.argument("ticket", type=str)
@DRY_RUN
@click.pass_context
def store_ticket(context: click.Context, ticket: str, dry_run: bool):
    """Include links to decompressed FASTQ files belonging to a ticket in Housekeeper."""
    status_db: Store = context.obj.status_db
    samples: List[Sample] = status_db.get_samples_from_ticket(ticket=ticket)
    stored_individuals: int = invoke_store_samples(
        context=context, dry_run=dry_run, sample_ids=[sample.internal_id for sample in samples]
    )
    LOG.info(f"Stored fastq files for {stored_individuals} samples")
