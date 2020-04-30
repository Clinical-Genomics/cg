"""CLI for compressing bam files"""
import logging
from pathlib import Path

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
    conversion_count = 0
    if case_id:
        cases = [context.obj["db"].family(case_id)]
    else:
        cases = context.obj["db"].families()
    for case in cases:
        if conversion_count == number_of_conversions:
            LOG.info("compressed bam-files for %s cases", conversion_count)
            break
        case_id = case.internal_id
        bam_dict = compress_api.get_bam_files(case_id=case_id)
        if not bam_dict:
            LOG.info("skipping %s", case_id)
            continue
        case_has_bam_file = True
        compression_is_pending = False
        for sample, bam_files in bam_dict.items():
            bam_path = Path(bam_files["bam"].full_path)
            if not context.obj["crunchy"].is_bam_compression_possible(
                bam_path=bam_path
            ):
                LOG.info("BAM to CRAM compression not possible for %s", sample)
                case_has_bam_file = False
                break
            if context.obj["crunchy"].is_cram_compression_pending(bam_path=bam_path):
                LOG.info("BAM to CRAM compression pending for %s", sample)
                compression_is_pending = True
                break

        if case_has_bam_file and not compression_is_pending:
            LOG.info("Compressing bam-files for %s", case_id)
            compress_api.compress_case_bams(
                bam_dict=bam_dict, ntasks=ntasks, mem=mem, dry_run=dry_run
            )
            conversion_count += 1
