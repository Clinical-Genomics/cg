"""CLI options for Nextflow and NF-Tower."""

import logging

import click
from pydantic import ValidationError

from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.constants import MetaApis, DRY_RUN
from cg.exc import AnalysisNotReadyError, CgError, HousekeeperStoreError
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)

OPTION_WORKDIR = click.option(
    "--work-dir",
    type=click.Path(),
    help="Directory where intermediate result files are stored",
)
OPTION_RESUME = click.option(
    "--resume",
    is_flag=True,
    default=False,
    show_default=True,
    help="Execute the script using the cached results, useful to continue \
        executions that was stopped by an error",
)
OPTION_PROFILE = click.option(
    "--profile",
    type=str,
    show_default=True,
    help="Choose a configuration profile",
)

OPTION_LOG = click.option(
    "--log",
    type=click.Path(),
    help="Set nextflow log file path",
)

OPTION_CONFIG = click.option(
    "--config",
    type=click.Path(),
    help="Nextflow config file path",
)

OPTION_PARAMS_FILE = click.option(
    "--params-file",
    type=click.Path(),
    help="Nextflow workflow-specific parameter file path",
)

OPTION_USE_NEXTFLOW = click.option(
    "--use-nextflow",
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Execute workflow using nextflow",
)

OPTION_REVISION = click.option(
    "--revision",
    type=str,
    help="Revision of workflow to run (either a git branch, tag or commit SHA number)",
)
OPTION_COMPUTE_ENV = click.option(
    "--compute-env",
    type=str,
    help="Compute environment name. If not specified the primary compute environment will be used.",
)
OPTION_TOWER_RUN_ID = click.option(
    "--nf-tower-id",
    type=str,
    is_flag=False,
    default=None,
    help="NF-Tower ID of run to relaunch. If not provided the latest NF-Tower ID for a case will be used.",
)
OPTION_FROM_START = click.option(
    "--from-start",
    is_flag=True,
    default=False,
    show_default=True,
    help="Start workflow from start without resuming execution",
)


@click.command("config-case")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def config_case(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Create config files required by a workflow for a case."""
    analysis_api: NfAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.config_case(case_id=case_id, dry_run=dry_run)
    except (CgError, ValidationError) as error:
        LOG.error(f"Could not create config files for {case_id}: {error}")
        raise click.Abort() from error


@click.command("run")
@ARGUMENT_CASE_ID
@OPTION_LOG
@OPTION_WORKDIR
@OPTION_FROM_START
@OPTION_PROFILE
@OPTION_CONFIG
@OPTION_PARAMS_FILE
@OPTION_REVISION
@OPTION_COMPUTE_ENV
@OPTION_USE_NEXTFLOW
@OPTION_TOWER_RUN_ID
@DRY_RUN
@click.pass_obj
def run(
    context: CGConfig,
    case_id: str,
    log: str,
    work_dir: str,
    from_start: bool,
    profile: str,
    config: str,
    params_file: str,
    revision: str,
    compute_env: str,
    use_nextflow: bool,
    nf_tower_id: str | None,
    dry_run: bool,
) -> None:
    """Run analysis for a case."""
    analysis_api: NfAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.run_nextflow_analysis(
            case_id=case_id,
            dry_run=dry_run,
            log=log,
            work_dir=work_dir,
            from_start=from_start,
            profile=profile,
            config=config,
            params_file=params_file,
            revision=revision,
            compute_env=compute_env,
            use_nextflow=use_nextflow,
            nf_tower_id=nf_tower_id,
        )
    except Exception as error:
        LOG.error(f"Unspecified error occurred: {error}")
        raise click.Abort() from error


@click.command("start")
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
@click.pass_obj
def start(
    context: CGConfig,
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
    """Start workflow for a case."""
    LOG.info(f"Starting analysis for {case_id}")
    analysis_api: NfAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        analysis_api.prepare_fastq_files(case_id=case_id, dry_run=dry_run)
        analysis_api.config_case(case_id=case_id, dry_run=dry_run)
        analysis_api.run_nextflow_analysis(
            case_id=case_id,
            dry_run=dry_run,
            log=log,
            work_dir=work_dir,
            from_start=True,
            profile=profile,
            config=config,
            params_file=params_file,
            revision=revision,
            compute_env=compute_env,
            use_nextflow=use_nextflow,
        )
    except Exception as error:
        LOG.error(f"Unexpected error occurred: {error}")
        raise click.Abort from error


@click.command("start-available")
@DRY_RUN
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False) -> None:
    """Start workflow for all cases ready for analysis."""
    analysis_api: NfAnalysisAPI = context.obj.meta_apis[MetaApis.ANALYSIS_API]
    exit_code: int = EXIT_SUCCESS
    for case in analysis_api.get_cases_ready_for_analysis():
        try:
            context.invoke(start, case_id=case.internal_id, dry_run=dry_run)
        except AnalysisNotReadyError as error:
            LOG.error(error)
        except Exception as error:
            LOG.error(error)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


@click.command("metrics-deliver")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def metrics_deliver(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Create and validate a metrics deliverables file for given case id.
    If QC metrics are met it sets the status in Trailblazer to complete.
    If failed, it sets it as failed and adds a comment with information of the failed metrics."""
    analysis_api: NfAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.metrics_deliver(case_id=case_id, dry_run=dry_run)
    except CgError as error:
        raise click.Abort() from error


@click.command("report-deliver")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def report_deliver(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Create a Housekeeper deliverables file for given case id."""
    analysis_api: NfAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.report_deliver(case_id=case_id, dry_run=dry_run)
    except CgError as error:
        LOG.error(f"Could not create report file: {error}")
        raise click.Abort()


@click.command("store-housekeeper")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def store_housekeeper(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Store a finished nf-analysis in Housekeeper and StatusDB."""
    analysis_api: NfAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.store_analysis_housekeeper(case_id=case_id, dry_run=dry_run)
    except HousekeeperStoreError as error:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {error}!")
        raise click.Abort()


@click.command("store")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_context
def store(context: click.Context, case_id: str, dry_run: bool) -> None:
    """Generate deliverable files for a case and store in Housekeeper if they
    pass QC metrics checks."""
    analysis_api: NfAnalysisAPI = context.obj.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.store(case_id=case_id, dry_run=dry_run)
    except Exception as error:
        LOG.error(repr(error))
        raise click.Abort()


@click.command("store-available")
@DRY_RUN
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """Store cases that are ready to be stored.
    The condition to be store: cases that are set as running in StatusDB and as completed or qc in Trailblazer.
    """

    analysis_api: NfAnalysisAPI = context.obj.meta_apis[MetaApis.ANALYSIS_API]

    exit_code: int = EXIT_SUCCESS

    for case in analysis_api.get_cases_to_store():
        LOG.info(f"Storing deliverables for {case.internal_id}")
        try:
            analysis_api.store(case_id=case.internal_id, dry_run=dry_run)
        except Exception as error:
            LOG.error(f"Error storing {case.internal_id}: {repr(error)}")
            exit_code: int = EXIT_FAIL
    if exit_code:
        raise click.Abort
