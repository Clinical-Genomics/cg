"""Commands for compressing files, and cleaning uncompressed files"""
import logging
from pathlib import Path

import click

from cg.apps import hk, scoutapi, crunchy
from cg.meta.compress import CompressAPI
from cg.store import Store


LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def compress(context):
    """Compress files"""
    context.obj["db"] = Store(context.obj["database"])
    context.obj["hk"] = hk.HousekeeperAPI(context.obj)
    context.obj["scout"] = scoutapi.ScoutAPI(context.obj)
    context.obj["crunchy"] = crunchy.CrunchyAPI(context.obj)


@compress.command()
@click.option("-c", "--case-id", type=str)
@click.option("-n", "--number-of-conversions", default=10, type=int, show_default=True)
@click.option("-t", "--ntasks", type=int, help="Number of tasks for slurm job")
@click.option("-m", "--mem", type=int, help="Memory for slurm job")
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def bam(context, case_id, number_of_conversions, ntasks, mem, dry_run):
    """Find cases with BAM files and compress into CRAM"""

    compress_api = CompressAPI(
        hk_api=context.obj["hk"], crunchy_api=context.obj["crunchy"], scout_api=context.obj["scout"]
    )
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
            if not context.obj["crunchy"].is_bam_compression_possible(bam_path=bam_path):
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


@compress.command()
@click.option("-c", "--case-id", type=str)
@click.option("-n", "--number-of-conversions", default=10, type=int, show_default=True)
@click.option("-t", "--ntasks", type=int, help="Number of tasks for slurm job")
@click.option("-m", "--mem", type=int, help="Memory for slurm job")
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def fastq(context, case_id, number_of_conversions, ntasks, mem, dry_run):
    """ Find cases with FASTQ files and compress into SPRING """
    compress_api = CompressAPI(
        hk_api=context.obj["hk"], crunchy_api=context.obj["crunchy"], scout_api=context.obj["scout"]
    )
    conversion_count = 0
    if case_id:
        cases = [context.obj["db"].family(case_id)]
    else:
        cases = context.obj["db"].families()
    for case in cases:
        if conversion_count == number_of_conversions:
            LOG.info("compressed FASTQ files for %s cases", conversion_count)
            break
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
            if not context.obj["crunchy"].is_fastq_compression_possible(
                fastq_first_path=Path(sample_fastq_dict["fastq_first_file"].full_path),
                fastq_second_path=Path(sample_fastq_dict["fastq_second_file"].full_path),
            ):
                LOG.info("FASTQ to SPRING compression not possible for %s", sample_id)
                case_has_fastq_files = False
                break
            if context.obj["crunchy"].is_spring_compression_pending(
                fastq_first_path=Path(sample_fastq_dict["fastq_first_file"].full_path),
                fastq_second_path=Path(sample_fastq_dict["fastq_second_file"].full_path),
            ):
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


@compress.group()
@click.pass_context
def clean(context):
    """Clean uncompressed files"""


@clean.command("bam")
@click.option("-c", "--case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def clean_bam(context, case_id, dry_run):
    """Remove compressed BAM files, and update links in scout and housekeeper
       to CRAM files"""
    compress_api = CompressAPI(
        hk_api=context.obj["hk"], crunchy_api=context.obj["crunchy"], scout_api=context.obj["scout"]
    )
    if case_id:
        cases = [context.obj["db"].family(case_id)]
    else:
        cases = context.obj["db"].families()
    for case in cases:
        case_id = case.internal_id
        compress_api.clean_bams(case_id, dry_run=dry_run)
