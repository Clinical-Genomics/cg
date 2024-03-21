"""CLI support to create config and/or start RNAFUSION."""

import logging
from pathlib import Path

import click

from cg.cli.workflow.commands import ARGUMENT_CASE_ID, resolve_compression
from cg.cli.workflow.nf_analysis import (
    OPTION_COMPUTE_ENV,
    OPTION_CONFIG,
    OPTION_LOG,
    OPTION_PARAMS_FILE,
    OPTION_PROFILE,
    OPTION_REVISION,
    OPTION_USE_NEXTFLOW,
    OPTION_WORKDIR,
    config_case,
    metrics_deliver,
    report_deliver,
    run,
    store_housekeeper,
)
from cg.cli.workflow.rnafusion.options import OPTION_REFERENCES
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.constants import DRY_RUN, MetaApis
from cg.exc import AnalysisNotReadyError, CgError
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


@rnafusion.command("start")
@ARGUMENT_CASE_ID
@OPTION_LOG
@OPTION_WORKDIR
@OPTION_PROFILE
@OPTION_CONFIG
@OPTION_PARAMS_FILE
@OPTION_REVISION
@OPTION_COMPUTE_ENV
@OPTION_USE_NEXTFLOW
@DRY_RUN
@click.pass_context
def start(
    context: click.Context,
    case_id: str,
    log: str,
    work_dir: str,
    profile: str,
    config: str,
    params_file: str,
    revision: str,
    compute_env: str,
    use_nextflow: bool,
    dry_run: bool,
) -> None:
    """Start full workflow for CASE ID."""
    LOG.info(f"Starting analysis for {case_id}")

    analysis_api: RnafusionAnalysisAPI = context.obj.meta_apis["analysis_api"]
    analysis_api.prepare_fastq_files(case_id=case_id, dry_run=dry_run)
    context.invoke(config_case, case_id=case_id, dry_run=dry_run)
    context.invoke(
        run,
        case_id=case_id,
        log=log,
        work_dir=work_dir,
        from_start=True,
        profile=profile,
        config=config,
        params_file=params_file,
        revision=revision,
        compute_env=compute_env,
        use_nextflow=use_nextflow,
        dry_run=dry_run,
    )


@rnafusion.command("start-available")
@DRY_RUN
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False) -> None:
    """Start full workflow for all cases ready for analysis."""

    analysis_api: AnalysisAPI = context.obj.meta_apis[MetaApis.ANALYSIS_API]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_analyze():
        try:
            context.invoke(start, case_id=case_obj.internal_id, dry_run=dry_run)
        except AnalysisNotReadyError as error:
            LOG.error(error)
        except CgError as error:
            LOG.error(error)
            exit_code = EXIT_FAIL
        except Exception as error:
            LOG.error(f"Unspecified error occurred: {error}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


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
