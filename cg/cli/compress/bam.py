"""CLI for compressing bam files"""
import logging

import click

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-c", "--case-id", type=str)
@click.option("-n", "--number-of-conversions", default=10, type=int, show_default=True)
@click.option("-t", "--ntasks", type=int, help="Number of tasks for slurm job")
@click.option("-m", "--mem", type=int, help="Memory for slurm job")
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def bam(context, case_id, number_of_conversions, ntasks, mem, dry_run):
    """Find cases with BAM files and compress into CRAM"""

    compress_api = context.obj["compress"]
    if ntasks:
        compress_api.ntasks = ntasks
    if mem:
        compress_api.mem = mem
    store = context.obj["db"]
    cases = store.families()
    if case_id:
        cases = [store.family(case_id)]

    conversion_count = 0
    for case in cases:
        if conversion_count == number_of_conversions:
            LOG.info("compressed bam-files for %s cases", conversion_count)
            return
        case_id = case.internal_id
        res = compress_api.compress_case(case_id, ntasks=ntasks, mem=mem, dry_run=dry_run)
        if res is False:
            LOG.info("skipping %s", case_id)
            continue
        conversion_count += 1
