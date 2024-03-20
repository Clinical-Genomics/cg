"""CLI support to create config and/or start RNAFUSION."""

import logging

import click

from cg.cli.workflow.commands import ARGUMENT_CASE_ID, resolve_compression
from cg.cli.workflow.nf_analysis import (
    config_case,
    metrics_deliver,
    report_deliver,
    run,
    start,
    start_available,
    store_housekeeper,
)
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.constants import DRY_RUN, MetaApis
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def rnafusion(context: click.Context) -> None:
    """nf-core/rnafusion analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = RnafusionAnalysisAPI(config=context.obj)


rnafusion.add_command(resolve_compression)
rnafusion.add_command(config_case)
rnafusion.add_command(run)
rnafusion.add_command(start)
rnafusion.add_command(start_available)
rnafusion.add_command(metrics_deliver)
rnafusion.add_command(report_deliver)
rnafusion.add_command(store_housekeeper)


@rnafusion.command("store")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_context
def store(context: click.Context, case_id: str, dry_run: bool) -> None:
    """Generate deliverables files for a case and store in Housekeeper if they
    pass QC metrics checks."""
    analysis_api: RnafusionAnalysisAPI = context.obj.meta_apis[MetaApis.ANALYSIS_API]

    is_latest_analysis_qc: bool = analysis_api.trailblazer_api.is_latest_analysis_qc(
        case_id=case_id
    )
    if not is_latest_analysis_qc and not analysis_api.trailblazer_api.is_latest_analysis_completed(
        case_id=case_id
    ):
        LOG.error(
            "Case not stored. Trailblazer status must be either QC or COMPLETE to be able to store"
        )
        return

    # Avoid storing a case without QC checks previously performed
    if (
        is_latest_analysis_qc
        or not analysis_api.get_metrics_deliverables_path(case_id=case_id).exists()
    ):
        LOG.info(f"Generating metrics file and performing QC checks for {case_id}")
        context.invoke(metrics_deliver, case_id=case_id, dry_run=dry_run)
    LOG.info(f"Storing analysis for {case_id}")
    context.invoke(report_deliver, case_id=case_id, dry_run=dry_run)
    context.invoke(store_housekeeper, case_id=case_id, dry_run=dry_run)


@rnafusion.command("store-available")
@DRY_RUN
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """Store bundles for all finished RNAFUSION analyses in Housekeeper."""

    analysis_api: AnalysisAPI = context.obj.meta_apis[MetaApis.ANALYSIS_API]

    exit_code: int = EXIT_SUCCESS

    for case_obj in set([*analysis_api.get_cases_to_qc(), *analysis_api.get_cases_to_store()]):
        LOG.info(f"Storing RNAFUSION deliverables for {case_obj.internal_id}")
        try:
            context.invoke(store, case_id=case_obj.internal_id, dry_run=dry_run)
        except Exception as error:
            LOG.error(f"Error storing {case_obj.internal_id}: {error}")
            exit_code: int = EXIT_FAIL
    if exit_code:
        raise click.Abort
