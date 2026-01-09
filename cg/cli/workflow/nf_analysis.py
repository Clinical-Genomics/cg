"""CLI options for Nextflow and NF-Tower."""

import logging

import rich_click as click

from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.cli.workflow.utils import validate_force_store_option
from cg.constants.cli_options import COMMENT, DRY_RUN, FORCE
from cg.constants.constants import MetaApis
from cg.exc import CgError, HousekeeperStoreError
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


OPTION_RESUME = click.option(
    "--resume",
    default=True,
    show_default=True,
    help="Execute the script using the cached results, useful to continue "
    "executions that were stopped by an error",
)
OPTION_REVISION = click.option(
    "--revision",
    type=str,
    help="Revision of workflow to run (either a git branch, tag or commit SHA number)",
)


@click.command("metrics-deliver")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def metrics_deliver(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """
    Create and validate a metrics deliverables file for given case id.
    If QC metrics are met it sets the status in Trailblazer to complete.
    If failed, it sets it as failed and adds a comment with information of the failed metrics.
    """
    analysis_api: NfAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.metrics_deliver(case_id=case_id, dry_run=dry_run)
    except CgError as error:
        raise click.Abort() from error


@click.command("report-deliver")
@ARGUMENT_CASE_ID
@DRY_RUN
@FORCE
@click.pass_obj
def report_deliver(context: CGConfig, case_id: str, dry_run: bool, force: bool) -> None:
    """
    Create a Housekeeper deliverables file for a given case ID.

    Raises:
        click.Abort: If an error occurs during the deliverables report generation or validation.
    """
    analysis_api: NfAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.report_deliver(case_id=case_id, dry_run=dry_run, force=force)
    except CgError as error:
        LOG.error(f"Could not create report file: {error}")
        raise click.Abort()


@click.command("store-housekeeper")
@ARGUMENT_CASE_ID
@DRY_RUN
@FORCE
@click.pass_obj
def store_housekeeper(context: CGConfig, case_id: str, dry_run: bool, force: bool) -> None:
    """
    Store a finished NF-analysis in Housekeeper.

    Raises:
        click.Abort: If an error occurs while storing a case bundle in Housekeeper.
    """
    analysis_api: NfAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.store_analysis_housekeeper(case_id=case_id, dry_run=dry_run, force=force)
    except HousekeeperStoreError as error:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {error}!")
        raise click.Abort()


@click.command("store")
@ARGUMENT_CASE_ID
@COMMENT
@DRY_RUN
@FORCE
@click.pass_context
def store(
    context: click.Context, case_id: str, comment: str | None, dry_run: bool, force: bool
) -> None:
    """
    Store deliverable files in Housekeeper after meeting QC metrics criteria.

    Raises:
        click.Abort: If an error occurs during the deliverables file generation, metrics
        validation, or storage processes.
    """
    validate_force_store_option(force=force, comment=comment)
    analysis_api: NfAnalysisAPI = context.obj.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.store(case_id=case_id, comment=comment, dry_run=dry_run, force=force)
    except Exception as error:
        LOG.error(repr(error))
        raise click.Abort()


@click.command("store-available")
@DRY_RUN
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """
    Store finished analyses for cases marked as running in StatusDB and completed or QC in Trailblazer.

    Raises:
        click.Abort: If any error occurs during the storage process.
    """

    analysis_api: NfAnalysisAPI = context.obj.meta_apis[MetaApis.ANALYSIS_API]
    was_successful: bool = True
    for case in analysis_api.get_cases_to_store():
        LOG.info(f"Storing deliverables for {case.internal_id}")
        try:
            analysis_api.store(case_id=case.internal_id, dry_run=dry_run)
        except Exception as error:
            LOG.error(f"Error storing {case.internal_id}: {repr(error)}")
            was_successful = False
    if not was_successful:
        raise click.Abort()
