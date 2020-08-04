"""Click commands to store microSALT analyses"""
import logging
from pathlib import Path
import sys

import click

from cg.apps import hk, tb
from cg.exc import (
    AnalysisDuplicationError,
    BundleAlreadyAddedError,
    MandatoryFilesMissing,
    StoreError,
)
from cg.meta.store.microsalt import gather_files_and_bundle_in_housekeeper
from cg.store import Store

LOG = logging.getLogger(__name__)
FAIL = 1
SUCCESS = 0


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
        LOG.error("Provide a config file.")
        context.abort()

    try:
        new_analysis = gather_files_and_bundle_in_housekeeper(config_stream, hk_api, status,)
    except AnalysisDuplicationError as error:
        click.echo(click.style(error.message, fg="red"))
        context.abort()
    except BundleAlreadyAddedError as error:
        click.echo(click.style(error.message, fg="red"))
        context.abort()
    except MandatoryFilesMissing as error:
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
    _store = context.obj["db"]
    usalt = context.obj["usalt"]

    exit_code = SUCCESS
    breakpoint()
    for order in _store.orders_to_microsalt_analyze():
        LOG.info("Storing microSALT order: %s", order)
        try:
            breakpoint()
            microsalt_deliverables = Path(usalt["root"], "results", order.internal_id + ".yaml")
            exit_code = context.invoke(analysis, config_stream=microsalt_deliverables) or exit_code
        except StoreError as error:
            LOG.error("Analysis storage failed: %s", error.message)
            exit_code = FAIL

    LOG.info("Done storing microbail orders. Exit code: %s", exit_code)

    sys.exit(exit_code)
