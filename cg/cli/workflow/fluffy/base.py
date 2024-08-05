import logging

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import link, resolve_compression, store, store_available
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.cli_options import DRY_RUN
from cg.exc import AnalysisNotReadyError, CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig

ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_EXTERNAL_REF = click.option("-e", "--external-ref", is_flag=True)

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def fluffy(context: click.Context):
    """
    Fluffy workflow
    """
    AnalysisAPI.get_help(context)
    context.obj.meta_apis["analysis_api"] = FluffyAnalysisAPI(config=context.obj)


fluffy.add_command(link)
fluffy.add_command(resolve_compression)
fluffy.add_command(store)
fluffy.add_command(store_available)


@fluffy.command("create-samplesheet")
@ARGUMENT_CASE_ID
@DRY_RUN
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
@DRY_RUN
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
        LOG.info(f"Submitted case {case_id} to Trailblazer!")
    except Exception as error:
        LOG.warning(f"Unable to submit job file to Trailblazer, raised error: {error}")

    analysis_api.set_statusdb_action(case_id=case_id, action="running")


@fluffy.command()
@ARGUMENT_CASE_ID
@DRY_RUN
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
    LOG.info(f"Starting full Fluffy workflow for {case_id}")
    if dry_run:
        LOG.info("Dry run: the executed commands will not produce output!")
    analysis_api: FluffyAnalysisAPI = context.obj.meta_apis["analysis_api"]
    analysis_api.prepare_fastq_files(case_id=case_id, dry_run=dry_run)
    context.invoke(link, case_id=case_id, dry_run=dry_run)
    context.invoke(create_samplesheet, case_id=case_id, dry_run=dry_run)
    context.invoke(run, case_id=case_id, config=config, dry_run=dry_run, external_ref=external_ref)


@fluffy.command("start-available")
@DRY_RUN
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full analysis workflow for all cases ready for analysis"""

    analysis_api: FluffyAnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case in analysis_api.get_cases_ready_for_analysis():
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
