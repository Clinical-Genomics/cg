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
@click.option("-c", "--case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def spring(context, case_id, dry_run):
    """Spring compress fastq-files for case"""
    fastq_files = context.obj["hk"].get_files(bundle=case_id, tags=["fastq"])
    fastq_first_path = None
    fastq_second_path = None
    for fastq_file in fastq_files:
        if fastq_file.full_path.endswith(FASTQ_FIRST_SUFFIX):
            fastq_first_path = fastq_file.full_path
        if fastq_file.full_path.endswith(FASTQ_SECOND_SUFFIX):
            fastq_second_path = fastq_file.full_path
    if all([fastq_first_path, fastq_second_path]):
        # See if fastq_file are already compressed
        if context.obj["crunchy"].spring_compression_exists(
            fastq_first_path=fastq_first_path, fastq_second_path=fastq_second_path
        ):
            LOG.debug("fastq-files for %s are already compressed", case_id)
        else:
            LOG.info("Compressing fastq-files for case %s", case_id)
            context.obj["crunchy"].spring(
                fastq_first_path=fastq_first_path,
                fastq_second_path=fastq_second_path,
                dry_run=dry_run,
            )


@compress.command()
@click.option("-n", "--number-of-conversions", type=int)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def springauto(context, case_id, number_of_conversions, dry_run):
    """Find cases with fastq-files to compress with spring"""
    # Scan all cases in status database for fastq
    conversion_count = 0
    for case in context.obj["status"].cases():
        if conversion_count == number_of_conversions:
            break
        case_id = case["internal_id"]
        fastq_files = context.obj["hk"].get_files(bundle=case_id, tags=["fastq"])
        fastq_first_path = None
        fastq_second_path = None
        for fastq_file in fastq_files:
            if fastq_file.full_path.endswith(FASTQ_FIRST_SUFFIX):
                fastq_first_path = fastq_file.full_path
            if fastq_file.full_path.endswith(FASTQ_SECOND_SUFFIX):
                fastq_second_path = fastq_file.full_path

        # See if paired fastq_files are found
        if all([fastq_first_path, fastq_second_path]):
            # See if fastq_file are already compressed
            if context.obj["crunchy"].compression_successful_spring(
                fastq_first_path=fastq_first_path, fastq_second_path=fastq_second_path
            ):
                LOG.debug("fastq-files for %s are already compressed", case_id)
                continue
            context.invoke(spring, case_id=case_id, dry_run=dry_run)
            conversion_count += 1
        else:
            LOG.debug("Could not find paired fastq-files for cases %s", case_id)


@compress.command()
@click.option("-c", "--case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def cram(context, case_id, dry_run):
    """Bam compress fastq-files for case"""
    click.echo("To be written")


@compress.command()
@click.option("-n", "--number-of-conversions", type=int)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def cramauto(context, case_id, number_of_conversions, dry_run):
    """Find cases with bam-files to compress into cram"""
    click.echo("To be written")
