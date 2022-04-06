"""Common CLI file generation functions"""

import click


from .mip_dna.base import mip_dna


@click.group()
def generate():
    """Generates and/or modifies files"""


generate.add_command(mip_dna)
