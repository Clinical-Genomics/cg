import logging
import click

LOG = logging.getLogger(__name__)


@click.command("genotype",
               short_help="Getting genotype data from the genotype database.")

@click.option('-d', '--days', help='load X days old sampels from genotype to vogue')
@click.pass_context
def genotype(context, days: int):
    """Adding samples from the genotype database to the trending database"""

    click.echo(click.style('----------------- GENOTYPE -----------------------'))

    vogue_upload_api = context.obj['vogue_upload_api']
    vogue_upload_api.load_genotype(days=days)
