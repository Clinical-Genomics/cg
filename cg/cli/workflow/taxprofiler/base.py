"""CLI support to create config and/or start TAXPROFILER."""

import logging
from pathlib import Path

import click

from cg.cli.workflow.commands import ARGUMENT_CASE_ID, resolve_compression
from cg.cli.workflow.taxprofiler.options import OPTION_INSTRUMENT_PLATFORM
from cg.constants.constants import MetaApis, DRY_RUN, CaseActions
from cg.constants.sequencing import SequencingPlatform
from cg.exc import CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.exc import CgError, DecompressionNeededError
from cg.cli.workflow.nextflow.options import (
    OPTION_CONFIG,
    OPTION_LOG,
    OPTION_PARAMS_FILE,
    OPTION_PROFILE,
    OPTION_REVISION,
    OPTION_USE_NEXTFLOW,
    OPTION_WORKDIR,
)
from cg.cli.workflow.taxprofiler.options import (
    OPTION_FROM_START,
    OPTION_INSTRUMENT_PLATFORM,
)
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.meta.workflow.nextflow_common import NextflowAnalysisAPI

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
    """Create sample sheet file for Taxprofiler analysis for a given case_id."""
    analysis_api: TaxprofilerAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]

    try:
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        analysis_api.config_case(
            case_id=case_id, instrument_platform=instrument_platform, fasta="", dry_run=dry_run
        )

    except CgError as error:
        LOG.error(f"Could not create sample sheet: {error}")
        LOG.error(f"{case_id} could not be found in StatusDB!")
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
@OPTION_USE_NEXTFLOW
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
    use_nextflow: bool,
    dry_run: bool,
) -> None:
    """Run taxprofiler analysis for given CASE ID."""
    analysis_api: TaxprofilerAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    command_args = {
        "log": NextflowAnalysisAPI.get_log_path(
            case_id=case_id, pipeline=analysis_api.pipeline, root_dir=analysis_api.root_dir, log=log
        ),
        "work-dir": NextflowAnalysisAPI.get_workdir_path(
            case_id=case_id, root_dir=analysis_api.root_dir, work_dir=work_dir
        ),
        "resume": not from_start,
        "profile": analysis_api.get_profile(profile=profile),
        "config": NextflowAnalysisAPI.get_nextflow_config_path(nextflow_config=config),
        "params-file": NextflowAnalysisAPI.get_params_file_path(
            case_id=case_id, root_dir=analysis_api.root_dir, params_file=params_file
        ),
        "name": case_id,
        "revision": revision or analysis_api.revision,
        "wait": "SUBMITTED",
    }

    try:
        analysis_api.verify_case_config_file_exists(case_id=case_id, dry_run=dry_run)
        analysis_api.check_analysis_ongoing(case_id)
        LOG.info(f"Running Taxprofiler analysis for {case_id}")
        analysis_api.run_analysis(
            case_id=case_id, command_args=command_args, use_nextflow=use_nextflow, dry_run=dry_run
        )
        #analysis_api.set_statusdb_action(
        #    case_id=case_id, action=CaseActions.RUNNING, dry_run=dry_run
        #)
    except (CgError, ValueError) as error:
        LOG.error(f"Could not run analysis: {error}")
        raise click.Abort() from error
    except Exception as error:
        LOG.error(f"Could not run analysis: {error}")
        raise click.Abort() from error
