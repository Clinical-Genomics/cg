"""CLI support to create config and/or start RAREDISEASE."""

import logging

import click
from pydantic.v1 import ValidationError

from cg.constants.constants import DRY_RUN, MetaApis
from cg.meta.workflow.analysis import AnalysisAPI
from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.exc import CgError

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def raredisease(context: click.Context) -> None:
    """nf-core/raredisease analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = RarediseaseAnalysisAPI(
        config=context.obj,
    )


@raredisease.command("config-case")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def config_case(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Create sample sheet file and params file for a given case."""
    analysis_api: RarediseaseAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    LOG.info(f"Creating config files for {case_id}.")
    try:
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        analysis_api.config_case(case_id=case_id, dry_run=dry_run)
    except (CgError, ValidationError) as error:
        LOG.error(f"Could not create config files for {case_id}: {error}")
        raise click.Abort() from error
