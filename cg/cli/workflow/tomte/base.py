"""CLI support to create config and/or start Tomte."""

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
    run,
    start,
    start_available,
    store,
    store_available,
    store_housekeeper,
)
from cg.constants.constants import MetaApis, Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.tomte import TomteAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def tomte(context: click.Context) -> None:
    """gms/tomte analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = TomteAnalysisAPI(config=context.obj)


tomte.add_command(resolve_compression)
tomte.add_command(config_case)
tomte.add_command(run)
tomte.add_command(start)
tomte.add_command(start_available)
tomte.add_command(metrics_deliver)
tomte.add_command(report_deliver)
tomte.add_command(store_housekeeper)
tomte.add_command(store)
tomte.add_command(store_available)


@tomte.command("dev-config-case")
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_config_case(cg_config: CGConfig, case_id: str):
    """
    Configure a Tomte case so that it is ready to be run. \b
    Creates the following files in the case run directory:
        - CASE_ID_params_file.yaml
        - CASE_ID_nextflow_config.json
        - CASE_ID_samplesheet.csv
        - gene_panels.bed
    """
    factory = ConfiguratorFactory(cg_config)
    configurator = cast(NextflowConfigurator, factory.get_configurator(Workflow.TOMTE))
    configurator.configure(case_id=case_id)


@tomte.command("dev-run")
@OPTION_REVISION
@OPTION_RESUME
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_run(cg_config: CGConfig, case_id: str, resume: bool, revision: str | None) -> None:
    """
    Run a preconfigured Tomte case. \b
    Assumes that the following files exist in the case run directory:
        - CASE_ID_params_file.yaml
        - CASE_ID_nextflow_config.json
        - CASE_ID_samplesheet.csv
        - gene_panels.bed
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.TOMTE)
    analysis_starter.run(case_id=case_id, resume=resume, revision=revision)


@tomte.command("dev-start")
@OPTION_REVISION
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_start(cg_config: CGConfig, case_id: str, revision: str | None):
    """
    Start a Tomte case. \b
    Configures the case and writes the following files:
        - CASE_ID_params_file.yaml
        - CASE_ID_nextflow_config.json
        - CASE_ID_samplesheet.csv
        - gene_panels.bed
    and submits the job to the Seqera Platform.
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.TOMTE)
    analysis_starter.start(case_id=case_id, revision=revision)


@tomte.command("dev-start-available")
@click.pass_obj
def dev_start_available(cg_config: CGConfig):
    """Starts all available Tomte cases."""
    LOG.info("Starting Tomte workflow for all available cases.")
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.TOMTE)
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort
