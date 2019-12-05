""""Base command for delivery sub commands"""
import click

from .mip_dna import mip_dna


@click.group()
def deliver():
    """Deliver for a pipeline"""


deliver.add_command(mip_dna)
