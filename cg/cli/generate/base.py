"""Common CLI file generation functions"""

import click


from .mip_dna.base import mip_dna
from .balsamic.base import balsamic


@click.group()
def generate():
    """Generates and/or modifies files"""


generate.add_command(mip_dna)
generate.add_command(balsamic)
