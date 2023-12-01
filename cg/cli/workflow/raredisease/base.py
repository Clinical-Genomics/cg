"""CLI support to create config and/or start RAREDISEASE."""

import logging

import click

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
    OPTION_FROM_START,
)

from cg.constants.constants import MetaApis
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI

# from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.constants import DRY_RUN, CaseActions, MetaApis
from cg.exc import AnalysisNotReadyError, CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.nf_analysis import NfCommandArgs
from cg.constants.nf_analysis import NfTowerStatus

# from cg.store import Store


LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def raredisease(context: click.Context) -> None:
    """nf-core/raredisease analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = RarediseaseAnalysisAPI(
        config=context.obj,
    )


raredisease.add_command(resolve_compression)


@raredisease.command("run")
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
    """Run raredisease analysis for given CASE ID."""
    analysis_api: RarediseaseAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    command_args: NfCommandArgs = NfCommandArgs(
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
        LOG.info(f"Running RAREDISEASE analysis for {case_id}")
        analysis_api.run_analysis(
            case_id=case_id, command_args=command_args, use_nextflow=use_nextflow, dry_run=dry_run
        )
        analysis_api.set_statusdb_action(
            case_id=case_id, action=CaseActions.RUNNING, dry_run=dry_run
        )
    except FileNotFoundError as error:
        LOG.error(f"Could not resume analysis: {error}")
        raise click.Abort() from error
    except (CgError, ValueError) as error:
        LOG.error(f"Could not run analysis: {error}")
        raise click.Abort() from error
    except Exception as error:
        LOG.error(f"Could not run analysis: {error}")
        raise click.Abort() from error
    if not dry_run:
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)
