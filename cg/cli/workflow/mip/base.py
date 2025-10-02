"""Module for common workflow commands."""

import logging

import rich_click as click

from cg.apps.environ import environ_email
from cg.cli.utils import echo_lines
from cg.cli.workflow.commands import link
from cg.cli.workflow.mip.options import (
    ARGUMENT_CASE_ID,
    EMAIL_OPTION,
    OPTION_BWA_MEM,
    OPTION_MIP_DRY_RUN,
    OPTION_PANEL_BED,
    OPTION_SKIP_EVALUATION,
    QOS_OPTION,
    START_AFTER_PROGRAM,
    START_WITH_PROGRAM,
)
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.cli_options import DRY_RUN, LIMIT
from cg.exc import AnalysisNotReadyError, CgError
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case

LOG = logging.getLogger(__name__)


@click.command("config-case")
@DRY_RUN
@OPTION_PANEL_BED
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(context: CGConfig, case_id: str, panel_bed: str, dry_run: bool):
    """Generate a config for the case id."""

    analysis_api: MipAnalysisAPI = context.meta_apis["analysis_api"]
    try:
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        panel_bed: str | None = analysis_api.get_panel_bed(panel_bed=panel_bed)
        config_data: dict = analysis_api.pedigree_config(case_id=case_id, panel_bed=panel_bed)
    except CgError as error:
        LOG.error(error)
        raise click.Abort()
    if dry_run:
        click.echo(config_data)
        return
    analysis_api.write_pedigree_config(data=config_data, case_id=case_id)


@click.command()
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_obj
def panel(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Write aggregated gene panel file exported from Scout."""

    analysis_api: MipAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    bed_lines: list[str] = analysis_api.get_gene_panel(case_id=case_id)
    if dry_run:
        echo_lines(lines=bed_lines)
        return
    analysis_api.write_panel(case_id, bed_lines)


@click.command()
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_obj
def managed_variants(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Write managed variants file exported from Scout."""

    analysis_api: MipAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
    vcf_lines: list[str] = analysis_api.get_managed_variants()
    if dry_run:
        echo_lines(lines=vcf_lines)
        return
    analysis_api.write_managed_variants(case_id=case_id, content=vcf_lines)


@click.command()
@QOS_OPTION
@EMAIL_OPTION
@START_AFTER_PROGRAM
@START_WITH_PROGRAM
@ARGUMENT_CASE_ID
@OPTION_BWA_MEM
@DRY_RUN
@OPTION_MIP_DRY_RUN
@OPTION_SKIP_EVALUATION
@click.pass_obj
def run(
    context: CGConfig,
    case_id: str,
    dry_run: bool = False,
    email: str = None,
    mip_dry_run: bool = False,
    slurm_quality_of_service: str = None,
    skip_evaluation: bool = False,
    start_after: str = None,
    start_with: str = None,
    use_bwa_mem: bool = False,
):
    """Run the analysis for a case."""

    analysis_api: MipAnalysisAPI = context.meta_apis["analysis_api"]

    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
    command_args = dict(
        slurm_quality_of_service=slurm_quality_of_service
        or analysis_api.get_slurm_qos_for_case(case_id),
        email=email or environ_email(),
        dryrun=mip_dry_run,
        start_after=start_after,
        start_with=start_with,
        skip_evaluation=analysis_api.get_skip_evaluation_flag(
            case_id=case_id, skip_evaluation=skip_evaluation
        ),
        use_bwa_mem=use_bwa_mem,
    )

    try:
        analysis_api.check_analysis_ongoing(case_id=case_id)
    except CgError as error:
        LOG.error(error)
        raise click.Abort
    analysis_api.run_analysis(case_id=case_id, dry_run=dry_run, command_args=command_args)

    if dry_run:
        LOG.info("Running in dry-run mode.")
        return

    if mip_dry_run:
        LOG.info("Executed MIP in dry-run mode")
        return

    try:
        analysis_api.on_analysis_started(case_id=case_id)
        LOG.info(f"{analysis_api.workflow} run started!")
    except Exception as error:
        LOG.error(f"Database error, unable to update analysis for case {case_id}: {error}")
        raise click.Abort


@click.command()
@ARGUMENT_CASE_ID
@EMAIL_OPTION
@OPTION_BWA_MEM
@DRY_RUN
@OPTION_MIP_DRY_RUN
@OPTION_PANEL_BED
@OPTION_SKIP_EVALUATION
@QOS_OPTION
@START_AFTER_PROGRAM
@START_WITH_PROGRAM
@click.pass_context
def start(
    context: click.Context,
    case_id: str,
    dry_run: bool,
    email: str,
    mip_dry_run: bool,
    panel_bed: str,
    slurm_quality_of_service: str,
    skip_evaluation: bool,
    start_after: str,
    start_with: str,
    use_bwa_mem: bool,
):
    """Start full analysis workflow for a case."""

    analysis_api: MipAnalysisAPI = context.obj.meta_apis["analysis_api"]

    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
    LOG.info(f"Starting full MIP analysis workflow for case {case_id}")
    analysis_api.prepare_fastq_files(case_id=case_id, dry_run=dry_run)
    context.invoke(link, case_id=case_id, dry_run=dry_run)
    context.invoke(panel, case_id=case_id, dry_run=dry_run)
    context.invoke(managed_variants, case_id=case_id, dry_run=dry_run)
    context.invoke(config_case, case_id=case_id, panel_bed=panel_bed, dry_run=dry_run)
    context.invoke(
        run,
        case_id=case_id,
        slurm_quality_of_service=slurm_quality_of_service,
        email=email,
        start_after=start_after,
        start_with=start_with,
        dry_run=dry_run,
        mip_dry_run=mip_dry_run,
        skip_evaluation=skip_evaluation,
        use_bwa_mem=use_bwa_mem,
    )


@click.command("start-available")
@DRY_RUN
@LIMIT
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False, limit: int | None = None):
    """Start full analysis workflow for all cases ready for analysis."""

    analysis_api: MipAnalysisAPI = context.obj.meta_apis["analysis_api"]

    cases: list[Case] = analysis_api.get_cases_to_analyze(limit=limit)
    LOG.info(f"Starting {len(cases)} available MIP cases")

    exit_code: int = EXIT_SUCCESS
    for case in cases:
        try:
            context.invoke(start, case_id=case.internal_id, dry_run=dry_run)
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
