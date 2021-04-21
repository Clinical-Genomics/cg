""" Start of CLI """
import logging
import sys
from typing import Optional

import cg
import click
import coloredlogs
import ruamel.yaml
from cg.cli.delete.base import delete
from cg.cli.set.base import set_cmd
from cg.cli.store.store import store as store_cmd
from cg.models.cg_config import CGConfig
from cg.store import Store

from .add import add as add_cmd
from .backup import backup
from .clean import clean
from .compress.base import compress, decompress
from .deliver.base import deliver as deliver_cmd
from .demultiplex.base import demultiplex as demultiplex_cmd
from .deploy.base import deploy as deploy_cmd
from .export import export
from .get import get
from .import_cmd import import_cmd
from .reset import reset_cmd
from .status import status
from .transfer import transfer_group
from .upload.base import upload
from .workflow.base import workflow as workflow_cmd

LOG = logging.getLogger(__name__)
LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]


@click.group()
@click.option("-c", "--config", type=click.File(), help="path to config file")
@click.option("-d", "--database", help="path/URI of the SQL database")
@click.option(
    "-l", "--log-level", type=click.Choice(LEVELS), default="INFO", help="lowest level to log at"
)
@click.option("--verbose", is_flag=True, help="Show full log information, time stamp etc")
@click.version_option(cg.__version__, prog_name=cg.__title__)
@click.pass_context
def base(
    context: click.Context,
    config: click.File,
    database: Optional[str],
    log_level: str,
    verbose: bool,
):
    """cg - interface between tools at Clinical Genomics."""
    if verbose:
        log_format = "%(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s"
    else:
        log_format = "%(message)s" if sys.stdout.isatty() else None

    coloredlogs.install(level=log_level, fmt=log_format)
    raw_configs: dict = ruamel.yaml.safe_load(config) if config else {"database": database}
    context.obj = CGConfig(**raw_configs)


@base.command()
@click.option("--reset", is_flag=True, help="reset database before setting up tables")
@click.option("--force", is_flag=True, help="bypass manual confirmations")
@click.pass_obj
def init(context: CGConfig, reset: bool, force: bool):
    """Setup the database."""
    status_db: Store = context.status_db
    existing_tables = status_db.engine.table_names()
    if force or reset:
        if existing_tables and not force:
            message = f"Delete existing tables? [{', '.join(existing_tables)}]"
            click.confirm(click.style(message, fg="yellow"), abort=True)
        status_db.drop_all()
    elif existing_tables:
        LOG.error("Database already exists, use '--reset'")
        raise click.Abort

    status_db.create_all()
    LOG.info("Success! New tables: %s", ", ".join(status_db.engine.table_names()))


base.add_command(add_cmd)
base.add_command(backup)
base.add_command(clean)
base.add_command(compress)
base.add_command(decompress)
base.add_command(delete)
base.add_command(export)
base.add_command(get)
base.add_command(import_cmd)
base.add_command(reset_cmd)
base.add_command(set_cmd)
base.add_command(status)
base.add_command(transfer_group)
base.add_command(upload)
base.add_command(workflow_cmd)
base.add_command(store_cmd)
base.add_command(deploy_cmd)
base.add_command(deliver_cmd)
base.add_command(demultiplex_cmd)
