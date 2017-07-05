import click
import coloredlogs
import ruamel.yaml

import cg

from .analyze import analyze
from .store import store


@click.group()
@click.option('-c', '--config', type=click.File())
@click.option('-d', '--database', help='path/URI of the SQL database')
@click.option('-l', '--log-level', default='INFO')
@click.version_option(cg.__version__, prog_name=cg.__title__)
@click.pass_context
def base(context, config, database, log_level):
    """Housekeeper - Access your files!"""
    coloredlogs.install(level=log_level)
    context.obj = ruamel.yaml.safe_load(config) if config else {}
    if database:
        context.obj['database'] = database


base.add_command(analyze)
base.add_command(store)
