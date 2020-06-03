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
    crunchy_api = context.obj["crunchy"]
    store = context.obj["db"]
    conversion_count = 0
    cases = store.families()
    if case_id:
        cases = [context.obj["db"].family(case_id)]

    for case in cases:
        if conversion_count == number_of_conversions:
            LOG.info("compressed FASTQ files for %s cases", conversion_count)
            return

        res = compress_api.compress_case_fastq(case=case)
        case_id = case.internal_id
        LOG.info("Searching for FASTQ files in %s", case_id)
        case_fastq_dict = dict()
        case_has_fastq_files = True
        compression_is_pending = False
        for link_obj in case.links:
            sample_id = link_obj.sample.internal_id
            sample_fastq_dict = compress_api.get_fastq_files(sample_id=sample_id)
            if not sample_fastq_dict:
                LOG.info("Could not find FASTQ files for %s", sample_id)
                case_has_fastq_files = False
                break

            first_fastq = sample_fastq_dict["fastq_first_file"]
            second_fastq = sample_fastq_dict["fastq_second_file"]
            spring_compression_done = crunchy_api.is_spring_compression_done(first_fastq)
            if spring_compression_done:
                LOG.warning("FASTQ to SPRING compression already done for %s", sample_id)
                case_has_fastq_files = False
                break

            spring_compression_pending = crunchy_api.is_spring_compression_pending(
                first_fastq, second_fastq
            )
            if spring_compression_pending:
                LOG.info("FASTQ to SPRING compression pending for %s", sample_id)
                compression_is_pending = True
                break
            case_fastq_dict[sample_id] = sample_fastq_dict

            if case_has_fastq_files and not compression_is_pending:
                LOG.info("Compressing FASTQ files for %s", case_id)
                compress_api.compress_case_fastqs(
                    fastq_dict=case_fastq_dict, ntasks=ntasks, mem=mem, dry_run=dry_run
                )
                conversion_count += 1
