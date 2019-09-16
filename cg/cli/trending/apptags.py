"""CLI to load apptags from status db to the trending database"""
import logging
import click

LOG = logging.getLogger(__name__)


@click.command("apptags",
               short_help="Getting application tags to the trending database.")
@click.pass_context
def apptags(context):
    """Loading apptags from status db to the trending database"""

    click.echo(click.style('----------------- APPLICATION TAGS -----------------------'))

    vogue_upload_api = context.obj['vogue_upload_api']
    vogue_upload_api.load_apptags()
