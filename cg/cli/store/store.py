""""Base command for storing sub commands"""
import logging
import click

from .mip_dna import mip_dna

LOG = logging.getLogger(__name__)


@click.group()
def store():
    """Store results from a pipeline in housekeeper."""


store.add_command(mip_dna)
