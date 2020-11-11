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
    "causalmite",
    "deepcub",
    "expertalien",
    "fluenteagle",
    "grandkoi",
    "lovingmayfly",
    "loyalegret",
    "modernbee",
    "proudcollie",
    "richalien",
    "suremako",
    "wisestork",
]

# List of cases used for validation that we should skip
VALIDATION_CASES = [
    "bosssponge",
    "busycolt",
    "casualgannet",
    "cleanshrimp",
    "daringpony",
    "easybeetle",
    "epicasp",
    "firstfawn",
    "fleetjay",
    "gamedeer",
    "gladthrush",
    "helpedfilly",
    "hotskink",
    "hotviper",
    "intentcorgi",
    "intentmayfly",
    "keencalf",
    "keenviper",
    "lightprawn",
    "livingox",
    "meetpossum",
    "mintbaboon",
    "mintyeti",
    "moralgoat",
    "onemite",
    "proeagle",
    "propercoral",
    "pumpedcat",
    "rightmacaw",
    "safeguinea",
    "sharpparrot",
    "sharppigeon",
    "strongbison",
    "strongman",
    "topsrhino",
    "unitedbeagle",
    "usablemarten",
    "vitalmouse",
]

CASES_TO_IGNORE = PROBLEMATIC_CASES + VALIDATION_CASES


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
        if internal_id in CASES_TO_IGNORE:
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


@click.command("sample")
@click.argument("sample-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def decompress_sample(context, sample_id, dry_run):
    compress_api = context.obj["compress_api"]
    update_compress_api(compress_api, dry_run=dry_run)

    was_decompressed = compress_api.decompress_spring(sample_id)
    if was_decompressed is False:
        LOG.info(f"Skipping sample {sample_id}")
        return 0
    LOG.info(f"Decompressed sample {sample_id}")
    return 1


@click.command("case")
@click.argument("case-id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def decompress_case(context, case_id, dry_run):
    """Decompress SPRING file, and include links to FASTQ files in housekeeper"""

    store = context.obj["status_db"]
    try:
        samples = get_fastq_individuals(store, case_id)
        decompressed_inds = 0
        for sample_id in samples:
            decompressed_count = context.invoke(
                decompress_sample, sample_id=sample_id, dry_run=dry_run
            )
            decompressed_inds += decompressed_count
    except CaseNotFoundError:
        return
    LOG.info(f"Decompressed spring archives in {decompressed_inds} samples")


@click.command("flowcell")
@click.argument("flowcell_id", type=str)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def decompress_flowcell(context, flowcell_id, dry_run):
    """Decompress SPRING file, and include links to FASTQ files in housekeeper"""

    store = context.obj["status_db"]
    samples = store.get_samples_from_flowcell(flowcell_id=flowcell_id)
    decompressed_inds = 0
    for sample in samples:
        decompressed_count = context.invoke(
            decompress_sample, sample_id=sample.internal_id, dry_run=dry_run
        )
        decompressed_inds += decompressed_count
    LOG.info(f"Decompressed spring archives in {decompressed_inds} samples")


@click.command("ticket")
@click.argument("ticket_id", type=int)
@click.option("-d", "--dry-run", is_flag=True)
@click.pass_context
def decompress_ticket(context, ticket_id, dry_run):
    """Decompress SPRING file, and include links to FASTQ files in housekeeper"""
    store = context.obj["status_db"]
    samples = store.get_samples_from_ticket(ticket_id=ticket_id)
    decompressed_inds = 0
    for sample in samples:
        decompressed_count = context.invoke(
            decompress_sample, sample_id=sample.internal_id, dry_run=dry_run
        )
        decompressed_inds += decompressed_count
    LOG.info(f"Decompressed spring archives in {decompressed_inds} samples")
