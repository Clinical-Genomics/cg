# -*- coding: utf-8 -*-
import coloredlogs
import click
import click_completion
import crayons
import ruamel.yaml

from .version import __version__
from . import commands
from cg.invoice import invoice as invoice_cli
from cg.queue import cli as queue_cli

# enable shell completion
click_completion.init()


@click.group(invoke_without_command=True)
@click.version_option(prog_name=crayons.yellow('cg'), version=__version__)
@click.option('-h', '--help', is_flag=True, help="Show this message then exit.")
@click.option('-l', '--log-level', default='INFO')
@click.option('-c', '--config', type=click.File('r'), required=True)
@click.pass_context
def cli(context, help, log_level, config):
    """Central place for interacting with CG apps."""
    coloredlogs.install(level=log_level)
    if help:
        click.echo(context.get_help())
    context.obj = ruamel.yaml.safe_load(config)


cli.add_command(commands.mip_config)
cli.add_command(commands.reruns)
cli.add_command(commands.update)
cli.add_command(commands.check)
cli.add_command(commands.mip_config)
cli.add_command(commands.mip_panel)
cli.add_command(commands.start)
cli.add_command(queue_cli.queue)
cli.add_command(commands.coverage)
cli.add_command(commands.genotypes)
cli.add_command(commands.qc)
cli.add_command(commands.visualize)
cli.add_command(commands.delivery_report)
cli.add_command(invoice_cli)
cli.add_command(commands.add)
cli.add_command(commands.validate)
cli.add_command(commands.observations)
cli.add_command(commands.auto_start)
cli.add_command(commands.keep)
