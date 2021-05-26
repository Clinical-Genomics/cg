"""Common CLI workflow functions"""


import click

from .balsamic.base import balsamic as balsamic_cmd
from .fluffy.base import fluffy
from .microsalt.base import microsalt
from .mip_dna.base import mip_dna
from .mip_rna.base import mip_rna
from .mutant.base import mutant


@click.group()
def workflow():
    """Workflows commands"""


workflow.add_command(balsamic_cmd)
workflow.add_command(microsalt)
workflow.add_command(mip_dna)
workflow.add_command(mip_rna)
workflow.add_command(fluffy)
workflow.add_command(mutant)
