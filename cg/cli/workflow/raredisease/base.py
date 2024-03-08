"""CLI support to create config and/or start RAREDISEASE."""

import logging

import click
from pydantic.v1 import ValidationError

from cg.cli.workflow.commands import ARGUMENT_CASE_ID, OPTION_DRY, resolve_compression
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
from cg.cli.utils import echo_lines
from cg.constants.constants import DRY_RUN, MetaApis
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.exc import CgError

from cg.constants.constants import DRY_RUN, CaseActions, MetaApis
from cg.exc import CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.nf_analysis import NfCommandArgs
from cg.constants.nf_analysis import NfTowerStatus

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def raredisease(context: click.Context) -> None:
    """NF-core/raredisease analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = RarediseaseAnalysisAPI(config=context.obj)


raredisease.add_command(resolve_compression)


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
        analysis_api.write_config_case(case_id=case_id, dry_run=dry_run)
    except (CgError, ValidationError) as error:
        LOG.error(f"Could not create config files for {case_id}: {error}")
        raise click.Abort() from error


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
                workflow=analysis_api.workflow,
                log=log,
            ),
            "work_dir": analysis_api.get_workdir_path(case_id=case_id, work_dir=work_dir),
            "resume": not from_start,
            "profile": analysis_api.get_profile(profile=profile),
            "config": analysis_api.get_params_file_path(case_id=case_id, params_file=params_file),
            "name": case_id,
            "compute_env": compute_env or analysis_api.get_compute_env(case_id=case_id),
            "revision": revision or analysis_api.revision,
            "wait": NfTowerStatus.SUBMITTED,
            "id": nf_tower_id,
        }
    )
    analysis_api.run_nextflow_analysis(
        case_id=case_id, dry_run=dry_run, use_nextflow=use_nextflow, command_args=command_args
    )


@raredisease.command("panel")
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_obj
def panel(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Write aggregated gene panel file exported from Scout."""

    analysis_api: RarediseaseAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    bed_lines: list[str] = analysis_api.get_gene_panel(case_id=case_id)
    if dry_run:
        echo_lines(lines=bed_lines)
        return
    analysis_api.write_panel(case_id=case_id, content=bed_lines)


@raredisease.command("managed-variants")
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_obj
def managed_variants(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Write managed variants file exported from Scout."""

    analysis_api: RarediseaseAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    vcf_lines: list[str] = analysis_api.get_managed_variants()
    if dry_run:
        echo_lines(lines=vcf_lines)
        return
    analysis_api.write_managed_variants(case_id=case_id, content=vcf_lines)
