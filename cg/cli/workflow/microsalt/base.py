"""CLI support to start microSALT."""

import logging
from pathlib import Path
from typing import cast

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, resolve_compression, store, store_available
from cg.constants.constants import Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter

LOG = logging.getLogger(__name__)

ARGUMENT_UNIQUE_IDENTIFIER = click.argument("unique_id", required=True, type=click.STRING)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def microsalt(context: click.Context) -> None:
    """Microbial workflow"""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis["analysis_api"] = MicrosaltAnalysisAPI(config=context.obj)


microsalt.add_command(store)
microsalt.add_command(store_available)
microsalt.add_command(resolve_compression)


@microsalt.command("config-case")
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(cg_config: CGConfig, case_id: str) -> None:
    """Create a config file for a microSALT case."""
    factory = ConfiguratorFactory(cg_config)
    configurator = cast(MicrosaltConfigurator, factory.get_configurator(Workflow.MICROSALT))
    configurator.configure(case_id=case_id)


@microsalt.command("run")
@click.option(
    "-c",
    "--config",
    "config_file_path",
    required=False,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    help="optionally change the config file path",
)
@ARGUMENT_CASE_ID
@click.pass_obj
def run(
    cg_config: CGConfig,
    config_file_path: click.Path,
    case_id: str,
) -> None:
    """Run a preconfigured microSALT case."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.MICROSALT
    )
    analysis_starter.run(case_id=case_id, config_file=config_file_path)


@microsalt.command("start")
@ARGUMENT_CASE_ID
@click.pass_obj
def start(cg_config: CGConfig, case_id: str) -> None:
    """
    Generates config file, links fastq files and runs the microSALT analysis for the provided case.
    """
    LOG.info(f"Starting microSALT workflow for {case_id}")
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.MICROSALT
    )
    analysis_starter.start(case_id)


@microsalt.command("start-available")
@click.pass_obj
def start_available(cg_config: CGConfig) -> None:
    """Starts all available microSALT cases."""
    LOG.info("Starting microSALT workflow for all available cases.")
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.MICROSALT
    )
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort


@microsalt.command("qc")
@ARGUMENT_UNIQUE_IDENTIFIER
@click.pass_context
def qc_microsalt(context: click.Context, unique_id: str) -> None:
    """Perform QC on a microSALT case."""
    analysis_api: MicrosaltAnalysisAPI = context.obj.meta_apis["analysis_api"]
    metrics_file_path: Path = analysis_api.get_metrics_file_path(unique_id)
    try:
        LOG.info(f"Performing QC on case {unique_id}")
        analysis_api.quality_checker.quality_control(metrics_file_path)
    except IndexError:
        LOG.error(f"No existing analysis directories found for case {unique_id}.")
