"""CLI to compress fastq"""

import logging

import click

from cg.exc import CaseNotFoundError

from .helpers import get_cases, get_individuals, update_compress_api

LOG = logging.getLogger(__name__)


@click.command("fastq")
@click.option("-c", "--case-id", type=str)
@click.option("-n", "--number-of-conversions", default=5, type=int, show_default=True)
@click.option("-t", "--ntasks", default=12, show_default=True, help="Number of tasks for slurm job")
@click.option("-m", "--mem", default=50, show_default=True, help="Memory for slurm job")
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def fastq_cmd(context, case_id, number_of_conversions, ntasks, mem, dry_run):
    """ Find cases with FASTQ files and compress into SPRING """
    compress_api = context.obj["compress"]
    update_compress_api(compress_api, dry_run=dry_run, ntasks=ntasks, mem=mem)

    store = context.obj["db"]
    try:
        cases = get_cases(store, case_id)
    except CaseNotFoundError:
        return

    conversion_count = 0
    for case in cases:
        # Keeps track on if all samples in a case have been converted
        case_converted = True
        if conversion_count >= number_of_conversions:
            continue

        LOG.info("Searching for FASTQ files in %s", case.internal_id)
        for link_obj in case.links:
            sample_id = link_obj.sample.internal_id
            res = compress_api.compress_fastq(sample_id)
            if res is False:
                LOG.info("skipping individual %s", sample_id)
                continue
            case_converted = False
        if not case_converted:
            conversion_count += 1

    LOG.info("Individuals in %s cases where compressed", conversion_count)


@click.command("fastq")
@click.option("-c", "--case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def clean_fastq(context, case_id, dry_run):
    """Remove compressed FASTQ files, and update links in housekeeper to SPRING files"""
    LOG.info("Running compress fastq")
    compress_api = context.obj["compress"]
    update_compress_api(compress_api, dry_run=dry_run)

    store = context.obj["db"]
    try:
        samples = get_individuals(store, case_id)
    except CaseNotFoundError:
        return

    cleaned_inds = 0
    for sample_id in samples:
        res = compress_api.clean_fastq(sample_id)
        if res is False:
            LOG.info("skipping individual %s", sample_id)
            continue
        cleaned_inds += 1

    LOG.info("Cleaned fastqs in %s individuals", cleaned_inds)
