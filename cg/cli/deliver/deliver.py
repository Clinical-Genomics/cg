""""Base command for delivery sub commands"""
import click

from .balsamic import balsamic
from .microsalt import microsalt
from .mip_dna import mip_dna
from .mip_rna import mip_rna


@click.group()
def deliver():
    """Deliver for a pipeline"""


deliver.add_command(balsamic)
deliver.add_command(microsalt)
deliver.add_command(mip_dna)
deliver.add_command(mip_rna)
