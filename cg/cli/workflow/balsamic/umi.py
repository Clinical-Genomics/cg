"""CLI support to create config and/or start BALSAMIC """

import logging
from typing import cast

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.balsamic.base import report_deliver, store, store_available, store_housekeeper
from cg.cli.workflow.balsamic.options import OPTION_PANEL_BED, OPTION_WORKFLOW_PROFILE
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, link, resolve_compression
from cg.constants import Workflow
from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.configurator.implementations.balsamic import BalsamicConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory

LOG = logging.getLogger(__name__)


@click.group(
    "balsamic-umi",
    invoke_without_command=True,
    context_settings=CLICK_CONTEXT_SETTINGS,
)
@click.pass_context
def balsamic_umi(context: click.Context):
    """Cancer analysis workflow"""
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return None
    config = context.obj
    context.obj.meta_apis["analysis_api"] = BalsamicUmiAnalysisAPI(config=config)


balsamic_umi.add_command(resolve_compression)
balsamic_umi.add_command(link)
balsamic_umi.add_command(report_deliver)
balsamic_umi.add_command(store_housekeeper)
balsamic_umi.add_command(store)
balsamic_umi.add_command(store_available)


@balsamic_umi.command("config-case")
@OPTION_PANEL_BED
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(cg_config: CGConfig, case_id: str, panel_bed: str | None):
    """Configure a Balsamic case so that it is ready to be run."""
    factory = ConfiguratorFactory(cg_config)
    configurator = cast(BalsamicConfigurator, factory.get_configurator(Workflow.BALSAMIC_UMI))
    configurator.configure(case_id=case_id, panel_bed=panel_bed)


@balsamic_umi.command("run")
@OPTION_WORKFLOW_PROFILE
@ARGUMENT_CASE_ID
@click.pass_obj
def run(cg_config: CGConfig, case_id: str, workflow_profile: click.Path | None):
    """Run a preconfigured Balsamic case."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.BALSAMIC_UMI
    )
    analysis_starter.run(case_id=case_id, workflow_profile=workflow_profile)


@balsamic_umi.command("start")
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
    """Start a Balsamic case. Configures the case if needed."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.BALSAMIC_UMI
    )
    analysis_starter.start(case_id=case_id, workflow_profile=workflow_profile, panel_bed=panel_bed)


@balsamic_umi.command("start-available")
@click.pass_obj
def start_available(cg_config: CGConfig):
    """Starts all available raredisease cases."""
    LOG.info("Starting Balsamic workflow for all available cases.")
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter = factory.get_analysis_starter_for_workflow(Workflow.BALSAMIC_UMI)
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort
