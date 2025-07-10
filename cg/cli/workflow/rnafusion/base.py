"""CLI support to create config and/or start RNAFUSION."""

import logging
from typing import cast

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, resolve_compression
from cg.cli.workflow.nf_analysis import (
    OPTION_REVISION,
    OPTION_STUB,
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
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def rnafusion(context: click.Context) -> None:
    """nf-core/rnafusion analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = RnafusionAnalysisAPI(config=context.obj)


rnafusion.add_command(resolve_compression)
rnafusion.add_command(config_case)
rnafusion.add_command(run)
rnafusion.add_command(start)
rnafusion.add_command(start_available)
rnafusion.add_command(metrics_deliver)
rnafusion.add_command(report_deliver)
rnafusion.add_command(store_housekeeper)
rnafusion.add_command(store)
rnafusion.add_command(store_available)


@rnafusion.command()
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_config_case(cg_config: CGConfig, case_id: str):
    """Configure an RNAFUSION case so that it is ready to be run."""
    factory = ConfiguratorFactory(cg_config)
    configurator = cast(NextflowConfigurator, factory.get_configurator(Workflow.RNAFUSION))
    configurator.configure(case_id=case_id)


@rnafusion.command()
@ARGUMENT_CASE_ID
@OPTION_REVISION
@OPTION_STUB
@click.pass_obj
def dev_run(cg_config: CGConfig, case_id: str, stub_run: bool, revision: str | None = None):
    """Run a preconfigured RNAFUSION case."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.RNAFUSION
    )
    analysis_starter.run(case_id=case_id, stub_run=stub_run, revision=revision)


@rnafusion.command()
@ARGUMENT_CASE_ID
@OPTION_REVISION
@OPTION_STUB
@click.pass_obj
def dev_start(
    cg_config: CGConfig, case_id: str, stub_run: bool = False, revision: str | None = None
):
    """Start an RNAFUSION case. Configures the case if needed."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.RNAFUSION
    )
    analysis_starter.start(case_id=case_id, stub_run=stub_run, revision=revision)


@rnafusion.command()
@click.pass_obj
def dev_start_available(cg_config: CGConfig) -> None:
    """Starts all available RNAFUSION cases."""
    LOG.info("Starting RNAFUSION workflow for all available cases.")
    analysis_starter = AnalysisStarterFactory(cg_config).get_analysis_starter_for_workflow(
        Workflow.RNAFUSION
    )
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort
