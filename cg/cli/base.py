import click
import coloredlogs
import ruamel.yaml

import cg
from cg.store import Store

from .analysis import analysis
from .store import store
from .add import add
from .upload import upload
from .status import status
from .transfer import transfer


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


@base.command()
@click.option('--reset', is_flag=True, help='reset database before setting up tables')
@click.option('--force', is_flag=True, help='bypass manual confirmations')
@click.pass_context
def init(context, reset, force):
    """Setup the database."""
    db = Store(context.obj['database'])
    existing_tables = db.engine.table_names()
    if force or reset:
        if existing_tables and not force:
            message = f"Delete existing tables? [{', '.join(existing_tables)}]"
            click.confirm(click.style(message, fg='yellow'), abort=True)
        db.drop_all()
    elif existing_tables:
        click.echo(click.style("Database already exists, use '--reset'", fg='red'))
        context.abort()

    db.create_all()
    message = f"Success! New tables: {', '.join(db.engine.table_names())}"
    click.echo(click.style(message, fg='green'))


base.add_command(analysis)
base.add_command(store)
base.add_command(add)
base.add_command(upload)
base.add_command(status)
base.add_command(transfer)
