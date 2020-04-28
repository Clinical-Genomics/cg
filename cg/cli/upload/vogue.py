"""Base command for trending"""

import logging
import click

from cg.meta.upload.vogue import UploadVogueAPI
from cg.apps import vogue as vogue_api, gt

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def vogue(context):
    """Load trending data into trending database"""

    click.echo(click.style("----------------- TRENDING -----------------------"))

    context.obj["vogue_api"] = vogue_api.VogueAPI(context.obj)
    context.obj["vogue_upload_api"] = UploadVogueAPI(
        genotype_api=gt.GenotypeAPI(context.obj),
        vogue_api=context.obj["vogue_api"],
        store=context.obj["status"],
    )


@vogue.command(
    "genotype", short_help="Getting genotype data from the genotype database."
)
@click.option(
    "-d",
    "--days",
    required="True",
    help="load X days old sampels from genotype to vogue",
)
@click.pass_context
def genotype(context, days: int):
    """Loading samples from the genotype database to the trending database"""

    click.echo(click.style("----------------- GENOTYPE -----------------------"))

    context.obj["vogue_upload_api"].load_genotype(days=days)


@vogue.command(
    "apptags", short_help="Getting application tags to the trending database."
)
@click.pass_context
def apptags(context):
    """Loading apptags from status db to the trending database"""

    click.echo(
        click.style("----------------- APPLICATION TAGS -----------------------")
    )

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
