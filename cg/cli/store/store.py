""""Base command for storing sub commands"""
import logging
import click

from .balsamic import balsamic
from .microsalt import microsalt
from .mip_dna import mip_dna
from .mip_rna import mip_rna

LOG = logging.getLogger(__name__)


@click.group()
def store():
    """Store results from a pipeline in housekeeper."""


store.add_command(balsamic)
store.add_command(microsalt)
store.add_command(mip_dna)
store.add_command(mip_rna)
