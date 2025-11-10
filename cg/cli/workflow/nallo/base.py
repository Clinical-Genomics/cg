"""CLI support to create config and/or start NALLO."""

import logging
from typing import cast

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS, echo_lines
from cg.cli.workflow.commands import ARGUMENT_CASE_ID
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
from cg.constants.cli_options import DRY_RUN
from cg.constants.constants import MetaApis, Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def nallo(context: click.Context) -> None:
    """GMS/Nallo analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = NalloAnalysisAPI(config=context.obj)


nallo.add_command(config_case)
nallo.add_command(report_deliver)
nallo.add_command(run)
nallo.add_command(start)
nallo.add_command(start_available)
nallo.add_command(store)
nallo.add_command(store_available)
nallo.add_command(store_housekeeper)
nallo.add_command(metrics_deliver)


@nallo.command("panel")
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_obj
def panel(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Write aggregated gene panel file exported from Scout."""

    analysis_api: NalloAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    bed_lines: list[str] = analysis_api.get_gene_panel(case_id=case_id)
    if dry_run:
        echo_lines(lines=bed_lines)
        return
    analysis_api.write_panel_as_tsv(case_id=case_id, content=bed_lines)


@nallo.command("dev-config-case")
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_config_case(cg_config: CGConfig, case_id: str):
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


@nallo.command("dev-run")
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_run(cg_config: CGConfig, case_id: str) -> None:
    """
    Run a preconfigured Nallo case. \b
    Assumes that the following files exist in the case run directory:
        - CASE_ID_params_file.yaml
        - CASE_ID_nextflow_config.json
        - CASE_ID_samplesheet.csv
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.NALLO)
    analysis_starter.run(case_id=case_id)


@nallo.command("dev-start")
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_start(cg_config: CGConfig, case_id: str):
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
    analysis_starter.start(case_id=case_id)


@nallo.command("dev-start-available")
@click.pass_obj
def dev_start_available(cg_config: CGConfig):
    """Starts all available Nallo cases."""
    LOG.info("Starting Nallo workflow for all available cases.")
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.NALLO)
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort
