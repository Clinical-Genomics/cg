"""CLI support to create config and/or start BALSAMIC """

import logging

import click
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.commands import link, resolve_compression
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.exc import CgError, DecompressionNeededError
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from pydantic import ValidationError

LOG = logging.getLogger(__name__)

ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_DRY = click.option(
    "-d", "--dry-run", help="Print command to console without executing", is_flag=True
)
OPTION_PANEL_BED = click.option(
    "--panel-bed",
    required=False,
    help="Panel BED is determined based on capture kit \
    used for library prep. Set this option to override the default",
)
OPTION_ANALYSIS_TYPE = click.option(
    "-a",
    "--analysis-type",
    type=click.Choice(["qc", "paired", "single"]),
    help="Setting this option to qc ensures only QC analysis is performed",
)
OPTION_RUN_ANALYSIS = click.option(
    "-r",
    "--run-analysis",
    is_flag=True,
    default=False,
    help="Execute BALSAMIC in non-dry mode",
)
OPTION_PRIORITY = click.option(
    "-p",
    "--priority",
    type=click.Choice(["low", "normal", "high"]),
    help="Job priority in SLURM. Will be set automatically according to priority in ClinicalDB, \
         this option can be used to override server setting",
)


@click.group(invoke_without_command=True)
@click.pass_context
def balsamic(context: click.Context):
    """Cancer analysis workflow """
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return None
    config = context.obj
    context.obj.meta_apis["analysis_api"] = BalsamicAnalysisAPI(
        config=config,
    )


balsamic.add_command(resolve_compression)
balsamic.add_command(link)


@balsamic.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_PANEL_BED
@OPTION_DRY
@click.pass_obj
def config_case(context: CGConfig, panel_bed: str, case_id: str, dry_run: bool):
    """Create config file for BALSAMIC analysis for a given CASE_ID"""

    analysis_api: BalsamicAnalysisAPI = context.meta_apis["analysis_api"]
    try:
        LOG.info(f"Creating config file for {case_id}.")
        analysis_api.verify_case_id_in_statusdb(case_id=case_id)
        analysis_api.config_case(case_id=case_id, panel_bed=panel_bed, dry_run=dry_run)
    except CgError as e:
        LOG.error(f"Could not create config: {e.message}")
        raise click.Abort()
    except Exception as error:
        LOG.error(f"Could not create config: {error}")
        raise click.Abort()


@balsamic.command("run")
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_PRIORITY
@OPTION_ANALYSIS_TYPE
@OPTION_RUN_ANALYSIS
@click.pass_obj
def run(
    context: CGConfig,
    analysis_type: str,
    run_analysis: bool,
    priority: str,
    case_id: str,
    dry_run: bool,
):
    """Run balsamic analysis for given CASE ID"""
    analysis_api: BalsamicAnalysisAPI = context.meta_apis["analysis_api"]
    try:
        analysis_api.verify_case_id_in_statusdb(case_id)
        analysis_api.verify_case_config_file_exists(case_id=case_id)
        analysis_api.check_analysis_ongoing(case_id)
        analysis_api.run_analysis(
            case_id=case_id,
            analysis_type=analysis_type,
            run_analysis=run_analysis,
            priority=priority,
            dry_run=dry_run,
        )
        if dry_run or not run_analysis:
            return
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action="running")
    except CgError as e:
        LOG.error(f"Could not run analysis: {e.message}")
        raise click.Abort()
    except Exception as e:
        LOG.error(f"Could not run analysis: {e}")
        raise click.Abort()


@balsamic.command("report-deliver")
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_ANALYSIS_TYPE
@click.pass_obj
def report_deliver(context: CGConfig, case_id: str, analysis_type: str, dry_run: bool):
    """Create a housekeeper deliverables file for given CASE ID"""

    analysis_api: BalsamicAnalysisAPI = context.meta_apis["analysis_api"]

    try:
        analysis_api.verify_case_id_in_statusdb(case_id=case_id)
        analysis_api.verify_case_config_file_exists(case_id=case_id)
        analysis_api.verify_analysis_finish_file_exists(case_id=case_id)
        analysis_api.report_deliver(case_id=case_id, analysis_type=analysis_type, dry_run=dry_run)
    except CgError as e:
        LOG.error(f"Could not create report file: {e.message}")
        raise click.Abort()
    except Exception as e:
        LOG.error(f"Could not run analysis: {e}")
        raise click.Abort()


@balsamic.command("store-housekeeper")
@ARGUMENT_CASE_ID
@click.pass_obj
def store_housekeeper(context: CGConfig, case_id: str):
    """Store a finished analysis in Housekeeper and StatusDB."""

    analysis_api: BalsamicAnalysisAPI = context.meta_apis["analysis_api"]
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    status_db: Store = context.status_db

    try:
        analysis_api.verify_case_id_in_statusdb(case_id=case_id)
        analysis_api.verify_case_config_file_exists(case_id=case_id)
        analysis_api.verify_deliverables_file_exists(case_id=case_id)
        analysis_api.upload_bundle_housekeeper(case_id=case_id)
        analysis_api.upload_bundle_statusdb(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action=None)
    except ValidationError as error:
        LOG.warning("Deliverables file is malformed")
        raise error
    except CgError as e:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {e.message}")
        raise click.Abort()
    except Exception as error:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {error}!")
        housekeeper_api.rollback()
        status_db.rollback()
        raise click.Abort()


@balsamic.command("start")
@ARGUMENT_CASE_ID
@OPTION_ANALYSIS_TYPE
@OPTION_PRIORITY
@OPTION_DRY
@OPTION_PANEL_BED
@OPTION_RUN_ANALYSIS
@click.pass_context
def start(
    context: click.Context,
    case_id: str,
    analysis_type: str,
    panel_bed: str,
    priority: str,
    run_analysis: bool,
    dry_run: bool,
):
    """Start full workflow for CASE ID"""
    LOG.info(f"Starting analysis for {case_id}")
    try:
        context.invoke(resolve_compression, case_id=case_id, dry_run=dry_run)
        context.invoke(link, case_id=case_id, dry_run=dry_run)
        context.invoke(config_case, case_id=case_id, panel_bed=panel_bed, dry_run=dry_run)
        context.invoke(
            run,
            case_id=case_id,
            analysis_type=analysis_type,
            priority=priority,
            run_analysis=run_analysis,
            dry_run=dry_run,
        )
    except DecompressionNeededError as e:
        LOG.error(e.message)


@balsamic.command("start-available")
@OPTION_DRY
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full workflow for all cases ready for analysis"""

    analysis_api: BalsamicAnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_analyze():
        try:
            context.invoke(start, case_id=case_obj.internal_id, dry_run=dry_run, run_analysis=True)
        except CgError as error:
            LOG.error(error.message)
            exit_code = EXIT_FAIL
        except Exception as e:
            LOG.error("Unspecified error occurred: %s", e)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


@balsamic.command("store")
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_ANALYSIS_TYPE
@click.pass_context
def store(context: click.Context, case_id: str, analysis_type: str, dry_run: bool):
    """Generate Housekeeper report for CASE ID and store in Housekeeper"""
    LOG.info(f"Storing analysis for {case_id}")
    context.invoke(report_deliver, case_id=case_id, analysis_type=analysis_type, dry_run=dry_run)
    context.invoke(store_housekeeper, case_id=case_id)


@balsamic.command("store-available")
@OPTION_DRY
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """Store bundles for all finished analyses in Housekeeper"""

    analysis_api: BalsamicAnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_store():
        LOG.info("Storing deliverables for %s", case_obj.internal_id)
        try:
            context.invoke(store, case_id=case_obj.internal_id, dry_run=dry_run)
        except Exception as exception_object:
            LOG.error("Error storing %s: %s", case_obj.internal_id, exception_object)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
