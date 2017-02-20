# -*- coding: utf-8 -*-
import click
import click_completion
import crayons
import ruamel.yaml

from .version import __version__
from . import scoutold as scoutold_api
from . import scout as scout_api

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


@cli.command()
@click.option('--source', '-s', type=click.Choice(['prod', 'archive']), default='prod')
@click.pass_context
def reruns(context, source='prod'):
    """Return reruns marked in Scout (old)."""
    scout_db = scout_api.connect(context.obj)
    if source == 'prod':
        for scout_case in scout_api.get_reruns(scout_db):
            click.echo(scout_case['_id'])

    elif source == 'archive':
        scoutold_db = scoutold_api.connect(context.obj)
        for scout_case in scoutold_api.get_reruns(scoutold_db):
            case_id = scout_case['_id'].replace('_', '-', 1)
            # lookup requested case in current Scout
            if scout_api.get_case(scout_db, case_id):
                pass
            else:
                click.echo(case_id)
