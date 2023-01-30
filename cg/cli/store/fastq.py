import logging
from pathlib import Path
from typing import Iterable, List

import click
from housekeeper.store.models import File

from cg.apps.crunchy.files import update_metadata_paths
from cg.cli.compress.helpers import update_compress_api
from cg.constants import SequencingFileTag
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
def store_sample(context: CGConfig, sample_id: str, dry_run: bool) -> int:
    """Include links to decompressed FASTQ files belonging to this sample in Housekeeper."""
    compress_api: CompressAPI = context.meta_apis["compress_api"]
    status_db: Store = context.status_db
    update_compress_api(compress_api, dry_run=dry_run)
    sample = status_db.sample(internal_id=sample_id)
    if not sample:
        LOG.warning(f"Could not find {sample_id}")
        return 0
    was_decompressed: bool = compress_api.add_decompressed_fastq(sample)
    if not was_decompressed:
        LOG.info(f"Skipping sample {sample_id}")
        return 0
    LOG.info(f"Stored fastq files for {sample_id}")
    return 1


def invoke_store_samples(context: click.Context, sample_ids: List[str], dry_run: bool) -> int:
    """Invoke store sample for sample ids."""
    stored_individuals: int = 0
    for sample_id in sample_ids:
        stored_count: int = context.invoke(store_sample, sample_id=sample_id, dry_run=dry_run)
        stored_individuals += stored_count
    return stored_individuals


@click.command("case")
@click.argument("case-id", type=str)
@DRY_RUN
@click.pass_context
def store_case(context: click.Context, case_id: str, dry_run: bool) -> None:
    """Include links to decompressed FASTQ files belonging to this case in Housekeeper."""

    status_db: Store = context.obj.status_db
    try:
        sample_ids: Iterable[str] = status_db.get_sample_ids_by_case_id(case_id=case_id)
        stored_individuals: int = invoke_store_samples(
            context=context, dry_run=dry_run, sample_ids=sample_ids
        )
    except CaseNotFoundError:
        return
    LOG.info(f"Stored fastq files for {stored_individuals} samples")


@click.command("flow-cell")
@click.argument("flow-cell-id", type=str)
@DRY_RUN
@click.pass_context
def store_flow_cell(context: click.Context, flow_cell_id: str, dry_run: bool) -> None:
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
def store_ticket(context: click.Context, ticket: str, dry_run: bool) -> None:
    """Include links to decompressed FASTQ files belonging to a ticket in Housekeeper."""
    status_db: Store = context.obj.status_db
    samples: List[Sample] = status_db.get_samples_from_ticket(ticket=ticket)
    stored_individuals: int = invoke_store_samples(
        context=context, dry_run=dry_run, sample_ids=[sample.internal_id for sample in samples]
    )
    LOG.info(f"Stored fastq files for {stored_individuals} samples")


@click.command("demultiplexed-flow-cell")
@click.argument("flow-cell-id", type=str)
@DRY_RUN
@click.pass_obj
def store_demultiplexed_flow_cell(context: click.Context, flow_cell_id: str, dry_run: bool) -> None:
    """Include all files in a flow cell bundle and its corresponding sequencing files. Updates SPRING metadata file"""
    compress_api: CompressAPI = context.meta_apis["compress_api"]
    status_db: Store = context.status_db
    update_compress_api(compress_api, dry_run=dry_run)

    samples: List[Sample] = status_db.get_samples_from_flow_cell(flow_cell_id=flow_cell_id)
    bundle_names: List[str] = (
        [sample.internal_id for sample in samples if sample.internal_id] + [flow_cell_id]
        if samples
        else [flow_cell_id]
    )
    for bundle_name in bundle_names:
        compress_api.hk_api.include_files_to_latest_version(bundle_name=bundle_name)

    if not samples:
        LOG.info(f"No samples found for flow cell {flow_cell_id} in the database")
        return
    for sample in samples:
        spring_metadata_files: List[File] = compress_api.hk_api.get_files_from_latest_version(
            bundle_name=sample.internal_id, tags=[SequencingFileTag.SPRING_METADATA]
        )
        if spring_metadata_files:
            for spring_metadata_file in spring_metadata_files:
                LOG.info(
                    f"Updating file paths in SPRING metadata file {spring_metadata_file.full_path}: for sample: {sample.internal_id}"
                )
                update_metadata_paths(
                    spring_metadata_path=spring_metadata_file.full_path,
                    new_parent_path=Path(spring_metadata_file.full_path).parent,
                )
