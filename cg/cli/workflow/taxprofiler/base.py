"""CLI support to create config and/or start TAXPROFILER."""

import logging

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, resolve_compression
from cg.cli.workflow.nf_analysis import (
    config_case,
    metrics_deliver,
    report_deliver,
    run,
    start,
    start_available,
    store,
    store_available,
    store_housekeeper,
)
from cg.constants.constants import MetaApis, Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def taxprofiler(context: click.Context) -> None:
    """nf-core/taxprofiler analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = TaxprofilerAnalysisAPI(config=context.obj)


@taxprofiler.command()
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_start(cg_config: CGConfig, case_id: str) -> None:
    """Start a Taxprofiler case. Configures the case if needed."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.TAXPROFILER
    )
    analysis_starter.start(case_id=case_id)


@taxprofiler.command()
@click.pass_obj
def dev_start_available(cg_config: CGConfig) -> None:
    """Starts all available Taxprofiler cases."""
    LOG.info("Starting Taxprofiler workflow for all available cases.")
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.TAXPROFILER
    )
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort


@taxprofiler.command()
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_run(cg_config: CGConfig, case_id: str) -> None:
    """Run a preconfigured Taxprofiler case."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.TAXPROFILER
    )
    analysis_starter.run(case_id=case_id)


taxprofiler.add_command(resolve_compression)
taxprofiler.add_command(config_case)
taxprofiler.add_command(run)
taxprofiler.add_command(start)
taxprofiler.add_command(start_available)
taxprofiler.add_command(metrics_deliver)
taxprofiler.add_command(report_deliver)
taxprofiler.add_command(store_housekeeper)
taxprofiler.add_command(store)
taxprofiler.add_command(store_available)
