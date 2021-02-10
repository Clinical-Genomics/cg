"""Base command for trending"""

import logging
from pathlib import Path

import click
from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.vogue import VogueAPI
from cg.cli.workflow.get_links import get_links
from cg.constants import Pipeline
from cg.exc import AnalysisUploadError
from cg.meta.upload.vogue import UploadVogueAPI
from cg.store import Store

LOG = logging.getLogger(__name__)

VOGUE_VALID_BIOINFO = [str(Pipeline.MIP_DNA), str(Pipeline.BALSAMIC)]


@click.group()
@click.pass_context
def vogue(context):
    """Load trending data into trending database"""

    click.echo(click.style("----------------- TRENDING -----------------------"))

    context.obj["status_db"] = Store(context.obj["database"])
    context.obj["vogue_api"] = VogueAPI(context.obj)
    context.obj["vogue_upload_api"] = UploadVogueAPI(
        genotype_api=GenotypeAPI(context.obj),
        vogue_api=context.obj["vogue_api"],
        store=context.obj["status_db"],
    )


@vogue.command("genotype", short_help="Getting genotype data from the genotype database.")
@click.option(
    "-d", "--days", type=int, required="True", help="load X days old sampels from genotype to vogue"
)
@click.pass_context
def genotype(context, days: int):
    """Loading samples from the genotype database to the trending database"""

    click.echo(click.style("----------------- GENOTYPE -----------------------"))

    context.obj["vogue_upload_api"].load_genotype(days=days)


@vogue.command("apptags", short_help="Getting application tags to the trending database.")
@click.pass_context
def apptags(context):
    """Loading apptags from status db to the trending database"""

    click.echo(click.style("----------------- APPLICATION TAGS -----------------------"))

    context.obj["vogue_upload_api"].load_apptags()


@vogue.command("flowcells", short_help="Getting flowcell data from the lims.")
@click.option(
    "-d", "--days", type=int, required="True", help="load X days old runs from lims to vogue"
)
@click.pass_context
def flowcells(context, days: int):
    """Loading runs from lims to the trending database"""

    LOG.info("----------------- FLOWCELLS -----------------------")

    context.obj["vogue_api"].load_flowcells(days=days)


@vogue.command("samples", short_help="Getting sample data from lims.")
@click.option(
    "-d", "--days", type=int, required="True", help="load X days old sampels from lims to vogue"
)
@click.pass_context
def samples(context, days: int):
    """Loading samples from lims to the trending database"""

    LOG.info("----------------- SAMPLES -----------------------")

    context.obj["vogue_api"].load_samples(days=days)


@vogue.command("reagent-labels", short_help="Getting reagent_label data from lims.")
@click.option(
    "-d", "--days", type=int, required=True, help="load X days old sampels from lims to vogue"
)
@click.pass_context
def reagent_labels(context, days: int):
    """Loading reagent_labels from lims to the trending database"""

    LOG.info("----------------- REAGENT LABELS -----------------------")

    context.obj["vogue_api"].load_reagent_labels(days=days)


@vogue.command("bioinfo", short_help="Load bioinfo results into vogue")
@click.option(
    "-c",
    "--case-name",
    required=True,
    help="Case name or project name for which the analysis results will load",
)
@click.option(
    "--cleanup/--no-cleanup", default=False, help="Cleanup processed case data while loading"
)
@click.option(
    "-t",
    "--target-load",
    default="all",
    type=click.Choice(["all", "raw", "process"]),
    show_default=True,
    help=(
        "Final target to load bioinfo data."
        "Target orders are: all, raw, process."
        "Selecting all, will load raw, process, and sample."
        "Selecting process, will upload raw and process."
        "Selecting raw, will only load raw data."
    ),
)
@click.option("--dry/--no-dry", default=False, help="Dry run...")
@click.pass_context
def bioinfo(context, case_name, cleanup, target_load, dry):
    """Load bioinfo case results to the trending database"""

    hk_api = context.obj["housekeeper_api"]
    store = context.obj["status_db"]

    click.echo(click.style("----------------- BIOINFO -----------------------"))

    load_bioinfo_raw_inputs = dict()

    # Probably get samples for a case_name through statusdb api
    load_bioinfo_raw_inputs["samples"] = _get_samples(store, case_name)

    # Probably get analysis result file through housekeeper ai
    load_bioinfo_raw_inputs["analysis_result_file"] = _get_multiqc_latest_file(hk_api, case_name)

    # Probably get analysis_type [multiqc or microsalt or all] from cli
    # This might automated to some extend by checking if input multiqc json.
    # This tells us how the result was generated. If it is multiqc it will try to validate keys with
    # an actual model.
    load_bioinfo_raw_inputs["analysis_type"] = "multiqc"

    # case_name is the input
    load_bioinfo_raw_inputs["analysis_case_name"] = case_name

    # Get case_analysis_type from cli a free text for an entry in trending database
    load_bioinfo_raw_inputs["case_analysis_type"] = "multiqc"

    # Get workflow_name and workflow_version
    workflow_name, workflow_version = _get_analysis_workflow_details(store, case_name)
    if workflow_name not in VOGUE_VALID_BIOINFO:
        raise AnalysisUploadError(f"Case upload failed: {case_name}. Reason: Bad workflow name.")
    load_bioinfo_raw_inputs["analysis_workflow_name"] = workflow_name
    load_bioinfo_raw_inputs["analysis_workflow_version"] = workflow_version

    if dry:
        click.echo(click.style("----------------- DRY RUN -----------------------"))

    if target_load in ("raw", "all"):
        click.echo(click.style("----------------- UPLOAD UNPROCESSED -----------------------"))
        if not dry:
            context.obj["vogue_upload_api"].load_bioinfo_raw(load_bioinfo_raw_inputs)

    if target_load in ("process", "all"):
        click.echo(click.style("----------------- PROCESS CASE -----------------------"))
        if not dry:
            context.obj["vogue_upload_api"].load_bioinfo_process(load_bioinfo_raw_inputs, cleanup)
        click.echo(click.style("----------------- PROCESS SAMPLE -----------------------"))
        if not dry:
            context.obj["vogue_upload_api"].load_bioinfo_sample(load_bioinfo_raw_inputs)


@vogue.command("bioinfo-all", short_help="Load all bioinfo results into vogue")
@click.option("--dry/--no-dry", is_flag=True, help="Dry run...")
@click.pass_context
def bioinfo_all(context, dry):
    """Load all cases with recent analysis and a multiqc-json to the trending database."""

    hk_api = context.obj["housekeeper_api"]
    store = context.obj["status_db"]
    cases = store.families()
    for case in cases:
        case_name = case.internal_id
        version_obj = hk_api.last_version(case_name)
        if not version_obj:
            continue

        # confirm multiqc.json exists
        multiqc_file_obj = hk_api.get_files(
            bundle=case_name, tags=["multiqc-json"], version=version_obj.id
        )
        if len(list(multiqc_file_obj)) == 0:
            continue

        # confirm that file exists
        existing_multiqc_file = multiqc_file_obj[0].full_path
        if not Path(existing_multiqc_file).exists():
            continue

        LOG.info("Found multiqc for %s, %s", case_name, existing_multiqc_file)
        try:
            context.invoke(bioinfo, case_name=case_name, cleanup=True, target_load="all", dry=dry)
        except AnalysisUploadError:
            LOG.error("Case upload failed: %s", case_name, exc_info=True)


def _get_multiqc_latest_file(hk_api: HousekeeperAPI, case_name: str) -> str:
    """Get latest multiqc_data.json path for a case_name
    Args:
        case_name(str): onemite
    Returns:
        multiqc_data_path(str): /path/to/multiqc.json
    """
    version_obj = hk_api.last_version(case_name)
    multiqc_json_file = hk_api.get_files(
        bundle=case_name, tags=["multiqc-json"], version=version_obj.id
    )

    if len(list(multiqc_json_file)) == 0:
        raise FileNotFoundError(f"No multiqc.json was found in housekeeper for {case_name}")

    return multiqc_json_file[0].full_path


def _get_samples(store: Store, case_name: str) -> str:
    """Get a sample string for case_name
    Args:
        case_name(str): onemite
    Returns:
        sample_names(str): ACC12345,ACC45679
    """

    link_objs = get_links(store, case_name)
    sample_ids = {link_obj.sample.internal_id for link_obj in link_objs}
    return ",".join(sample_ids)


def _get_analysis_workflow_details(status_api: Store, case_name: str) -> str:
    """Get lowercase workflow name for a case_name
    Args:
        case_name(str): onemite
    Returns:
        workflow_name(str): balsamic
        workflow_version(str): v3.14.15
    """
    # Workflow that generated these results
    case_obj = status_api.family(case_name)
    workflow_name = None
    workflow_version = None
    if case_obj.analyses:
        workflow_name = case_obj.analyses[0].pipeline
        workflow_version = case_obj.analyses[0].pipeline_version

    return workflow_name.lower(), workflow_version
