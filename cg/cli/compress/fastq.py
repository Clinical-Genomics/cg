"""CLI to compress fastq"""

import logging

import click

LOG = logging.getLogger(__name__)


@click.command("fastq")
@click.option("-c", "--case-id", type=str)
@click.option("-n", "--number-of-conversions", default=10, type=int, show_default=True)
@click.option("-t", "--ntasks", type=int, help="Number of tasks for slurm job")
@click.option("-m", "--mem", type=int, help="Memory for slurm job")
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def fastq_cmd(context, case_id, number_of_conversions, ntasks, mem, dry_run):
    """ Find cases with FASTQ files and compress into SPRING """
    compress_api = context.obj["compress"]

    if ntasks:
        compress_api.ntasks = ntasks
    if mem:
        compress_api.mem = mem

    cases = context.obj["db"].families()
    if case_id:
        case_obj = context.obj["db"].family(case_id)
        if not case_obj:
            LOG.warning("Could not find case %s", case_id)
            return
        cases = [case_obj]

    conversion_count = 0
    nr_cases = 0
    for nr_cases, case in enumerate(cases, 1):
        case_converted = True
        if conversion_count >= number_of_conversions:
            continue

        LOG.info("Searching for FASTQ files in %s", case.internal_id)
        for link_obj in case.links:
            sample_id = link_obj.sample.internal_id
            res = compress_api.compress_fastq(sample_id, dry_run=dry_run)
            if res is False:
                LOG.info("skipping individual %s", sample_id)
                continue
            case_converted = False
        if not case_converted:
            conversion_count += 1

    if nr_cases == 0:
        LOG.warning("No cases found")
        return
    LOG.info("Individuals in %s cases where compressed", conversion_count)
