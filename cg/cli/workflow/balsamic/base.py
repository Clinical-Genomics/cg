"""CLI support to create config and/or start BALSAMIC."""

import logging
import traceback

import rich_click as click
from pydantic.v1 import ValidationError

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.balsamic.options import (
    OPTION_CACHE_VERSION,
    OPTION_GENDER,
    OPTION_GENOME_VERSION,
    OPTION_OBSERVATIONS,
    OPTION_PANEL_BED,
    OPTION_PON_CNN,
    OPTION_QOS,
    OPTION_WORKFLOW_PROFILE,
)
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, link, resolve_compression
from cg.cli.workflow.utils import validate_force_store_option
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.cli_options import COMMENT, DRY_RUN, FORCE, LIMIT
from cg.exc import AnalysisNotReadyError, CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def balsamic(context: click.Context):
    """Cancer analysis workflow"""
    AnalysisAPI.get_help(context)

    config = context.obj
    context.obj.meta_apis["analysis_api"] = BalsamicAnalysisAPI(config=config)


balsamic.add_command(resolve_compression)
balsamic.add_command(link)


@balsamic.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_GENDER
@OPTION_GENOME_VERSION
@OPTION_PANEL_BED
@OPTION_PON_CNN
@OPTION_OBSERVATIONS
@OPTION_CACHE_VERSION
@DRY_RUN
@click.pass_obj
def config_case(
    context: CGConfig,
    case_id: str,
    gender: str,
    genome_version: str,
    panel_bed: str,
    pon_cnn: click.Path,
    observations: list[click.Path],
    cache_version: str,
    dry_run: bool,
):
    """Create config file for BALSAMIC analysis for a given CASE_ID."""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    try:
        LOG.info(f"Creating config file for {case_id}.")
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        analysis_api.config_case(
            case_id=case_id,
            gender=gender,
            genome_version=genome_version,
            panel_bed=panel_bed,
            pon_cnn=pon_cnn,
            observations=observations,
            cache_version=cache_version,
            dry_run=dry_run,
        )
    except CgError as error:
        error_info = f"Error: {type(error).__name__}: {str(error)}\n{traceback.format_exc()}"
        LOG.error(f"Could not create config: {error_info}")
        raise click.Abort()
    except Exception as error:
        error_info = f"Error: {type(error).__name__}: {str(error)}\n{traceback.format_exc()}"
        LOG.error(f"Could not create config: {error_info}")
        raise click.Abort()


@balsamic.command("run")
@ARGUMENT_CASE_ID
@OPTION_WORKFLOW_PROFILE
@DRY_RUN
@OPTION_QOS
@click.pass_obj
def run(
    context: CGConfig,
    case_id: str,
    workflow_profile: click.Path,
    slurm_quality_of_service: str,
    dry_run: bool,
):
    """Run balsamic analysis for given CASE ID"""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    try:
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        analysis_api.verify_case_config_file_exists(case_id=case_id, dry_run=dry_run)
        analysis_api.check_analysis_ongoing(case_id)
        analysis_api.run_analysis(
            case_id=case_id,
            workflow_profile=workflow_profile,
            slurm_quality_of_service=slurm_quality_of_service,
            dry_run=dry_run,
        )
        if dry_run:
            return
        analysis_api.on_analysis_started(case_id)
    except Exception as error:
        error_info = f"Error: {type(error).__name__}: {str(error)}\n{traceback.format_exc()}"
        LOG.error(f"Could not run analysis: {error_info}")
        raise click.Abort()


@balsamic.command("report-deliver")
@ARGUMENT_CASE_ID
@DRY_RUN
@FORCE
@click.pass_obj
def report_deliver(context: CGConfig, case_id: str, dry_run: bool, force: bool):
    """Create a Housekeeper deliverables file for a given case ID."""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    try:
        analysis_api.status_db.verify_case_exists(case_id)
        analysis_api.verify_case_config_file_exists(case_id=case_id, dry_run=dry_run)
        analysis_api.trailblazer_api.verify_latest_analysis_is_completed(
            case_id=case_id, force=force
        )
        analysis_api.report_deliver(case_id=case_id, dry_run=dry_run)
    except CgError as error:
        LOG.error(f"Could not create report file: {error}")
        raise click.Abort()
    except Exception as error:
        LOG.error(f"Could not create report file: {error}")
        raise click.Abort()


@balsamic.command("store-housekeeper")
@ARGUMENT_CASE_ID
@COMMENT
@DRY_RUN
@FORCE
@click.pass_obj
def store_housekeeper(
    context: CGConfig, case_id: str, comment: str | None, dry_run: bool, force: bool
):
    """Store a finished analysis in Housekeeper and StatusDB."""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    status_db: Store = context.status_db

    try:
        analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
        analysis_api.verify_case_config_file_exists(case_id=case_id, dry_run=dry_run)
        analysis_api.verify_deliverables_file_exists(case_id=case_id)
        _, version = analysis_api.create_housekeeper_bundle(
            case_id=case_id, dry_run=dry_run, force=force
        )
        analysis_api.update_analysis_as_completed_statusdb(
            case_id=case_id, hk_version_id=version.id, comment=comment, dry_run=dry_run, force=force
        )
        analysis_api.set_statusdb_action(case_id=case_id, action=None, dry_run=dry_run)
    except ValidationError as error:
        LOG.warning("Deliverables file is malformed")
        raise error
    except CgError as error:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {error}")
        raise click.Abort()
    except Exception as error:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {error}!")
        housekeeper_api.rollback()
        status_db.session.rollback()
        raise click.Abort()


@balsamic.command("start")
@ARGUMENT_CASE_ID
@OPTION_GENDER
@OPTION_GENOME_VERSION
@OPTION_QOS
@DRY_RUN
@OPTION_PANEL_BED
@OPTION_PON_CNN
@OPTION_CACHE_VERSION
@OPTION_OBSERVATIONS
@OPTION_WORKFLOW_PROFILE
@click.pass_context
def start(
    context: click.Context,
    case_id: str,
    gender: str,
    genome_version: str,
    cache_version: str,
    panel_bed: str,
    pon_cnn: str,
    observations: list[click.Path],
    slurm_quality_of_service: str,
    workflow_profile: click.Path,
    dry_run: bool,
):
    """Start full workflow for case ID."""
    analysis_api: BalsamicAnalysisAPI = context.obj.meta_apis["analysis_api"]
    analysis_api.prepare_fastq_files(case_id=case_id, dry_run=dry_run)
    LOG.info(f"Starting analysis for {case_id}")
    context.invoke(link, case_id=case_id, dry_run=dry_run)
    context.invoke(
        config_case,
        case_id=case_id,
        gender=gender,
        genome_version=genome_version,
        cache_version=cache_version,
        panel_bed=panel_bed,
        pon_cnn=pon_cnn,
        observations=observations,
        dry_run=dry_run,
    )
    context.invoke(
        run,
        case_id=case_id,
        workflow_profile=workflow_profile,
        slurm_quality_of_service=slurm_quality_of_service,
        dry_run=dry_run,
    )


@balsamic.command("start-available")
@DRY_RUN
@LIMIT
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False, limit: int | None = None):
    """Start full workflow for all cases ready for analysis"""

    analysis_api: AnalysisAPI = context.obj.meta_apis["analysis_api"]

    cases: list[Case] = analysis_api.get_cases_to_analyze(limit=limit)
    LOG.info(f"Starting {len(cases)} available Balsamic cases")

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


@balsamic.command("store")
@ARGUMENT_CASE_ID
@COMMENT
@DRY_RUN
@FORCE
@click.pass_context
def store(context: click.Context, case_id: str, comment: str | None, dry_run: bool, force: bool):
    """Generate Housekeeper report for CASE ID and store in Housekeeper"""
    LOG.info(f"Storing analysis for {case_id}")
    validate_force_store_option(force=force, comment=comment)
    context.invoke(report_deliver, case_id=case_id, dry_run=dry_run, force=force)
    context.invoke(store_housekeeper, case_id=case_id, comment=comment, force=force)


@balsamic.command("store-available")
@DRY_RUN
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """Store bundles for all finished analyses in Housekeeper"""

    analysis_api: AnalysisAPI = context.obj.meta_apis["analysis_api"]

    was_successful: bool = True
    for case_obj in analysis_api.get_cases_to_store():
        LOG.info(f"Storing deliverables for {case_obj.internal_id}")
        try:
            context.invoke(store, case_id=case_obj.internal_id, dry_run=dry_run)
        except Exception as exception_object:
            LOG.error(f"Error storing {case_obj.internal_id}: {exception_object}")
            was_successful = False
    if not was_successful:
        raise click.Abort()
