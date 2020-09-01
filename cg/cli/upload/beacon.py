"""Code for uploading to scout via CLI"""
import datetime as dt

import click

from cg.apps import beacon as beacon_app
from cg.meta.upload.beacon import UploadBeaconApi


@click.command()
@click.argument("family_id")
@click.option("-p", "--panel", help="Gene panel to filter VCF by", required=True, multiple=True)
@click.option("-out", "--outfile", help="Name of pdf outfile", default=None)
@click.option("-cust", "--customer", help="Name of customer", default="")
@click.option("-qual", "--quality", help="Variant quality threshold", default=20)
@click.option(
    "-ref", "--genome_reference", help="Chromosome build (default=grch37)", default="grch37"
)
@click.pass_context
def beacon(
    context: click.Context,
    family_id: str,
    panel: str,
    outfile: str,
    customer: str,
    quality: int,
    genome_reference: str,
):
    """Upload variants for affected samples in a family to cgbeacon."""

    click.echo(click.style("----------------- BEACON ----------------------"))

    if outfile:
        outfile += dt.datetime.now().strftime("%Y-%m-%d_%H:%M:%S.pdf")
    api = UploadBeaconApi(
        status=context.obj["status"],
        hk_api=context.obj["housekeeper_api"],
        scout_api=context.obj["scout_api"],
        beacon_api=beacon_app.BeaconApi(context.obj),
    )
    api.upload(
        family_id=family_id,
        panel=panel,
        outfile=outfile,
        customer=customer,
        qual=quality,
        reference=genome_reference,
    )
