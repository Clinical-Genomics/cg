"""Click commands to store mip analyses"""
import logging
from pathlib import Path

import click
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Pipeline
from cg.exc import (
    AnalysisDuplicationError,
    AnalysisNotFinishedError,
    BundleAlreadyAddedError,
    MandatoryFilesMissing,
    PipelineUnknownError,
)
from cg.meta.store.base import gather_files_and_bundle_in_housekeeper
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_obj
def store(context: CGConfig):
    """Store results from MIP in housekeeper"""

    context.meta_apis["analysis_api"] = MipDNAAnalysisAPI(context)


@store.command()
@click.argument("config-stream", type=click.File("r"), required=False)
@click.pass_obj
def analysis(context: CGConfig, config_stream):
    """Store a finished analysis in Housekeeper"""

    analysis_api: MipDNAAnalysisAPI = context.meta_apis["analysis_api"]

    exit_code = EXIT_SUCCESS
    if not config_stream:
        LOG.error("Provide a config file.")
        raise click.Abort

    try:
        new_analysis = gather_files_and_bundle_in_housekeeper(
            config_stream=config_stream,
            hk_api=analysis_api.housekeeper_api,
            status=analysis_api.status_db,
            workflow=Pipeline.MIP_DNA,
        )
        analysis_api.status_db.add_commit(new_analysis)
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
        LOG.error(f"Missing file: {error}")
        exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort

    LOG.info("Included files in Housekeeper")


@store.command()
@click.pass_context
def completed(context: click.Context):
    """Store all completed analyses"""

    analysis_api: MipAnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code = EXIT_SUCCESS
    for case_obj in analysis_api.status_db.cases_to_store(pipeline=Pipeline.MIP_DNA):
        try:
            analysis_obj: TrailblazerAnalysis = analysis_api.trailblazer_api.get_latest_analysis(
                case_id=case_obj.internal_id
            )
            if analysis_obj.status != "completed":
                continue
            LOG.info(f"Storing case: {analysis_obj.family}")
            with Path(
                analysis_api.get_case_config_path(case_id=case_obj.internal_id)
            ).open() as config_stream:

                context.invoke(analysis, config_stream=config_stream)
        except (Exception, click.Abort) as error:
            LOG.error(f"Case storage failed: {case_obj.internal_id}, {error}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
