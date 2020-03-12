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


# @compress.command()
# @click.option("--case-id", "-c", type=str)
# @click.option("-n", "--number-of-conversions", type=int)
# @click.option("-d", "--dry-run", is_flag=True)
# @click.pass_context
# def spring(context, case_id, number_of_conversions, dry_run):
#     """Find cases with fastq-files and compress with spring"""
#     compress_api = CompressAPI(hk_api=context.obj["hk"], crunchy_api=context.obj["crunchy"])
#     conversion_count = 0
#     if case_id:
#         families = [context.obj["db"].family(case_id)]
#     else:
#         families = context.obj["db"].families()
#     for case in families:
#         if conversion_count == number_of_conversions:
#             break
#         case_id = case.internal_id
#         fastq_dict = compress_api.get_fastq_files(bundle=case_id)
#         if not fastq_dict:
#             continue
#         case_is_compressable = True
#         for sample, fastq_files in fastq_dict.items():
#             fastq_first = Path(fastq_files["fastq_first_path"])
#             fastq_second = Path(fastq_files["fastq_second_path"])
#             if not context.obj["crunchy"].fastq_compression_possible(
#                 fastq_first_path=fastq_first, fastq_second_path=fastq_second
#             ):
#                 case_is_compressable = False
#                 break
#         if case_is_compressable:
#             LOG.info("Compressing fastq-files for %s", case_id)
#             for sample, fastq_files in fastq_dict.items():
#                 fastq_first = Path(fastq_files["fastq_first_path"])
#                 fastq_second = Path(fastq_files["fastq_second_path"])
#                 LOG.info(
#                     "compressing %s and %s for sample %s",
#                     fastq_first,
#                     fastq_second,
#                     sample,
#                 )
#                 context.obj["crunchy"].spring(
#                     fastq_first_path=fastq_first,
#                     fastq_second_path=fastq_second,
#                     dry_run=dry_run,
#                 )
#             conversion_count += 1


@compress.command()
@click.option("-c", "--case-id", type=str)
@click.option("-n", "--number-of-conversions", type=int)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def cram(context, case_id, number_of_conversions, dry_run):
    """Find cases with bam-files and compress into cram"""

    compress_api = CompressAPI(
        hk_api=context.obj["hk"],
        crunchy_api=context.obj["crunchy"],
        scout_api=context.obj["scout"],
    )
    conversion_count = 0
    if case_id:
        families = [context.obj["db"].family(case_id)]
    else:
        families = context.obj["db"].families()
    for case in families:
        if conversion_count == number_of_conversions:
            LOG.info("compressed bam-files for %s cases", conversion_count)
            break
        case_id = case.internal_id
        bam_dict = compress_api.get_bam_files_from_scout(case_id=case_id)
        if not bam_dict:
            continue
        case_is_compressable = True
        for sample, bam_file in bam_dict.items():
            if not context.obj["crunchy"].bam_compression_possible(bam_path=bam_file):
                case_is_compressable = False
                break
        if case_is_compressable:
            LOG.info("Compressing bam-files for %s", case_id)
            compress_api.compress_case(bam_dict=bam_dict, dry_run=dry_run)
            conversion_count += 1
