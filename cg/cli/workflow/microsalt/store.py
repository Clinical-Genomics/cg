"""Click commands to store microSALT analyses"""
import logging

import click

from cg.apps.hk import HousekeeperAPI
from cg.exc import (
    AnalysisDuplicationError,
    BundleAlreadyAddedError,
    MandatoryFilesMissing,
)
from cg.meta.store.base import gather_files_and_bundle_in_housekeeper
from cg.store import Store

from cg.constants import EXIT_SUCCESS, EXIT_FAIL, Pipeline

import _io

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Store results from microSALT in housekeeper."""
    context.obj["status_db"] = Store(context.obj["database"])
    context.obj["housekeeper_api"] = HousekeeperAPI(context.obj)


@store.command()
@click.argument("config-stream", type=click.File("r"), required=False)
@click.pass_context
def analysis(context, config_stream):
    """Store a finished analysis in Housekeeper."""
    status = context.obj["status_db"]
    hk_api = context.obj["housekeeper_api"]

    if not config_stream:
        LOG.error("Please provide a config file")
        context.abort()

    try:
        new_analysis = gather_files_and_bundle_in_housekeeper(
            config_stream, hk_api, status, workflow=Pipeline.MICROSALT
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
    """Store all completed analyses"""
    microsalt_analysis_api = context.obj["microsalt_analysis_api"]
    exit_code = EXIT_SUCCESS
    for deliverables_file in microsalt_analysis_api.get_deliverables_to_store():
        try:
            context.invoke(analysis, config_stream=_io.open(deliverables_file))
        except click.Abort:
            exit_code = EXIT_FAIL
        except Exception as error:
            LOG.error("Unspecified error occurred - %s", error.__class__.__name__)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
