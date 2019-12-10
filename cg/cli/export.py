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

    db_func = getattr(Store(context.obj["database"]), f"{table}")
    db_obj = db_func(identifier)

    if db_obj is None:
        LOG.error("%s: %s not found", identifier, table)
        context.abort()

    click.echo(db_obj.to_dict())
