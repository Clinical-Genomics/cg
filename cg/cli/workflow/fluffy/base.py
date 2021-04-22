import logging

import click
from cg.cli.workflow.commands import link, resolve_compression, store, store_available
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Pipeline
from cg.exc import CgError, DecompressionNeededError
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig

OPTION_DRY = click.option(
    "-d", "--dry-run", "dry_run", help="Print command to console without executing", is_flag=True
)
ARGUMENT_CASE_ID = click.argument("case_id", required=True)

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def fluffy(context: click.Context):
    """
    Fluffy workflow
    """
    if context.invoked_subcommand is None:
        LOG.info(context.get_help())
        return None
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
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    analysis_api.make_samplesheet(case_id=case_id, dry_run=dry_run)


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def run(context: CGConfig, case_id: str, dry_run: bool):
    """
    Run Fluffy analysis
    """
    analysis_api: FluffyAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    analysis_api.run_fluffy(case_id=case_id, dry_run=dry_run)
    if dry_run:
        return
    # Submit analysis for tracking in Trailblazer
    try:
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)
        LOG.info("Submitted case %s to Trailblazer!", case_id)
    except Exception as e:
        LOG.warning("Unable to submit job file to Trailblazer, raised error: %s", e)

    analysis_api.set_statusdb_action(case_id=case_id, action="running")


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def start(context: click.Context, case_id: str, dry_run: bool):
    """
    Starts full Fluffy analysis workflow
    """
    LOG.info("Starting full Fluffy workflow for %s", case_id)
    if dry_run:
        LOG.info("Dry run: the executed commands will not produce output!")
    try:
        context.invoke(link, case_id=case_id, dry_run=dry_run)
        context.invoke(create_samplesheet, case_id=case_id, dry_run=dry_run)
        context.invoke(run, case_id=case_id, dry_run=dry_run)
    except DecompressionNeededError as e:
        LOG.error(e.message)


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
            LOG.error(error.message)
            exit_code = EXIT_FAIL
        except Exception as e:
            LOG.error("Unspecified error occurred: %s", e)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
