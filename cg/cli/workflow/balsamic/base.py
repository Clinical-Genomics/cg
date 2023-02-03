"""CLI support to create config and/or start BALSAMIC."""

import logging
from typing import List

import click
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.balsamic.options import (
    OPTION_PANEL_BED,
    OPTION_QOS,
    OPTION_RUN_ANALYSIS,
    OPTION_GENOME_VERSION,
    OPTION_PON_CNN,
    OPTION_GENDER,
    OPTION_OBSERVATIONS,
    OPTION_FORCE_NORMAL,
)
from cg.cli.workflow.commands import link, resolve_compression, ARGUMENT_CASE_ID
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.constants import DRY_RUN
from cg.exc import CgError, DecompressionNeededError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from pydantic import ValidationError

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def balsamic(context: click.Context):
    """Cancer analysis workflow"""
    AnalysisAPI.get_help(context)

    config = context.obj
    context.obj.meta_apis["analysis_api"] = BalsamicAnalysisAPI(
        config=config,
    )


balsamic.add_command(resolve_compression)
balsamic.add_command(link)


@balsamic.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_GENDER
@OPTION_GENOME_VERSION
@OPTION_PANEL_BED
@OPTION_PON_CNN
@OPTION_OBSERVATIONS
@OPTION_FORCE_NORMAL
@DRY_RUN
@click.pass_obj
def config_case(
    context: CGConfig,
    case_id: str,
    gender: str,
    genome_version: str,
    panel_bed: str,
    pon_cnn: click.Path,
    observations: List[click.Path],
    force_normal: bool,
    dry_run: bool,
):
    """Create config file for BALSAMIC analysis for a given CASE_ID."""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    try:
        LOG.info(f"Creating config file for {case_id}.")
        analysis_api.verify_case_id_in_statusdb(case_id=case_id)
        analysis_api.config_case(
            case_id=case_id,
            gender=gender,
            genome_version=genome_version,
            panel_bed=panel_bed,
            pon_cnn=pon_cnn,
            observations=observations,
            force_normal=force_normal,
            dry_run=dry_run,
        )
    except CgError as error:
        LOG.error(f"Could not create config: {error}")
        raise click.Abort()
    except Exception as error:
        LOG.error(f"Could not create config: {error}")
        raise click.Abort()


@balsamic.command("run")
@ARGUMENT_CASE_ID
@DRY_RUN
@OPTION_QOS
@OPTION_RUN_ANALYSIS
@click.pass_obj
def run(
    context: CGConfig,
    run_analysis: bool,
    slurm_quality_of_service: str,
    case_id: str,
    dry_run: bool,
):
    """Run balsamic analysis for given CASE ID"""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    try:
        analysis_api.verify_case_id_in_statusdb(case_id)
        analysis_api.verify_case_config_file_exists(case_id=case_id)
        analysis_api.check_analysis_ongoing(case_id)
        analysis_api.run_analysis(
            case_id=case_id,
            run_analysis=run_analysis,
            slurm_quality_of_service=slurm_quality_of_service,
            dry_run=dry_run,
        )
        if dry_run or not run_analysis:
            return
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action="running")
    except CgError as error:
        LOG.error(f"Could not run analysis: {error}")
        raise click.Abort()
    except Exception as error:
        LOG.error(f"Could not run analysis: {error}")
        raise click.Abort()


@balsamic.command("report-deliver")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def report_deliver(context: CGConfig, case_id: str, dry_run: bool):
    """Create a housekeeper deliverables file for given CASE ID"""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]

    try:
        analysis_api.verify_case_id_in_statusdb(case_id=case_id)
        analysis_api.verify_case_config_file_exists(case_id=case_id)
        analysis_api.trailblazer_api.is_latest_analysis_completed(case_id=case_id)
        analysis_api.report_deliver(case_id=case_id, dry_run=dry_run)
    except CgError as error:
        LOG.error(f"Could not create report file: {error}")
        raise click.Abort()
    except Exception as error:
        LOG.error(f"Could not create report file: {error}")
        raise click.Abort()


@balsamic.command("store-housekeeper")
@ARGUMENT_CASE_ID
@click.pass_obj
def store_housekeeper(context: CGConfig, case_id: str):
    """Store a finished analysis in Housekeeper and StatusDB."""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
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
    except CgError as error:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {error}")
        raise click.Abort()
    except Exception as error:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {error}!")
        housekeeper_api.rollback()
        status_db.rollback()
        raise click.Abort()


@balsamic.command("start")
@ARGUMENT_CASE_ID
@OPTION_GENDER
@OPTION_GENOME_VERSION
@OPTION_QOS
@DRY_RUN
@OPTION_PANEL_BED
@OPTION_PON_CNN
@OPTION_RUN_ANALYSIS
@OPTION_FORCE_NORMAL
@click.pass_context
def start(
    context: click.Context,
    case_id: str,
    gender: str,
    genome_version: str,
    panel_bed: str,
    pon_cnn: str,
    slurm_quality_of_service: str,
    run_analysis: bool,
    force_normal: bool,
    dry_run: bool,
):
    """Start full workflow for CASE ID"""
    LOG.info(f"Starting analysis for {case_id}")
    try:
        context.invoke(resolve_compression, case_id=case_id, dry_run=dry_run)
        context.invoke(link, case_id=case_id, dry_run=dry_run)
        context.invoke(
            config_case,
            case_id=case_id,
            gender=gender,
            genome_version=genome_version,
            panel_bed=panel_bed,
            pon_cnn=pon_cnn,
            force_normal=force_normal,
            dry_run=dry_run,
        )
        context.invoke(
            run,
            case_id=case_id,
            slurm_quality_of_service=slurm_quality_of_service,
            run_analysis=run_analysis,
            dry_run=dry_run,
        )
    except DecompressionNeededError as error:
        LOG.error(error)


@balsamic.command("start-available")
@DRY_RUN
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full workflow for all cases ready for analysis"""

    analysis_api: AnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_analyze():
        try:
            context.invoke(start, case_id=case_obj.internal_id, dry_run=dry_run, run_analysis=True)
        except CgError as error:
            LOG.error(error)
            exit_code = EXIT_FAIL
        except Exception as error:
            LOG.error("Unspecified error occurred: %s", error)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


@balsamic.command("store")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_context
def store(context: click.Context, case_id: str, dry_run: bool):
    """Generate Housekeeper report for CASE ID and store in Housekeeper"""
    LOG.info(f"Storing analysis for {case_id}")
    context.invoke(report_deliver, case_id=case_id, dry_run=dry_run)
    context.invoke(store_housekeeper, case_id=case_id)


@balsamic.command("store-available")
@DRY_RUN
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """Store bundles for all finished analyses in Housekeeper"""

    analysis_api: AnalysisAPI = context.obj.meta_apis["analysis_api"]

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
