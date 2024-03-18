"""CLI support to create config and/or start RAREDISEASE."""

import logging

import click
from pydantic.v1 import ValidationError

from cg.cli.utils import echo_lines
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, OPTION_DRY, resolve_compression
from cg.cli.workflow.nf_analysis import (
    OPTION_COMPUTE_ENV,
    OPTION_CONFIG,
    OPTION_LOG,
    OPTION_PARAMS_FILE,
    OPTION_PROFILE,
    OPTION_REVISION,
    OPTION_USE_NEXTFLOW,
    OPTION_WORKDIR,
    run,
)
from cg.constants.constants import MetaApis
from cg.exc import CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig


LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def raredisease(context: click.Context) -> None:
    """NF-core/raredisease analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = RarediseaseAnalysisAPI(config=context.obj)


raredisease.add_command(resolve_compression)
raredisease.add_command(run)


@raredisease.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def config_case(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Create sample sheet file and params file for a given case."""
    analysis_api: RarediseaseAnalysisAPI = context.meta_apis[MetaApis.ANALYSIS_API]
    LOG.info(f"Creating config files for {case_id}.")
    try:
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        analysis_api.write_config_case(case_id=case_id, dry_run=dry_run)
        analysis_api.write_params_file(case_id=case_id, dry_run=dry_run)
    except (CgError, ValidationError) as error:
        LOG.error(f"Could not create config files for {case_id}: {error}")
        raise click.Abort() from error


@raredisease.command("start")
@ARGUMENT_CASE_ID
@OPTION_COMPUTE_ENV
@OPTION_CONFIG
@OPTION_DRY
@OPTION_LOG
@OPTION_PARAMS_FILE
@OPTION_PROFILE
@OPTION_REVISION
@OPTION_USE_NEXTFLOW
@OPTION_WORKDIR
@click.pass_context
def start(
    context: click.Context,
    case_id: str,
    compute_env: str,
    config: str,
    dry_run: bool,
    log: str,
    params_file: str,
    profile: str,
    revision: str,
    use_nextflow: bool,
    work_dir: str,
) -> None:
    """Start full workflow for CASE ID."""
    LOG.info(f"Starting analysis for {case_id}")

    analysis_api: RarediseaseAnalysisAPI = context.obj.meta_apis["analysis_api"]
    analysis_api.prepare_fastq_files(case_id=case_id, dry_run=dry_run)
    context.invoke(config_case, case_id=case_id, dry_run=dry_run)
    context.invoke(
        run,
        case_id=case_id,
        compute_env=compute_env,
        config=config,
        dry_run=dry_run,
        from_start=True,
        log=log,
        params_file=params_file,
        profile=profile,
        revision=revision,
        use_nextflow=use_nextflow,
        work_dir=work_dir,
    )


@raredisease.command("start-available")
@OPTION_DRY
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
