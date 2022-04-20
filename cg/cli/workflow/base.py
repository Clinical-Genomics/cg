"""Common CLI workflow functions"""


import click

from .balsamic.base import balsamic
from .balsamic.umi import balsamic_umi
from .fluffy.base import fluffy
from .microsalt.base import microsalt
from .mip_dna.base import mip_dna
from .mip_rna.base import mip_rna
from .mutant.base import mutant
from .fastq.base import fastq


@click.group()
def workflow():
    """Workflows commands"""


workflow.add_command(balsamic)
workflow.add_command(balsamic_umi)
workflow.add_command(microsalt)
workflow.add_command(mip_dna)
workflow.add_command(mip_rna)
workflow.add_command(fluffy)
workflow.add_command(mutant)
workflow.add_command(fastq)
