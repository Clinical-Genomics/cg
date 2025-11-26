"""CLI support to create config and/or start RAREDISEASE."""

import logging
from typing import cast

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, resolve_compression
from cg.cli.workflow.nf_analysis import (
    OPTION_RESUME,
    OPTION_REVISION,
    config_case,
    metrics_deliver,
    report_deliver,
    store,
    store_available,
    store_housekeeper,
)
from cg.constants.constants import MetaApis, Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def raredisease(context: click.Context) -> None:
    """NF-core/raredisease analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = RarediseaseAnalysisAPI(config=context.obj)


raredisease.add_command(metrics_deliver)
raredisease.add_command(resolve_compression)
raredisease.add_command(report_deliver)
raredisease.add_command(store)
raredisease.add_command(store_available)
raredisease.add_command(store_housekeeper)


@raredisease.command()
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(cg_config: CGConfig, case_id: str):
    """Configure a raredisease case so that it is ready to be run."""
    factory = ConfiguratorFactory(cg_config)
    configurator = cast(NextflowConfigurator, factory.get_configurator(Workflow.RAREDISEASE))
    configurator.configure(case_id=case_id)


@raredisease.command()
@OPTION_REVISION
@OPTION_RESUME
@ARGUMENT_CASE_ID
@click.pass_obj
def run(cg_config: CGConfig, case_id: str, resume: bool, revision: str | None):
    """Run a preconfigured raredisease case."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.RAREDISEASE
    )
    analysis_starter.run(case_id=case_id, resume=resume, revision=revision)


@raredisease.command()
@OPTION_REVISION
@ARGUMENT_CASE_ID
@click.pass_obj
def start(cg_config: CGConfig, case_id: str, revision: str | None):
    """Start a raredisease case. Configures the case if needed."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.RAREDISEASE
    )
    analysis_starter.start(case_id=case_id, revision=revision)


@raredisease.command()
@click.pass_obj
def start_available(cg_config: CGConfig) -> None:
    """Starts all available raredisease cases."""
    LOG.info("Starting raredisease workflow for all available cases.")
    analysis_starter = AnalysisStarterFactory(cg_config).get_analysis_starter_for_workflow(
        Workflow.RAREDISEASE
    )
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort
