# -*- coding: utf-8 -*- import logging

import click

from .mip_dna import mip_dna


@click.group()
@click.pass_context
def deliver(context):
    """Deliver stuff."""
    pass


deliver.add_command(mip_dna)
