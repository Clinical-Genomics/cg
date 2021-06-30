import logging

import click

from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.command()
@click.option("cases", "-c", multiple=True, type=int, required=True)
@click.pass_obj
def fohm(context: CGConfig, cases: list):
    pass
