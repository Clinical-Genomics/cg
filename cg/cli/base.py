"""Start of CLI with lazy loading and local imports."""

import logging
import sys
from pathlib import Path

import click
import coloredlogs
from sqlalchemy.orm import scoped_session

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


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("-c", "--config", type=click.Path(exists=True), help="Path to config file")
@click.option("-d", "--database", help="Path/URI of the SQL database")
@click.option(
    "-l", "--log-level", type=click.Choice(LEVELS), default="INFO", help="Lowest level to log at"
)
@click.option("--verbose", is_flag=True, help="Show full log information, time stamp, etc.")
@click.version_option("1.0", prog_name="cg")
@click.pass_context
def base(context: click.Context, config: Path, database: str | None, log_level: str, verbose: bool):
    """cg - Interface between tools at Clinical Genomics."""
    if verbose:
        log_format = "%(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s"
    else:
        log_format = "%(message)s" if sys.stdout.isatty() else None

    coloredlogs.install(level=log_level, fmt=log_format)
    raw_config = (
        ReadFile.get_content_from_file(file_format=FileFormat.YAML, file_path=config)
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


def load_command(module_name: str, command_name: str):
    """Dynamically load and add commands."""
    module = __import__(module_name, fromlist=[command_name])
    return getattr(module, command_name)


base.add_command(load_command("cg.cli.add", "add"))
base.add_command(load_command("cg.cli.archive", "archive"))
base.add_command(load_command("cg.cli.backup", "backup"))
base.add_command(load_command("cg.cli.clean", "clean"))
base.add_command(load_command("cg.cli.compress.base", "compress"))
base.add_command(load_command("cg.cli.compress.base", "decompress"))
base.add_command(load_command("cg.cli.delete.base", "delete"))
base.add_command(load_command("cg.cli.get", "get"))
base.add_command(load_command("cg.cli.set.base", "set_cmd"))
base.add_command(load_command("cg.cli.transfer", "transfer_group"))
base.add_command(load_command("cg.cli.upload.base", "upload"))
base.add_command(load_command("cg.cli.workflow.base", "workflow"))
base.add_command(load_command("cg.cli.store.base", "store"))
base.add_command(load_command("cg.cli.deliver.base", "deliver"))
base.add_command(load_command("cg.cli.demultiplex.base", "demultiplex_cmd"))
base.add_command(load_command("cg.cli.generate.base", "generate"))
base.add_command(load_command("cg.cli.downsample", "downsample"))
base.add_command(load_command("cg.cli.post_process.post_process", "post_processing"))
base.add_command(load_command("cg.cli.sequencing_qc.sequencing_qc", "sequencing_qc"))
