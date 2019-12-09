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

    click.echo(click.style('----------------- TRENDING -----------------------'))

    context.obj['vogue_api'] = vogue_api.VogueAPI(context.obj)


@vogue.command("genotype",
               short_help="Getting genotype data from the genotype database.")
@click.option('-d', '--days', required='True',
              help='load X days old sampels from genotype to vogue')
@click.pass_context
def genotype(context, days: int):
    """Loading samples from the genotype database to the trending database"""

    click.echo(click.style('----------------- GENOTYPE -----------------------'))

    vogue_upload_api = UploadVogueAPI(genotype_api=gt.GenotypeAPI(context.obj),
                                      vogue_api=context.obj['vogue_api'])

    vogue_upload_api.load_genotype(days=days)
