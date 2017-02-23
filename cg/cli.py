# -*- coding: utf-8 -*-
import logging

import click
import click_completion
import crayons
import ruamel.yaml

from .log import init_log
from .version import __version__
from . import commands

# enable shell completion
click_completion.init()


@click.group(invoke_without_command=True)
@click.version_option(prog_name=crayons.yellow('cg'), version=__version__)
@click.option('-h', '--help', is_flag=True, help="Show this message then exit.")
@click.option('-l', '--log-level', default='INFO')
@click.option('--log-file', type=click.Path())
@click.option('-c', '--config', type=click.File('r'), required=True)
@click.pass_context
def cli(context, help, log_level, log_file, config):
    """Central place for interacting with CG apps."""
    init_log(logging.getLogger(), loglevel=log_level, filename=log_file)

    if help:
        click.echo(context.get_help())
    context.obj = ruamel.yaml.safe_load(config)


cli.add_command(commands.mip_config)
cli.add_command(commands.reruns)
cli.add_command(commands.update)
