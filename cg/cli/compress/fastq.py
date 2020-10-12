"""CLI function to compress FASTQ files into SPRING archives"""

import logging

import click

from cg.exc import CaseNotFoundError

from .helpers import (
    correct_spring_paths,
    get_fastq_cases,
    get_fastq_individuals,
    update_compress_api,
)

LOG = logging.getLogger(__name__)

# There is a list of problematic cases that we should skip
PROBLEMATIC_CASES = [
    "modernbee",
    "suremako",
    "expertalien",
    "wisestork",
    "richalien",
    "deepcub",
    "causalmite",
    "proudcollie",
    "loyalegret",
    "grandkoi",
    "fluenteagle",
    "lovingmayfly",
]

# List of cases used for validation that we should skip
VALIDATION_CASES = [
    "mintyeti",
    "topsrhino",
    "gladthrush",
    "cleanshrimp",
    "usablemarten",
    "casualgannet",
    "pumpedcat",
    "firstfawn",
    "helpedfilly",
    "daringpony",
    "strongbison",
    "proeagle",
    "easybeetle",
    "sharppigeon",
    "gamedeer",
    "keencalf",
    "epicasp",
    "safeguinea",
    "hotviper",
    "hotskink",
    "onemite",
    "busycolt",
    "rightmacaw",
    "intentcorgi",
    "vitalmouse",
    "lightprawn",
    "meetpossum",
    "strongman",
    "mintbaboon",
    "propercoral",
    "livingox",
    "keenviper",
    "sharpparrot",
    "moralgoat",
    "fleetjay",
    "bosssponge",
    "unitedbeagle",
]


@click.command("fastq")
@click.option("-c", "--case-id", type=str)
@click.option("-n", "--number-of-conversions", default=5, type=int, show_default=True)
@click.option("-t", "--ntasks", default=12, show_default=True, help="Number of tasks for slurm job")
@click.option("-m", "--mem", default=50, show_default=True, help="Memory for slurm job")
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def fastq_cmd(context, case_id, number_of_conversions, ntasks, mem, dry_run):
    """ Find cases with FASTQ files and compress into SPRING """
    LOG.info("Running compress FASTQ")
    update_compress_api(context.obj["compress_api"], dry_run=dry_run, ntasks=ntasks, mem=mem)

    store = context.obj["status_db"]
    try:
        cases = get_fastq_cases(store, case_id)
    except CaseNotFoundError:
        return

    case_conversion_count = 0
    ind_conversion_count = 0
    for case in cases:
        # Keeps track on if all samples in a case have been converted
        case_converted = True
        if case_conversion_count >= number_of_conversions:
            break
        internal_id = case.internal_id
        if internal_id in [*PROBLEMATIC_CASES, *VALIDATION_CASES]:
            LOG.info("Skipping case %s", internal_id)
            continue

        LOG.info("Searching for FASTQ files in case %s", internal_id)
        for link_obj in case.links:
            sample_id = link_obj.sample.internal_id
            case_converted = context.obj["compress_api"].compress_fastq(sample_id)
            if case_converted is False:
                LOG.info("skipping individual %s", sample_id)
                continue
            ind_conversion_count += 1
        if case_converted:
            case_conversion_count += 1

    LOG.info(
        "%s Individuals in %s (completed) cases where compressed",
        ind_conversion_count,
        case_conversion_count,
    )


@click.command("fastq")
@click.option("-c", "--case-id")
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def clean_fastq(context, case_id, dry_run):
    """Remove compressed FASTQ files, and update links in housekeeper to SPRING files"""
    LOG.info("Running compress clean FASTQ")
    compress_api = context.obj["compress_api"]
    update_compress_api(compress_api, dry_run=dry_run)

    store = context.obj["status_db"]
    samples = get_fastq_individuals(store, case_id)

    cleaned_inds = 0
    try:
        for sample_id in samples:
            res = compress_api.clean_fastq(sample_id)
            if res is False:
                LOG.info("skipping individual %s", sample_id)
                continue
            cleaned_inds += 1
    except CaseNotFoundError:
        return

    LOG.info("Cleaned fastqs in %s individuals", cleaned_inds)


@click.command("fix-spring")
@click.option("-b", "--bundle-name")
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def fix_spring(context, bundle_name, dry_run):
    """Check if bundle(s) have non existing SPRING files and correct these"""
    LOG.info("Running compress clean FASTQ")
    compress_api = context.obj["compress_api"]
    update_compress_api(compress_api, dry_run=dry_run)
    hk_api = compress_api.hk_api
    correct_spring_paths(hk_api=hk_api, bundle_name=bundle_name, dry_run=dry_run)


@click.command("spring")
@click.argument("case-id")
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def decompress_spring(context, case_id, dry_run):
    """Decompress SPRING file, and include links to FASTQ files in housekeeper"""
    LOG.info("Running decompress spring")
    compress_api = context.obj["compress_api"]
    update_compress_api(compress_api, dry_run=dry_run)

    store = context.obj["status_db"]
    samples = get_fastq_individuals(store, case_id)

    decompressed_inds = 0
    try:
        for sample_id in samples:
            was_decompressed = compress_api.decompress_spring(sample_id)
            if was_decompressed is False:
                LOG.info("skipping individual %s", sample_id)
                continue
            decompressed_inds += 1
    except CaseNotFoundError:
        return

    LOG.info("Decompressed spring archives in %s individuals", decompressed_inds)
