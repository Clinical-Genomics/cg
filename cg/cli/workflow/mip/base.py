import logging
from typing import List

import click
from cg.apps.environ import environ_email
from cg.cli.workflow.commands import ensure_flowcells_ondisk, link, resolve_compression
from cg.cli.workflow.mip.options import (
    ARGUMENT_CASE_ID,
    EMAIL_OPTION,
    OPTION_DRY,
    OPTION_MIP_DRY_RUN,
    OPTION_PANEL_BED,
    OPTION_SKIP_EVALUATION,
    PRIORITY_OPTION,
    START_AFTER_PROGRAM,
    START_WITH_PROGRAM,
)
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.exc import CgError, DecompressionNeededError, FlowcellsNeededError
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.command("config-case")
@OPTION_DRY
@OPTION_PANEL_BED
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(context: CGConfig, case_id: str, panel_bed: str, dry_run: bool):
    """Generate a config for the case_id"""

    analysis_api: MipAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id)

    panel_bed: str = analysis_api.resolve_panel_bed(panel_bed=panel_bed)
    try:
        config_data: dict = analysis_api.pedigree_config(case_id=case_id, panel_bed=panel_bed)
    except CgError as error:
        LOG.error(error.message)
        raise click.Abort()
    if dry_run:
        click.echo(config_data)
        return
    analysis_api.write_pedigree_config(data=config_data, case_id=case_id)


@click.command()
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_obj
def panel(context: CGConfig, case_id: str, dry_run: bool):
    """Write aggregated gene panel file exported from Scout"""

    analysis_api: MipAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)

    bed_lines: List[str] = analysis_api.panel(case_id=case_id)
    if dry_run:
        for bed_line in bed_lines:
            click.echo(bed_line)
        return
    analysis_api.write_panel(case_id, bed_lines)


@click.command()
@PRIORITY_OPTION
@EMAIL_OPTION
@START_AFTER_PROGRAM
@START_WITH_PROGRAM
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_MIP_DRY_RUN
@OPTION_SKIP_EVALUATION
@click.pass_obj
def run(
    context: CGConfig,
    case_id: str,
    dry_run: bool = False,
    email: str = None,
    mip_dry_run: bool = False,
    priority: str = None,
    skip_evaluation: bool = False,
    start_after: str = None,
    start_with: str = None,
):
    """Run the analysis for a case"""

    analysis_api: MipAnalysisAPI = context.meta_apis["analysis_api"]

    analysis_api.verify_case_id_in_statusdb(case_id)
    command_args = dict(
        priority=priority or analysis_api.get_priority_for_case(case_id),
        email=email or environ_email(),
        dryrun=mip_dry_run,
        start_after=start_after,
        start_with=start_with,
        skip_evaluation=analysis_api.get_skip_evaluation_flag(
            case_id=case_id, skip_evaluation=skip_evaluation
        ),
    )

    analysis_api.check_analysis_ongoing(case_id=case_id)
    analysis_api.run_analysis(case_id=case_id, dry_run=dry_run, command_args=command_args)

    if dry_run:
        LOG.info("Running in dry-run mode.")
        return

    if mip_dry_run:
        LOG.info("Executed MIP in dry-run mode")
        return

    try:
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action="running")
        LOG.info("%s run started!", analysis_api.pipeline)
    except CgError as e:
        LOG.error(e.message)
        raise click.Abort


@click.command()
@ARGUMENT_CASE_ID
@EMAIL_OPTION
@OPTION_DRY
@OPTION_MIP_DRY_RUN
@OPTION_PANEL_BED
@OPTION_SKIP_EVALUATION
@PRIORITY_OPTION
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
    priority: str,
    skip_evaluation: bool,
    start_after: str,
    start_with: str,
):
    """Start full MIP analysis workflow for a case"""

    analysis_api: MipAnalysisAPI = context.obj.meta_apis["analysis_api"]

    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    LOG.info("Starting full MIP analysis workflow for case %s", case_id)
    try:
        context.invoke(ensure_flowcells_ondisk, case_id=case_id)
        context.invoke(resolve_compression, case_id=case_id, dry_run=dry_run)
        context.invoke(link, case_id=case_id, dry_run=dry_run)
        context.invoke(panel, case_id=case_id, dry_run=dry_run)
        context.invoke(config_case, case_id=case_id, panel_bed=panel_bed, dry_run=dry_run)
        context.invoke(
            run,
            case_id=case_id,
            priority=priority,
            email=email,
            start_after=start_after,
            start_with=start_with,
            dry_run=dry_run,
            mip_dry_run=mip_dry_run,
            skip_evaluation=skip_evaluation,
        )
    except (FlowcellsNeededError, DecompressionNeededError) as e:
        LOG.error(e.message)


@click.command("start-available")
@OPTION_DRY
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full MIP analysis workflow for all cases ready for analysis"""

    analysis_api: MipAnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_analyze():
        try:
            context.invoke(start, case_id=case_obj.internal_id, dry_run=dry_run)
        except CgError as error:
            LOG.error(error.message)
            exit_code = EXIT_FAIL
        except Exception as e:
            LOG.error(f"Unspecified error occurred: %s", e)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
