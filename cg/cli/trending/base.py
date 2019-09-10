#!/usr/bin/env python
import logging

import click

LOG = logging.getLogger(__name__)

# commands
from cg.cli.trending.genotype import genotype as genotype_command 


@click.group()
def trending():
    """Load trending data into trending database"""
    
    click.echo(click.style('----------------- TRENDING -----------------------'))

    pass

trending.add_command(genotype_command)