"""CLI support to create config and/or start TAXPROFILER."""

import logging
from typing import cast

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, resolve_compression
from cg.cli.workflow.nf_analysis import (
    metrics_deliver,
    report_deliver,
    store,
    store_available,
    store_housekeeper,
)
from cg.constants.constants import MetaApis, Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
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
def start(cg_config: CGConfig, case_id: str) -> None:
    """Start a Taxprofiler case. \n
    Configures the case and writes the following files: \n
        - CASE_ID_params_file.yaml \n
        - CASE_ID_nextflow_config.json \n
        - CASE_ID_samplesheet.csv \n
    and submits the job to the Seqera Platform.
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.TAXPROFILER
    )
    analysis_starter.start(case_id=case_id)


@taxprofiler.command()
@click.pass_obj
def start_available(cg_config: CGConfig) -> None:
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
def run(cg_config: CGConfig, case_id: str) -> None:
    """Run a preconfigured Taxprofiler case. \n
    Assumes that the following files are in the case run directory: \n
        - CASE_ID_params_file.yaml \n
        - CASE_ID_nextflow_config.json \n
        - CASE_ID_samplesheet.csv
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.TAXPROFILER
    )
    analysis_starter.run(case_id=case_id)


@taxprofiler.command()
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(cg_config: CGConfig, case_id: str) -> None:
    """Configure a Taxprofiler case so that it is ready to be run. \n
    Creates the following files in the case run directory:\n
        - CASE_ID_params_file.yaml \n
        - CASE_ID_nextflow_config.json \n
        - CASE_ID_samplesheet.csv
    """
    factory = ConfiguratorFactory(cg_config)
    configurator = cast(NextflowConfigurator, factory.get_configurator(Workflow.TAXPROFILER))
    configurator.configure(case_id=case_id)


taxprofiler.add_command(resolve_compression)
taxprofiler.add_command(metrics_deliver)
taxprofiler.add_command(report_deliver)
taxprofiler.add_command(store_housekeeper)
taxprofiler.add_command(store)
taxprofiler.add_command(store_available)
