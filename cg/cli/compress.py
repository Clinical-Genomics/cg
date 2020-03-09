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
        fastq_files = context.obj["hk"].get_files(bundle=case_id, tags=["fastq"])
        fastq_dict = {}
        for fastq_file in fastq_files:
            sample_name = Path(fastq_file.full_path).name.split("_")[0]
            if sample_name not in fastq_dict.keys():
                fastq_dict[sample_name] = {
                    "fastq_first_path": None,
                    "fastq_second_path": None,
                }
            if fastq_file.full_path.endswith(FASTQ_FIRST_SUFFIX):
                fastq_dict[sample_name]["fastq_first_path"] = fastq_file.full_path
            if fastq_file.full_path.endswith(FASTQ_SECOND_SUFFIX):
                fastq_dict[sample_name]["fastq_second_path"] = fastq_file.full_path

        fastq_check = True
        for sample, fastq_files in fastq_dict.items():
            fastq_first = fastq_files["fastq_first_path"]
            fastq_second = fastq_files["fastq_second_path"]
            if fastq_first is None or not Path(fastq_first).exists():
                LOG.warning(
                    "Could not find fastq %s for sample %s in %s",
                    fastq_first,
                    sample,
                    case_id,
                )
                fastq_check = False
            if fastq_second is None or not Path(fastq_second).exists():
                LOG.warning(
                    "Could not find fastq %s for sample %s in %s",
                    fastq_first,
                    sample,
                    case_id,
                )
                fastq_check = False
            if context.obj["crunchy"].spring_compression_exists(
                fastq_first_path=fastq_first, fastq_second_path=fastq_second
            ):
                LOG.info(
                    "Spring compression already exists for %s and %s",
                    fastq_first,
                    fastq_second,
                )
                fastq_check = False

        if fastq_check:
            fastq_first = fastq_files["fastq_first_path"]
            fastq_second = fastq_files["fastq_second_path"]
            LOG.info("Compressing fastq-files for %s", case_id)
            for sample, fastq_files in fastq_dict.items():
                LOG.info(sample)
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
