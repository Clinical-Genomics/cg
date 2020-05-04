"""Base command for trending"""

import logging
import click

from cg.meta.upload.vogue import UploadVogueAPI
from cg.apps import vogue as vogue_api, gt
from cg.cli.workflow.get_links import get_links
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def vogue(context):
    """Load trending data into trending database"""

    click.echo(click.style("----------------- TRENDING -----------------------"))

    context.obj["db"] = Store(context.obj["database"])
    context.obj["vogue_api"] = vogue_api.VogueAPI(context.obj)
    context.obj["vogue_upload_api"] = UploadVogueAPI(
        genotype_api=gt.GenotypeAPI(context.obj),
        vogue_api=context.obj["vogue_api"],
        store=context.obj["status"],
    )


@vogue.command("genotype", short_help="Getting genotype data from the genotype database.")
@click.option(
    "-d", "--days", required="True", help="load X days old sampels from genotype to vogue",
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
    "-d", "--days", required="True", help="load X days old runs from lims to vogue",
)
@click.pass_context
def flowcells(context, days: int):
    """Loading runs from lims to the trending database"""

    click.echo(click.style("----------------- FLOWCELLS -----------------------"))

    context.obj["vogue_upload_api"].load_flowcells(days=days)


@vogue.command("samples", short_help="Getting sample data from lims.")
@click.option(
    "-d", "--days", required="True", help="load X days old sampels from lims to vogue",
)
@click.pass_context
def samples(context, days: int):
    """Loading samples from lims to the trending database"""

    click.echo(click.style("----------------- SAMPLES -----------------------"))

    context.obj["vogue_upload_api"].load_samples(days=days)


@vogue.command("bioinfo", short_help="Load bioinfo results into vogue")
@click.option(
    "-c",
    "--case-name",
    required=True,
    help="Case name or project name for which the analysis results will load",
)
@click.option(
    "--cleanup/--no-cleanup", default=False, help="Cleanup processed case data while loading",
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
@click.pass_context
def bioinfo(context, case_name, cleanup, target_load):
    """Load bioinfo case results to the trending database"""

    click.echo(click.style("----------------- BIOINFO -----------------------"))

    load_bioinfo_raw_inputs = dict()
    
    
    # Probably get samples for a case_name through statusdb api
    load_bioinfo_raw_inputs["samples"] = _get_samples(context, case_name)

    # Probably get analysis result file through housekeeper ai
    load_bioinfo_raw_inputs["analysis_result_file"] = _get_analysis_result_file(case_name)

#    # Probably get analysis_type [multiqc or microsalt or all] from cli
#    # This might automated to some extend by checking if input multiqc json.
#    # This tells us how the result was generated. If it is multiqc it will try to validate keys with 
#    # an actual model.
#    load_bioinfo_raw_inputs["analysis_type"] = get_analysis_type(case_name)
#
#    # case_name is the input
#    load_bioinfo_raw_inputs["analysis_case_name"] = case_name
#
#    # Get workflow version from where!?
#    load_bioinfo_raw_inputs["analysis_workflow_version"] = get_analysis_worfklow_version(case_name)
#
#    # Get case_analysis_type from cli a free text for an entry in trending database
#    load_bioinfo_raw_inputs["case_analysis_type"] = get_case_analysis_type(case_name)
#
    # Workflow that generated these results
    load_bioinfo_raw_inputs["analysis_workflow_name"] = _get_analysis_workflow_name(context, case_name)

    print(load_bioinfo_raw_inputs)

def _get_samples(context, case_name):
    """Get a sample string for case_name
       Args:
           case_name(str): onemite
       Returns:
           sample_names(str): ACC12345,ACC45679
    """
    
    link_objs = get_links(context, case_name, sample_id=False)
    sample_ids = set()
    for link_obj in link_objs:
        if link_obj.sample.delivered_at is not None:
            sample_ids.add(link_obj.sample.internal_id)
    return ",".join(sample_ids)

def _get_analysis_result_file(case_name):
    """Get the analysis file for a tag and a case_name 
       Args:
           case_name(str): onemite
       Returns:
           result_file(str): /path/to/multiqc.json
    """

    return 'path/result/multiqc.json'


def _get_analysis_workflow_name(context, case_name):
    """Get lowercase workflow name for a case_name
       Args:
           case_name(str): onemite
       Returns:
           workflow_name(str): balsamic 
    """
    #TODO: check if sample has two data_analysis assigned
    link_objs = get_links(context, case_name, sample_id=False)
    data_analysis = set()
    for link_obj in link_objs:
        if link_obj.sample.delivered_at is not None:
            data_analysis.add(link_obj.sample.data_analysis)
    
    return data_analysis
