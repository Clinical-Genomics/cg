#!/usr/bin/env python
import click

# commands
from cg.cli.trending.genotype import genotype as genotype_command


@click.group()
def trending():
    """Load trending data into trending database"""

    click.echo(click.style('----------------- TRENDING -----------------------'))


trending.add_command(genotype_command)
