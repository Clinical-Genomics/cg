"""CLI support to create config and/or start TAXPROFILER."""

import logging

import click
from pydantic.v1 import ValidationError

from cg.cli.workflow.commands import ARGUMENT_CASE_ID, resolve_compression
from cg.cli.workflow.nf_analysis import (
    OPTION_COMPUTE_ENV,
    OPTION_CONFIG,
    OPTION_LOG,
    OPTION_PARAMS_FILE,
    OPTION_PROFILE,
    OPTION_REVISION,
    OPTION_TOWER_RUN_ID,
    OPTION_USE_NEXTFLOW,
    OPTION_WORKDIR,
)
from cg.cli.workflow.taxprofiler.options import (
    OPTION_FROM_START,
    OPTION_INSTRUMENT_PLATFORM,
)
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.constants import DRY_RUN, CaseActions, MetaApis
from cg.constants.nf_analysis import NfTowerStatus
from cg.constants.sequencing import SequencingPlatform
from cg.exc import CgError, DecompressionNeededError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.rnafusion.rnafusion import CommandArgs

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def taxprofiler(context: click.Context) -> None:
    """nf-core/taxprofiler analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = TaxprofilerAnalysisAPI(
        config=context.obj,
    )


taxprofiler.add_command(resolve_compression)


@taxprofiler.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_INSTRUMENT_PLATFORM
@DRY_RUN
@click.pass_obj
def config_case(
    context: CGConfig, case_id: str, instrument_platform: SequencingPlatform, dry_run: bool
) -> None:
    """Create sample sheet and parameter file for Taxprofiler analysis for a given case."""
    analysis_api: TaxprofilerAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    try:
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        analysis_api.config_case(
            case_id=case_id, instrument_platform=instrument_platform, dry_run=dry_run
        )

    except (CgError, ValidationError) as error:
        LOG.error(f"Could not create config files for {case_id}: {error}")
        raise click.Abort() from error


@taxprofiler.command("run")
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
    """Run taxprofiler analysis for a case."""
    analysis_api: TaxprofilerAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    command_args: CommandArgs = CommandArgs(
        **{
            "log": analysis_api.get_log_path(
                case_id=case_id,
                pipeline=analysis_api.pipeline,
                log=log,
            ),
            "work_dir": analysis_api.get_workdir_path(case_id=case_id, work_dir=work_dir),
            "resume": not from_start,
            "profile": analysis_api.get_profile(profile=profile),
            "config": analysis_api.get_nextflow_config_path(nextflow_config=config),
            "params_file": analysis_api.get_params_file_path(
                case_id=case_id, params_file=params_file
            ),
            "name": case_id,
            "compute_env": compute_env or analysis_api.compute_env,
            "revision": revision or analysis_api.revision,
            "wait": NfTowerStatus.SUBMITTED,
            "id": nf_tower_id,
        }
    )
    try:
        analysis_api.verify_sample_sheet_exists(case_id=case_id, dry_run=dry_run)
        analysis_api.check_analysis_ongoing(case_id)
        LOG.info(f"Running Taxprofiler analysis for {case_id}")
        analysis_api.run_analysis(
            case_id=case_id, command_args=command_args, use_nextflow=use_nextflow, dry_run=dry_run
        )
        analysis_api.set_statusdb_action(
            case_id=case_id, action=CaseActions.RUNNING, dry_run=dry_run
        )
    except Exception as error:
        LOG.error(f"Could not run analysis: {error}")
        raise click.Abort() from error
    if not dry_run and not use_nextflow:
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)


@taxprofiler.command("start")
@ARGUMENT_CASE_ID
@OPTION_LOG
@OPTION_WORKDIR
@OPTION_PROFILE
@OPTION_CONFIG
@OPTION_PARAMS_FILE
@OPTION_REVISION
@OPTION_COMPUTE_ENV
@OPTION_USE_NEXTFLOW
@OPTION_TOWER_RUN_ID
@DRY_RUN
@click.pass_context
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
    nf_tower_id: str | None,
    dry_run: bool,
) -> None:
    """Start full workflow for case id."""
    LOG.info(f"Starting analysis for {case_id}")

    try:
        context.invoke(resolve_compression, case_id=case_id, dry_run=dry_run)
    except DecompressionNeededError as error:
        LOG.error(error)
        raise click.Abort() from error
    context.invoke(config_case, case_id=case_id, dry_run=dry_run)
    context.invoke(
        run,
        case_id=case_id,
        log=log,
        work_dir=work_dir,
        from_start=True,
        profile=profile,
        nf_tower_id=nf_tower_id,
        config=config,
        params_file=params_file,
        revision=revision,
        compute_env=compute_env,
        use_nextflow=use_nextflow,
        dry_run=dry_run,
    )


@taxprofiler.command("start-available")
@DRY_RUN
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False) -> None:
    """Start full workflow for all cases available for analysis."""

    analysis_api: AnalysisAPI = context.obj.meta_apis[MetaApis.ANALYSIS_API]

    exit_code: int = EXIT_SUCCESS
    for case in analysis_api.get_cases_to_analyze():
        try:
            context.invoke(start, case_id=case.internal_id, dry_run=dry_run)
        except Exception as error:
            LOG.error(error)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
