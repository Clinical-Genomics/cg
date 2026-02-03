"""CLI support to create config and/or start BALSAMIC."""

import logging
from typing import cast

import rich_click as click
from pydantic.v1 import ValidationError

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.balsamic.options import OPTION_PANEL_BED, OPTION_WORKFLOW_PROFILE
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, resolve_compression
from cg.cli.workflow.utils import validate_force_store_option
from cg.constants import Workflow
from cg.constants.cli_options import COMMENT, DRY_RUN, FORCE
from cg.exc import CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.configurator.implementations.balsamic import BalsamicConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
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


@balsamic.command("config-case")
@OPTION_PANEL_BED
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(cg_config: CGConfig, case_id: str, panel_bed: str | None):
    """Configure a Balsamic case so that it is ready to be run.

    \b
    Creates the case config file:
        - CASE_ID.json
    """
    factory = ConfiguratorFactory(cg_config)
    configurator = cast(BalsamicConfigurator, factory.get_configurator(Workflow.BALSAMIC))
    configurator.configure(case_id=case_id, panel_bed=panel_bed)


@balsamic.command("run")
@OPTION_WORKFLOW_PROFILE
@ARGUMENT_CASE_ID
@click.pass_obj
def run(cg_config: CGConfig, case_id: str, workflow_profile: click.Path | None):
    """
    Run a preconfigured Balsamic case.

    \b
    Assumes that case config file exist in the case run directory:
        - CASE_ID.json
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.BALSAMIC)
    analysis_starter.run(case_id=case_id, workflow_profile=workflow_profile)


@balsamic.command("start")
@OPTION_PANEL_BED
@OPTION_WORKFLOW_PROFILE
@ARGUMENT_CASE_ID
@click.pass_obj
def start(
    cg_config: CGConfig,
    case_id: str,
    panel_bed: str | None,
    workflow_profile: click.Path | None,
):
    """
    Starts a Balsamic cases.

    \b
    Configures the case and creates the case config file:
        - CASE_ID.json
    and submits the job to slurm.
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.BALSAMIC)
    analysis_starter.start(case_id=case_id, workflow_profile=workflow_profile, panel_bed=panel_bed)


@balsamic.command("start-available")
@click.pass_obj
def start_available(cg_config: CGConfig):
    """
    Starts all available Balsamic cases.

    \b
    Configures the individual case and creates its case config file:
        - CASE_ID.json
    and submits the job to slurm.
    """
    LOG.info("Starting Balsamic workflow for all available cases.")
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter = factory.get_analysis_starter_for_workflow(Workflow.BALSAMIC)
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort
