"""Base command for trending"""

import click
from cg.cli.trending.genotype import genotype as genotype_command
from cg.cli.trending.apptags import apptags as apptags_command


@click.group()
def trending():
    """Load trending data into trending database"""

    click.echo(click.style('----------------- TRENDING -----------------------'))


trending.add_command(genotype_command)
trending.add_command(apptags_command)
