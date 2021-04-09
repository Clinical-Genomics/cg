"""Functionality to export data from the database"""
import logging

import click
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.argument("table")
@click.argument("identifier")
@click.pass_context
def export(context: click.Context, table: str, identifier: str):
    """Get information about almost anything in the store."""
    status_db: Store = context.obj["status_db"]
    db_func = getattr(status_db, f"{table}")
    db_obj = db_func(identifier)

    if db_obj is None:
        LOG.error("%s: %s not found", identifier, table)
        raise click.Abort

    click.echo(db_obj.to_dict())
