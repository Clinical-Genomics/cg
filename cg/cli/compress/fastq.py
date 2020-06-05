"""CLI to compress fastq"""

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
def fastq(context, case_id, number_of_conversions, ntasks, mem, dry_run):
    """ Find cases with FASTQ files and compress into SPRING """
    compress_api = context.obj["compress"]
    store = context.obj["db"]

    if ntasks:
        compress_api.ntasks = ntasks
    if mem:
        compress_api.mem = mem

    conversion_count = 0
    cases = store.families()
    if case_id:
        cases = [context.obj["db"].family(case_id)]

    for case in cases:
        if conversion_count == number_of_conversions:
            LOG.info("compressed FASTQ files for %s cases", conversion_count)
            return

        case_id = case.internal_id
        LOG.info("Searching for FASTQ files in %s", case_id)
        for link_obj in case.links:
            sample_id = link_obj.sample.internal_id
            res = compress_api.compress_fastq(sample_id, dry_run=dry_run)
            if res is False:
                LOG.info("skipping individual %s", sample_id)
                continue
        conversion_count += 1
