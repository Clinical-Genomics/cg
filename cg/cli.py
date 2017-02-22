# -*- coding: utf-8 -*-
import click
import click_completion
import crayons
import ruamel.yaml

from .version import __version__
from . import commands

# enable shell completion
click_completion.init()


@click.group(invoke_without_command=True)
@click.version_option(prog_name=crayons.yellow('cg'), version=__version__)
@click.option('-h', '--help', is_flag=True, help="Show this message then exit.")
@click.argument('config', type=click.File('r'))
@click.pass_context
def cli(context, config, help=False):
    """Central place for interacting with CG apps."""
    if help:
        click.echo(context.get_help())
    context.obj = ruamel.yaml.safe_load(config)


cli.add_command(commands.mip_config)
cli.add_command(commands.reruns)
