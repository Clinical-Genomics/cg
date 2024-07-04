""" Start of CLI """

import logging
import sys
from pathlib import Path

import click
import coloredlogs
from sqlalchemy.orm import scoped_session

import cg
from cg.cli.sequencing_qc.sequencing_qc import sequencing_qc
from cg.cli.validate import validate
from cg.cli.add import add as add_cmd
from cg.cli.archive import archive
from cg.cli.backup import backup
from cg.cli.clean import clean
from cg.cli.compress.base import compress, decompress
from cg.cli.delete.base import delete
from cg.cli.deliver.base import deliver as deliver_cmd
from cg.cli.demultiplex.base import demultiplex_cmd_group as demultiplex_cmd
from cg.cli.downsample import downsample
from cg.cli.generate.base import generate as generate_cmd
from cg.cli.get import get
from cg.cli.set.base import set_cmd
from cg.cli.store.base import store as store_cmd
from cg.cli.transfer import transfer_group
from cg.cli.upload.base import upload
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.validate import validate
from cg.cli.workflow.base import workflow as workflow_cmd
from cg.constants.cli_options import FORCE
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.models.cg_config import CGConfig
from cg.store.database import (
    create_all_tables,
    drop_all_tables,
    get_scoped_session_registry,
    get_tables,
)

LOG = logging.getLogger(__name__)
LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]


def teardown_session():
    """Ensure that the session is closed and all resources are released to the connection pool."""
    registry: scoped_session | None = get_scoped_session_registry()
    if registry:
        registry.remove()


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
@click.option("-c", "--config", type=click.Path(exists=True), help="path to config file")
@click.option("-d", "--database", help="path/URI of the SQL database")
@click.option(
    "-l", "--log-level", type=click.Choice(LEVELS), default="INFO", help="lowest level to log at"
)
@click.option("--verbose", is_flag=True, help="Show full log information, time stamp etc")
@click.version_option(cg.__version__, prog_name=cg.__title__)
@click.pass_context
def base(
    context: click.Context,
    config: click.Path,
    database: str | None,
    log_level: str,
    verbose: bool,
):
    """cg - interface between tools at Clinical Genomics."""
    if verbose:
        log_format = "%(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s"
    else:
        log_format = "%(message)s" if sys.stdout.isatty() else None

    coloredlogs.install(level=log_level, fmt=log_format)
    raw_config: dict = (
        ReadFile.get_content_from_file(file_format=FileFormat.YAML, file_path=Path(config))
        if config
        else {"database": database}
    )
    context.obj = CGConfig(**raw_config)
    context.call_on_close(teardown_session)


@base.command()
@click.option("--reset", is_flag=True, help="Reset database before setting up tables")
@FORCE
@click.pass_obj
def init(context: CGConfig, reset: bool, force: bool):
    """Setup the database."""
    existing_tables: list[str] = get_tables()
    if force or reset:
        if existing_tables and not force:
            message = f"Delete existing tables? [{', '.join(existing_tables)}]"
            click.confirm(click.style(message, fg="yellow"), abort=True)
        drop_all_tables()
    elif existing_tables:
        LOG.error("Database already exists, use '--reset'")
        raise click.Abort

    create_all_tables()
    LOG.info(f"Success! New tables: {', '.join(get_tables())}")


base.add_command(add_cmd)
base.add_command(archive)
base.add_command(backup)
base.add_command(clean)
base.add_command(compress)
base.add_command(decompress)
base.add_command(delete)
base.add_command(get)
base.add_command(set_cmd)
base.add_command(transfer_group)
base.add_command(upload)
base.add_command(workflow_cmd)
base.add_command(store_cmd)
base.add_command(deliver_cmd)
base.add_command(demultiplex_cmd)
base.add_command(generate_cmd)
base.add_command(downsample)
base.add_command(validate)
base.add_command(sequencing_qc)
