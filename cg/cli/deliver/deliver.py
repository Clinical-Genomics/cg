# -*- coding: utf-8 -*- import logging

import click

from .mip_dna import mip_dna


@click.group()
def deliver():
    """Deliver for a pipeline"""


deliver.add_command(mip_dna)
