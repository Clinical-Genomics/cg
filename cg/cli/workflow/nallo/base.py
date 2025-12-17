"""CLI support to create config and/or start NALLO."""

import logging
from typing import cast

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.cli.workflow.nf_analysis import (
    OPTION_RESUME,
    OPTION_REVISION,
    metrics_deliver,
    report_deliver,
    store,
    store_available,
    store_housekeeper,
)
from cg.constants.constants import MetaApis, Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def nallo(context: click.Context) -> None:
    """GMS/Nallo analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = NalloAnalysisAPI(config=context.obj)


nallo.add_command(report_deliver)
nallo.add_command(store)
nallo.add_command(store_available)
nallo.add_command(store_housekeeper)
nallo.add_command(metrics_deliver)


@nallo.command("config-case")
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(cg_config: CGConfig, case_id: str):
    """
    Configure a Nallo case so that it is ready to be run. \b
    Creates the following files in the case run directory:
        - CASE_ID_params_file.yaml
        - CASE_ID_nextflow_config.json
        - CASE_ID_samplesheet.csv
    """
    factory = ConfiguratorFactory(cg_config)
    configurator = cast(NextflowConfigurator, factory.get_configurator(Workflow.NALLO))
    configurator.configure(case_id=case_id)


@nallo.command("run")
@OPTION_REVISION
@OPTION_RESUME
@ARGUMENT_CASE_ID
@click.pass_obj
def run(cg_config: CGConfig, case_id: str, resume: bool, revision: str | None) -> None:
    """
    Run a preconfigured Nallo case. \b
    Assumes that the following files exist in the case run directory:
        - CASE_ID_params_file.yaml
        - CASE_ID_nextflow_config.json
        - CASE_ID_samplesheet.csv
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.NALLO)
    analysis_starter.run(case_id=case_id, resume=resume, revision=revision)


@nallo.command("start")
@OPTION_REVISION
@ARGUMENT_CASE_ID
@click.pass_obj
def start(cg_config: CGConfig, case_id: str, revision: str | None):
    """
    Start a Nallo case. \b
    Configures the case and writes the following files:
        - CASE_ID_params_file.yaml
        - CASE_ID_nextflow_config.json
        - CASE_ID_samplesheet.csv
    and submits the job to the Seqera Platform.
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.NALLO)
    analysis_starter.start(case_id=case_id, revision=revision)


@nallo.command("start-available")
@click.pass_obj
def start_available(cg_config: CGConfig):
    """Starts all available Nallo cases."""
    LOG.info("Starting Nallo workflow for all available cases.")
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.NALLO)
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort
