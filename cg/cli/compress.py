import logging
from pathlib import Path

import click

from cg.apps import hk, scoutapi, crunchy
from cg.apps.crunchy import FASTQ_FIRST_SUFFIX, FASTQ_SECOND_SUFFIX
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
@click.option("--case-id", "-c", type=str)
@click.option("-n", "--number-of-conversions", type=int)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def spring(context, case_id, number_of_conversions, dry_run):
    """Find cases with fastq-files to compress with spring"""
    # Scan all cases in status database for fastq
    conversion_count = 0
    for case in context.obj["status"].family(case_id):
        if conversion_count == number_of_conversions and not case_id:
            break
        case_id = case.family.internal_id
        fastq_dict = context.obj["hk"].get_fastq_files(bundle=case_id)
        case_is_compressable = True
        for sample, fastq_files in fastq_dict.items():
            fastq_first = fastq_files["fastq_first_path"]
            fastq_second = fastq_files["fastq_second_path"]
            if not context.obj["crunchy"].fastq_compression_ready(
                fastq_first_path=fastq_first, fastq_second_path=fastq_second
            ):
                case_is_compressable = False
                break
        if case_is_compressable:
            LOG.info("Compressing fastq-files for %s", case_id)
            for sample, fastq_files in fastq_dict.items():
                LOG.info(sample)
                fastq_first = fastq_files["fastq_first_path"]
                fastq_second = fastq_files["fastq_second_path"]
                context.obj["crunchy"].spring(
                    fastq_first_path=fastq_first,
                    fastq_second_path=fastq_second,
                    dry_run=dry_run,
                )
            conversion_count += 1


@compress.command()
@click.option("-c", "--case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def cram(context, case_id, dry_run):
    """Bam compress fastq-files for case"""
    click.echo("To be written")
