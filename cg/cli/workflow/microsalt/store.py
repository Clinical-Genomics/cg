"""Click commands to store microSALT analyses"""
import logging

import click

from cg.apps import hk, tb
from cg.exc import (
    AnalysisDuplicationError,
    BundleAlreadyAddedError,
    MandatoryFilesMissing,
)
from cg.meta.store.base import gather_files_and_bundle_in_housekeeper
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Store results from microSALT in housekeeper."""
    context.obj["db"] = Store(context.obj["database"])
    context.obj["tb_api"] = tb.TrailblazerAPI(context.obj)
    context.obj["hk_api"] = hk.HousekeeperAPI(context.obj)


@store.command()
@click.argument("config-stream", type=click.File("r"), required=False)
@click.pass_context
def analysis(context, config_stream):
    """Store a finished analysis in Housekeeper."""
    status = context.obj["db"]
    hk_api = context.obj["hk_api"]

    if not config_stream:
        LOG.error("Please provide a config file")
        context.abort()

    try:
        new_analysis = gather_files_and_bundle_in_housekeeper(
            config_stream, hk_api, status, workflow="microsalt"
        )
    except (AnalysisDuplicationError, BundleAlreadyAddedError, MandatoryFilesMissing) as error:
        click.echo(click.style(error.message, fg="red"))
        context.abort()
    except FileNotFoundError as error:
        click.echo(click.style(f"missing file: {error.args[0]}", fg="red"))
        context.abort()

    status.add_commit(new_analysis)
    click.echo(click.style("included files in Housekeeper", fg="green"))


@store.command()
@click.pass_context
def completed(context):
    """Store all completed analyses."""
    pass
