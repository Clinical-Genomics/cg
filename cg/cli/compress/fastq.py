"""CLI function to compress FASTQ files into SPRING archives."""

import logging
from typing import Iterable

import rich_click as click

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.compress.helpers import (
    compress_sample_fastqs_in_cases,
    correct_spring_paths,
    get_cases_to_process,
    update_compress_api,
)
from cg.constants.cli_options import DRY_RUN
from cg.exc import CaseNotFoundError
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.command("fastq")
@click.option("-c", "--case-id", type=str)
@click.option(
    "-b",
    "--days-back",
    default=60,
    show_default=True,
    help="Threshold for how long ago was the case created",
)
@click.option("--hours", type=int, help="Hours to allocate for slurm job")
@click.option("-m", "--mem", type=int, help="Memory for slurm job")
@click.option("-t", "--ntasks", type=int, help="Number of tasks for slurm job")
@click.option("-n", "--number-of-conversions", default=5, type=int, show_default=True)
@DRY_RUN
@click.pass_obj
def fastq_cmd(
    context: CGConfig,
    case_id: str | None,
    days_back: int,
    hours: int | None,
    dry_run: bool,
    mem: int | None,
    ntasks: int | None,
    number_of_conversions: int,
):
    """Compress old FASTQ files into SPRING."""
    LOG.info("Running compress FASTQ")
    compress_api: CompressAPI = context.meta_apis["compress_api"]
    store: Store = context.status_db
    cases: list[Case] = get_cases_to_process(case_id=case_id, days_back=days_back, store=store)
    if not cases:
        LOG.info("No cases to compress")
        return None
    compress_sample_fastqs_in_cases(
        compress_api=compress_api,
        cases=cases,
        dry_run=dry_run,
        number_of_conversions=number_of_conversions,
        hours=hours,
        mem=mem,
        ntasks=ntasks,
    )


@click.command("fastq")
@click.option("-c", "--case-id")
@click.option(
    "-b",
    "--days-back",
    default=60,
    show_default=True,
    help="Threshold for how long ago was the case created",
)
@DRY_RUN
@click.pass_obj
def clean_fastq(context: CGConfig, case_id: str | None, days_back: int, dry_run: bool):
    """Remove compressed FASTQ files, and update links in Housekeeper to SPRING files."""
    LOG.info("Running compress clean FASTQ")
    compress_api: CompressAPI = context.meta_apis["compress_api"]
    store: Store = context.status_db
    update_compress_api(compress_api, dry_run=dry_run)

    cases: list[Case] | None = get_cases_to_process(
        case_id=case_id, days_back=days_back, store=store
    )
    if not cases:
        LOG.info("Did not find any FASTQ files to clean. Closing")
        return
    is_successful: bool = True
    for case in cases:
        samples: list[Sample] = case.samples
        if not compress_api.clean_fastq_files_for_samples(samples=samples, days_back=days_back):
            is_successful: bool = False
    if not is_successful:
        click.Abort("Failed to clean FASTQ files. Aborting")


@click.command("fix-spring")
@click.option("-b", "--bundle-name")
@DRY_RUN
@click.pass_obj
def fix_spring(context: CGConfig, bundle_name: str | None, dry_run: bool):
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
        samples: Iterable[str] = store.get_sample_ids_by_case_id(case_id=case_id)
        decompressed_individuals = 0
        for sample_id in samples:
            decompressed_count: int = context.invoke(
                decompress_sample, sample_id=sample_id, dry_run=dry_run
            )
            decompressed_individuals += decompressed_count
    except CaseNotFoundError:
        return
    LOG.info(f"Decompressed spring archives in {decompressed_individuals} samples")


@click.command("illumina-run")
@click.argument("flow-cell-id", type=str)
@DRY_RUN
@click.pass_obj
def decompress_illumina_run(context: click.Context, flow_cell_id: str, dry_run: bool):
    """Decompress SPRING files for flow cell, and include links to FASTQ files in Housekeeper."""

    store: Store = context.obj.status_db
    samples: Iterable[Sample] = store.get_samples_by_illumina_flow_cell(flow_cell_id)
    decompressed_individuals = 0
    for sample in samples:
        decompressed_count = context.invoke(
            decompress_sample, sample_id=sample.internal_id, dry_run=dry_run
        )
        decompressed_individuals += decompressed_count
    LOG.info(f"Decompressed spring archives in {decompressed_individuals} samples")


@click.command("ticket")
@click.argument("ticket", type=str)
@DRY_RUN
@click.pass_context
def decompress_ticket(context: click.Context, ticket: str, dry_run: bool):
    """Decompress SPRING file for ticket, and include links to FASTQ files in Housekeeper."""
    store: Store = context.obj.status_db
    samples: Iterable[Sample] = store.get_samples_from_ticket(ticket=ticket)
    decompressed_individuals = 0
    for sample in samples:
        decompressed_count = context.invoke(
            decompress_sample, sample_id=sample.internal_id, dry_run=dry_run
        )
        decompressed_individuals += decompressed_count
    LOG.info(f"Decompressed spring archives in {decompressed_individuals} samples")
