"""Click commands to store mip analyses"""
import logging
from pathlib import Path

import click

from cg.apps.tb import TrailblazerAPI
from cg.apps.hk import HousekeeperAPI
from cg.exc import (
    AnalysisNotFinishedError,
    AnalysisDuplicationError,
    BundleAlreadyAddedError,
    PipelineUnknownError,
    MandatoryFilesMissing,
)
from cg.meta.store.base import gather_files_and_bundle_in_housekeeper
from cg.store import Store
from cg.constants import EXIT_SUCCESS, EXIT_FAIL


LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Store results from MIP in housekeeper."""
    context.obj["status_db"] = Store(context.obj["database"])
    context.obj["trailblazer_api"] = TrailblazerAPI(context.obj)
    context.obj["housekeeper_api"] = HousekeeperAPI(context.obj)


@store.command()
@click.argument("config-stream", type=click.File("r"), required=False)
@click.pass_context
def analysis(context, config_stream):
    """Store a finished analysis in Housekeeper."""
    status = context.obj["status_db"]
    hk_api = context.obj["housekeeper_api"]

    exit_code = EXIT_SUCCESS
    if not config_stream:
        LOG.error("Provide a config file.")
        raise click.Abort

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
        LOG.error(error.message)
        exit_code = EXIT_FAIL
    except FileNotFoundError as error:
        LOG.error(f"Missing file: {error.args[0]}")
        exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort()
    status.add_commit(new_analysis)
    LOG.info("Included files in Housekeeper")


@store.command()
@click.pass_context
def completed(context):
    """Store all completed analyses."""
    hk_api = context.obj["housekeeper_api"]
    tb_api = context.obj["trailblazer_api"]

    exit_code = EXIT_SUCCESS
    for analysis_obj in tb_api.analyses(status="completed", deleted=False):
        existing_record = hk_api.version(analysis_obj.family, analysis_obj.started_at)
        if existing_record:
            LOG.info("analysis stored: %s - %s", analysis_obj.family, analysis_obj.started_at)
            continue
        LOG.info(f"storing family: {analysis_obj.family}")
        with Path(analysis_obj.config_path).open() as config_stream:
            try:
                context.invoke(analysis, config_stream=config_stream)
            except (Exception, click.Abort):
                LOG.error("case storage failed: %s", analysis_obj.family, exc_info=True)
                exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
