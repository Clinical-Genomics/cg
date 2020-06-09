"""CLI for compressing bam files"""
import logging

import click

from cg.exc import CaseNotFoundError

from .helpers import get_cases, update_compress_api

LOG = logging.getLogger(__name__)


@click.command("bam")
@click.option("-c", "--case-id", type=str)
@click.option("-n", "--number-of-conversions", default=10, type=int, show_default=True)
@click.option("-t", "--ntasks", type=int, help="Number of tasks for slurm job")
@click.option("-m", "--mem", type=int, help="Memory for slurm job")
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def bam_cmd(context, case_id, number_of_conversions, ntasks, mem, dry_run):
    """Find cases with BAM files and compress into CRAM"""

    compress_api = context.obj["compress"]
    update_compress_api(compress_api, dry_run=dry_run, ntasks=ntasks, mem=mem)

    store = context.obj["db"]
    try:
        cases = get_cases(store, case_id)
    except CaseNotFoundError:
        raise click.Abort

    conversion_count = 0
    for case in cases:
        if conversion_count == number_of_conversions:
            LOG.info("compressed bam-files for %s cases", conversion_count)
            return
        case_id = case.internal_id
        res = compress_api.compress_case(case_id)
        if res is False:
            LOG.info("skipping %s", case_id)
            continue
        conversion_count += 1


@click.command("bam")
@click.option("-c", "--case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def clean_bam(context, case_id, dry_run):
    """Remove compressed BAM files, and update links in scout and housekeeper
       to CRAM files"""
    compress_api = context.obj["compress"]
    update_compress_api(compress_api, dry_run=dry_run)
    store = context.obj["db"]

    try:
        cases = get_cases(store, case_id)
    except CaseNotFoundError:
        raise click.Abort

    for case in cases:
        case_id = case.internal_id
        compress_api.clean_bams(case_id)
