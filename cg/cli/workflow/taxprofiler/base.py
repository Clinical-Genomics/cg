"""CLI support to create config and/or start TAXPROFILER."""

import logging
from pathlib import Path

import click

from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.cli.workflow.taxprofiler.options import OPTION_INSTRUMENT_PLATFORM
from cg.constants.constants import MetaApis
from cg.constants.sequencing import SequencingPlatform
from cg.exc import CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig


LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def taxprofiler(context: click.Context) -> None:
    """nf-core/taxprofiler analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = TaxprofilerAnalysisAPI(
        config=context.obj,
    )


@taxprofiler.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_INSTRUMENT_PLATFORM
@click.pass_obj
def config_case(context: CGConfig, case_id: str, instrument_platform: SequencingPlatform) -> None:
    """Create sample sheet file for Taxprofiler analysis for a given case_id."""
    analysis_api: TaxprofilerAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]

    try:
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        analysis_api.config_case(case_id=case_id, instrument_platform=instrument_platform, fasta="")

    except CgError as error:
        LOG.error(f"Could not create sample sheet: {error}")
        LOG.error(f"{case_id} could not be found in StatusDB!")
        raise click.Abort() from error
