"""CLI function to compress FASTQ files into SPRING archives"""

import datetime as dt
import logging
from typing import Iterable, List, Optional

import click

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.compress.helpers import correct_spring_paths, get_fastq_individuals, update_compress_api
from cg.constants.compression import CASES_TO_IGNORE
from cg.exc import CaseNotFoundError
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models

LOG = logging.getLogger(__name__)

# There is a list of problematic cases that we should skip


@click.command("fastq")
@click.option("-c", "--case-id", type=str)
@click.option("-n", "--number-of-conversions", default=5, type=int, show_default=True)
@click.option("-t", "--ntasks", default=12, show_default=True, help="Number of tasks for slurm job")
@click.option("-m", "--mem", default=50, show_default=True, help="Memory for slurm job")
@click.option(
    "-b",
    "--days-back",
    default=60,
    show_default=True,
    help="Threshold for how long ago family was created",
)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_obj
def fastq_cmd(
    context: CGConfig,
    case_id: Optional[str],
    number_of_conversions: int,
    ntasks: int,
    mem: int,
    days_back: int,
    dry_run: bool,
):
    """Find cases with FASTQ files and compress into SPRING"""
    LOG.info("Running compress FASTQ")
    compress_api: CompressAPI = context.meta_apis["compress_api"]
    store: Store = context.status_db
    update_compress_api(compress_api, dry_run=dry_run, ntasks=ntasks, mem=mem)

    cases: List[models.Family] = []
    if case_id:
        case_obj: models.Family = store.family(case_id)
        if not case_obj:
            LOG.warning("Could not find case %s", case_id)
            return
        cases.append(case_obj)
    else:
        date_threshold = dt.datetime.now() - dt.timedelta(days=days_back)
        cases = compress_api.get_cases_to_compress(store, date_threshold=date_threshold)

    case_conversion_count = 0
    ind_conversion_count = 0
    for case in cases:
        # Keeps track on if all samples in a case have been converted
        case_converted = True
        if case_conversion_count >= number_of_conversions:
            break
        internal_id: str = case.internal_id
        if internal_id in CASES_TO_IGNORE:
            LOG.info("Skipping case %s", internal_id)
            continue

        LOG.info("Searching for FASTQ files in case %s", internal_id)
        if not case.links:
            continue
        for link_obj in case.links:
            sample_id: str = link_obj.sample.internal_id
            case_converted: bool = compress_api.compress_fastq(sample_id)
            if not case_converted:
                LOG.info("skipping individual %s", sample_id)
                continue
            ind_conversion_count += 1
        if case_converted:
            case_conversion_count += 1
            LOG.info("Considering case %s converted", internal_id)

    LOG.info(
        "%s Individuals in %s (completed) cases where compressed",
        ind_conversion_count,
        case_conversion_count,
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
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_obj
def clean_fastq(context: CGConfig, case_id: Optional[str], days_back: int, dry_run: bool):
    """Remove compressed FASTQ files, and update links in housekeeper to SPRING files"""
    LOG.info("Running compress clean FASTQ")
    compress_api: CompressAPI = context.meta_apis["compress_api"]
    store: Store = context.status_db
    update_compress_api(compress_api, dry_run=dry_run)

    cases: List[models.Family] = []
    if case_id:
        case_obj: models.Family = store.family(case_id)
        if not case_obj:
            LOG.warning("Could not find case %s", case_id)
            return
        cases.append(case_obj)
    else:
        date_threshold = dt.datetime.now() - dt.timedelta(days=days_back)
        cases = compress_api.get_cases_to_compress(store, date_threshold=date_threshold)

    cleaned_inds = 0
    for case_obj in cases:
        if case_obj.internal_id in CASES_TO_IGNORE:
            continue
        samples: Iterable[str] = get_fastq_individuals(store=store, case_id=case_obj.internal_id)
        for sample_id in samples:
            res: bool = compress_api.clean_fastq(sample_id)
            if not res:
                LOG.info("Skipping individual %s", sample_id)
                continue
            cleaned_inds += 1

    LOG.info("Cleaned fastqs in %s individuals", cleaned_inds)


@click.command("fix-spring")
@click.option("-b", "--bundle-name")
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_obj
def fix_spring(context: CGConfig, bundle_name: Optional[str], dry_run: bool):
    """Check if bundle(s) have non existing SPRING files and correct these"""
    LOG.info("Running compress clean FASTQ")
    compress_api = context.meta_apis["compress_api"]
    update_compress_api(compress_api, dry_run=dry_run)
    hk_api: HousekeeperAPI = compress_api.hk_api
    correct_spring_paths(hk_api=hk_api, bundle_name=bundle_name, dry_run=dry_run)


@click.command("sample")
@click.argument("sample-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_obj
def decompress_sample(context: CGConfig, sample_id: str, dry_run: bool):
    """Decompress SPRING file, and include links to FASTQ files in housekeeper"""

    compress_api: CompressAPI = context.meta_apis["compress_api"]
    update_compress_api(compress_api, dry_run=dry_run)

    was_decompressed: bool = compress_api.decompress_spring(sample_id)
    if not was_decompressed:
        LOG.info(f"Skipping sample {sample_id}")
        return 0
    LOG.info(f"Decompressed sample {sample_id}")
    return 1


@click.command("case")
@click.argument("case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def decompress_case(context: click.Context, case_id, dry_run):
    """Decompress SPRING file, and include links to FASTQ files in housekeeper"""

    store: Store = context.obj.status_db
    try:
        samples: Iterable[str] = get_fastq_individuals(store, case_id)
        decompressed_inds = 0
        for sample_id in samples:
            decompressed_count: int = context.invoke(
                decompress_sample, sample_id=sample_id, dry_run=dry_run
            )
            decompressed_inds += decompressed_count
    except CaseNotFoundError:
        return
    LOG.info(f"Decompressed spring archives in {decompressed_inds} samples")


@click.command("flowcell")
@click.argument("flowcell_id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_obj
def decompress_flowcell(context: click.Context, flowcell_id: str, dry_run: bool):
    """Decompress SPRING file, and include links to FASTQ files in housekeeper"""

    store: Store = context.obj.status_db
    samples: Iterable[models.Sample] = store.get_samples_from_flowcell(flowcell_name=flowcell_id)
    decompressed_inds = 0
    for sample in samples:
        decompressed_count = context.invoke(
            decompress_sample, sample_id=sample.internal_id, dry_run=dry_run
        )
        decompressed_inds += decompressed_count
    LOG.info(f"Decompressed spring archives in {decompressed_inds} samples")


@click.command("ticket")
@click.argument("ticket", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def decompress_ticket(context: click.Context, ticket: str, dry_run: bool):
    """Decompress SPRING file, and include links to FASTQ files in housekeeper"""
    store: Store = context.obj.status_db
    samples: Iterable[models.Sample] = store.get_samples_from_ticket(ticket=ticket)
    decompressed_inds = 0
    for sample in samples:
        decompressed_count = context.invoke(
            decompress_sample, sample_id=sample.internal_id, dry_run=dry_run
        )
        decompressed_inds += decompressed_count
    LOG.info(f"Decompressed spring archives in {decompressed_inds} samples")
