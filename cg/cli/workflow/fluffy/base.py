import logging

import click
from cg.cli.workflow.commands import link, resolve_compression, store, store_available
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.exc import CgError, DecompressionNeededError
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.meta.workflow.analysis import AnalysisAPI


OPTION_DRY = click.option(
    "-d", "--dry-run", "dry_run", help="Print command to console without executing", is_flag=True
)
ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_EXTERNAL_REF = click.option("-e", "--external-ref", is_flag=True)

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def fluffy(context: click.Context):
    """
    Fluffy workflow
    """
    AnalysisAPI.get_help(context)
    context.obj.meta_apis["analysis_api"] = FluffyAnalysisAPI(
        config=context.obj,
    )


fluffy.add_command(link)
fluffy.add_command(resolve_compression)
fluffy.add_command(store)
fluffy.add_command(store_available)


@fluffy.command("create-samplesheet")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def create_samplesheet(context: CGConfig, case_id: str, dry_run: bool):
    """
    Write modified samplesheet file to case folder
    """
    analysis_api: FluffyAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
    analysis_api.make_sample_sheet(case_id=case_id, dry_run=dry_run)


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.option("-c", "--config", help="Path to fluffy config in .json format")
@OPTION_EXTERNAL_REF
@click.pass_obj
def run(context: CGConfig, case_id: str, dry_run: bool, config: str, external_ref: bool = False):
    """
    Run Fluffy analysis
    """
    analysis_api: FluffyAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
    analysis_api.run_fluffy(
        case_id=case_id, workflow_config=config, dry_run=dry_run, external_ref=external_ref
    )
    if dry_run:
        return
    # Submit analysis for tracking in Trailblazer
    try:
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)
        LOG.info("Submitted case %s to Trailblazer!", case_id)
    except Exception as error:
        LOG.warning("Unable to submit job file to Trailblazer, raised error: %s", error)

    analysis_api.set_statusdb_action(case_id=case_id, action="running")


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.option("-c", "--config", help="Path to fluffy config in .json format")
@OPTION_EXTERNAL_REF
@click.pass_context
def start(
    context: click.Context,
    case_id: str,
    dry_run: bool,
    external_ref: bool = False,
    config: str = None,
):
    """
    Starts full Fluffy analysis workflow
    """
    LOG.info("Starting full Fluffy workflow for %s", case_id)
    if dry_run:
        LOG.info("Dry run: the executed commands will not produce output!")
    try:
        context.invoke(link, case_id=case_id, dry_run=dry_run)
        context.invoke(create_samplesheet, case_id=case_id, dry_run=dry_run)
        context.invoke(
            run, case_id=case_id, config=config, dry_run=dry_run, external_ref=external_ref
        )
    except DecompressionNeededError as error:
        LOG.error(error)


@fluffy.command("start-available")
@OPTION_DRY
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full analysis workflow for all cases ready for analysis"""

    analysis_api: FluffyAnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_analyze():
        try:
            context.invoke(start, case_id=case_obj.internal_id, dry_run=dry_run)
        except CgError as error:
            LOG.error(error)
            exit_code = EXIT_FAIL
        except Exception as error:
            LOG.error("Unspecified error occurred: %s", error)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
