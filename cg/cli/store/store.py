# -*- coding: utf-8 -*-
import logging
import click

from .mip_dna import mip_dna

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Store results from MIP in housekeeper."""
    pass


store.add_command(mip_dna)
