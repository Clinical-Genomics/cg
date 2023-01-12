"""CLI function to compress FASTQ files into SPRING archives."""

import datetime as dt
import logging
from typing import Iterable, List, Optional

import click

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.compress.helpers import correct_spring_paths, get_fastq_individuals, update_compress_api
from cg.constants.compression import CASES_TO_IGNORE
from cg.constants.constants import DRY_RUN
from cg.exc import CaseNotFoundError
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Family, Sample

LOG = logging.getLogger(__name__)


def get_cases_to_process(
    days_back: int, store: Store, case_id: Optional[str] = None
) -> Optional[List[Family]]:
    """Return cases to process."""
    cases: List[Family] = []
    if case_id:
        case: Family = store.family(case_id)
        if not case:
            LOG.warning(f"Could not find case {case_id}")
            return
        cases.append(case)
    else:
        date_threshold: dt.datetime = dt.datetime.now() - dt.timedelta(days=days_back)
        cases: List[Family] = store.get_cases_to_compress(date_threshold=date_threshold)
    return cases


def is_case_ignored(case_id: str) -> bool:
    """Check if case should be skipped."""
    if case_id in CASES_TO_IGNORE:
        LOG.info(f"Skipping case: {case_id}")
        return True
    return False


@click.command("fastq")
@click.option("-c", "--case-id", type=str)
@click.option(
    "-b",
    "--days-back",
    default=60,
    show_default=True,
    help="Threshold for how long ago family was created",
)
@click.option("--hours", type=int, help="Hours to allocate for slurm job")
@click.option("-m", "--mem", type=int, help="Memory for slurm job")
@click.option("-t", "--ntasks", type=int, help="Number of tasks for slurm job")
@click.option("-n", "--number-of-conversions", default=5, type=int, show_default=True)
@DRY_RUN
@click.pass_obj
def fastq_cmd(
    context: CGConfig,
    case_id: Optional[str],
    days_back: int,
    hours: Optional[int],
    dry_run: bool,
    mem: Optional[int],
    ntasks: Optional[int],
    number_of_conversions: int,
):
    """Compress old FASTQ files into SPRING."""
    LOG.info("Running compress FASTQ")
    compress_api: CompressAPI = context.meta_apis["compress_api"]
    store: Store = context.status_db
    update_compress_api(
        compress_api=compress_api, dry_run=dry_run, hours=hours, mem=mem, ntasks=ntasks
    )
    cases: List[Family] = get_cases_to_process(case_id=case_id, days_back=days_back, store=store)
    if not cases:
        return

    case_conversion_count = 0
    ind_conversion_count = 0
    for case in cases:
        case_converted = True
        if case_conversion_count >= number_of_conversions:
            break
        if is_case_ignored(case_id=case.internal_id):
            continue

        LOG.info(f"Searching for FASTQ files in case {case.internal_id}")
        if not case.links:
            continue
        for case_link in case.links:
            sample_id: str = case_link.sample.internal_id
            case_converted: bool = compress_api.compress_fastq(sample_id=sample_id)
            if not case_converted:
                LOG.info(f"skipping individual {sample_id}")
                continue
            ind_conversion_count += 1
        if case_converted:
            case_conversion_count += 1
            LOG.info(f"Considering case {case.internal_id} converted")

    LOG.info(
        f"{ind_conversion_count} individuals in {case_conversion_count} (completed) cases where compressed"
    )


@click.command("fastq")
@click.option("-c", "--case-id")
@click.option(
    "-b",
    "--days-back",
    default=60,
    show_default=True,
    help="Threshold for how long ago family was created",
)
@DRY_RUN
@click.pass_obj
def clean_fastq(context: CGConfig, case_id: Optional[str], days_back: int, dry_run: bool):
    """Remove compressed FASTQ files, and update links in Housekeeper to SPRING files."""
    LOG.info("Running compress clean FASTQ")
    compress_api: CompressAPI = context.meta_apis["compress_api"]
    store: Store = context.status_db
    update_compress_api(compress_api, dry_run=dry_run)

    cases: List[Family] = get_cases_to_process(case_id=case_id, days_back=days_back, store=store)
    if not cases:
        return

    cleaned_inds = 0
    for case in cases:
        if is_case_ignored(case_id=case.internal_id):
            continue
        samples: Iterable[str] = get_fastq_individuals(store=store, case_id=case.internal_id)
        for sample_id in samples:
            was_cleaned: bool = compress_api.clean_fastq(sample_id=sample_id)
            if not was_cleaned:
                LOG.info(f"Skipping individual {sample_id}")
                continue
            cleaned_inds += 1

    LOG.info(f"Cleaned fastqs in {cleaned_inds} individuals")


@click.command("fix-spring")
@click.option("-b", "--bundle-name")
@DRY_RUN
@click.pass_obj
def fix_spring(context: CGConfig, bundle_name: Optional[str], dry_run: bool):
    """Check if bundle(s) have non-existing SPRING files and correct these."""
    LOG.info("Running fix spring")
    compress_api = context.meta_apis["compress_api"]
    update_compress_api(compress_api, dry_run=dry_run)
    hk_api: HousekeeperAPI = compress_api.hk_api
    correct_spring_paths(hk_api=hk_api, bundle_name=bundle_name, dry_run=dry_run)


@click.command("sample")
@click.argument("sample-id", type=str)
@DRY_RUN
@click.pass_obj
def decompress_sample(context: CGConfig, sample_id: str, dry_run: bool):
    """Decompress SPRING file for sample, and include links to FASTQ files in Housekeeper."""

    compress_api: CompressAPI = context.meta_apis["compress_api"]
    update_compress_api(compress_api=compress_api, dry_run=dry_run)

    was_decompressed: bool = compress_api.decompress_spring(sample_id=sample_id)
    if not was_decompressed:
        LOG.info(f"Skipping sample {sample_id}")
        return 0
    LOG.info(f"Decompressed sample {sample_id}")
    return 1


@click.command("case")
@click.argument("case-id", type=str)
@DRY_RUN
@click.pass_context
def decompress_case(context: click.Context, case_id, dry_run):
    """Decompress SPRING file for case, and include links to FASTQ files in Housekeeper."""

    store: Store = context.obj.status_db
    try:
        samples: Iterable[str] = get_fastq_individuals(store=store, case_id=case_id)
        decompressed_inds = 0
        for sample_id in samples:
            decompressed_count: int = context.invoke(
                decompress_sample, sample_id=sample_id, dry_run=dry_run
            )
            decompressed_inds += decompressed_count
    except CaseNotFoundError:
        return
    LOG.info(f"Decompressed spring archives in {decompressed_inds} samples")


@click.command("flow-cell")
@click.argument("flow-cell-id", type=str)
@DRY_RUN
@click.pass_obj
def decompress_flowcell(context: click.Context, flow_cell_id: str, dry_run: bool):
    """Decompress SPRING files for flow cell, and include links to FASTQ files in Housekeeper."""

    store: Store = context.obj.status_db
    samples: Iterable[Sample] = store.get_samples_from_flowcell(flowcell_name=flow_cell_id)
    decompressed_inds = 0
    for sample in samples:
        decompressed_count = context.invoke(
            decompress_sample, sample_id=sample.internal_id, dry_run=dry_run
        )
        decompressed_inds += decompressed_count
    LOG.info(f"Decompressed spring archives in {decompressed_inds} samples")


@click.command("ticket")
@click.argument("ticket", type=str)
@DRY_RUN
@click.pass_context
def decompress_ticket(context: click.Context, ticket: str, dry_run: bool):
    """Decompress SPRING file for ticket, and include links to FASTQ files in Housekeeper."""
    store: Store = context.obj.status_db
    samples: Iterable[Sample] = store.get_samples_from_ticket(ticket=ticket)
    decompressed_inds = 0
    for sample in samples:
        decompressed_count = context.invoke(
            decompress_sample, sample_id=sample.internal_id, dry_run=dry_run
        )
        decompressed_inds += decompressed_count
    LOG.info(f"Decompressed spring archives in {decompressed_inds} samples")
