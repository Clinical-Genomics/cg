"""Click commands to store mip analyses"""
import logging
from pathlib import Path
import sys

import click

from cg.apps import hk, tb
from cg.exc import (
    AnalysisNotFinishedError,
    AnalysisDuplicationError,
    BundleAlreadyAddedError,
    PipelineUnknownError,
    MandatoryFilesMissing,
)
from cg.meta.store.base import gather_files_and_bundle_in_housekeeper
from cg.store import Store

LOG = logging.getLogger(__name__)
FAIL = 1
SUCCESS = 0


@click.group()
@click.pass_context
def store(context):
    """Store results from MIP in housekeeper."""
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
        new_analysis = gather_files_and_bundle_in_housekeeper(
            config_stream,
            hk_api,
            status,
            workflow="mip",
        )
    except (
        AnalysisNotFinishedError,
        AnalysisDuplicationError,
        BundleAlreadyAddedError,
        PipelineUnknownError,
        MandatoryFilesMissing,
    ) as error:
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
    hk_api = context.obj["hk_api"]
    tb_api = context.obj["tb_api"]

    exit_code = SUCCESS
    for analysis_obj in tb_api.analyses(status="completed", deleted=False):
        existing_record = hk_api.version(analysis_obj.family, analysis_obj.started_at)
        if existing_record:
            LOG.debug("analysis stored: %s - %s", analysis_obj.family, analysis_obj.started_at)
            continue
        click.echo(click.style(f"storing family: {analysis_obj.family}", fg="blue"))
        with Path(analysis_obj.config_path).open() as config_stream:
            try:
                context.invoke(analysis, config_stream=config_stream)
            except Exception:
                LOG.error("case storage failed: %s", analysis_obj.family, exc_info=True)
                exit_code = FAIL

    sys.exit(exit_code)
