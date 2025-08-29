"""CLI support to create config and/or start RAREDISEASE."""

import logging
from typing import cast

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS, echo_lines
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
from cg.constants.cli_options import DRY_RUN
from cg.constants.constants import MetaApis, Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def raredisease(context: click.Context) -> None:
    """NF-core/raredisease analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = RarediseaseAnalysisAPI(config=context.obj)


raredisease.add_command(metrics_deliver)
raredisease.add_command(resolve_compression)
raredisease.add_command(config_case)
raredisease.add_command(report_deliver)
raredisease.add_command(run)
raredisease.add_command(start)
raredisease.add_command(start_available)
raredisease.add_command(store)
raredisease.add_command(store_available)
raredisease.add_command(store_housekeeper)


@raredisease.command()
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_config_case(cg_config: CGConfig, case_id: str):
    """Configure a raredisease case so that it is ready to be run."""
    factory = ConfiguratorFactory(cg_config)
    configurator = cast(NextflowConfigurator, factory.get_configurator(Workflow.RAREDISEASE))
    configurator.configure(case_id=case_id)


@raredisease.command()
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_run(cg_config: CGConfig, case_id: str):
    """Run a preconfigured raredisease case."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.RAREDISEASE
    )
    analysis_starter.run(case_id=case_id)


@raredisease.command()
@ARGUMENT_CASE_ID
@click.pass_obj
def dev_start(cg_config: CGConfig, case_id: str):
    """Start a raredisease case. Configures the case if needed."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(
        Workflow.RAREDISEASE
    )
    analysis_starter.start(case_id=case_id)


@raredisease.command()
@click.pass_obj
def dev_start_available(cg_config: CGConfig) -> None:
    """Starts all available raredisease cases."""
    LOG.info("Starting raredisease workflow for all available cases.")
    analysis_starter = AnalysisStarterFactory(cg_config).get_analysis_starter_for_workflow(
        Workflow.RAREDISEASE
    )
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort


@raredisease.command("panel")
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_obj
def panel(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Write aggregated gene panel file exported from Scout."""

    analysis_api: RarediseaseAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    bed_lines: list[str] = analysis_api.get_gene_panel(case_id=case_id)
    if dry_run:
        echo_lines(lines=bed_lines)
        return
    analysis_api.write_panel(case_id=case_id, content=bed_lines)


@raredisease.command("managed-variants")
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_obj
def managed_variants(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Write managed variants file exported from Scout."""

    analysis_api: RarediseaseAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    vcf_lines: list[str] = analysis_api.get_managed_variants(case_id=case_id)
    if dry_run:
        echo_lines(lines=vcf_lines)
        return
    analysis_api.write_managed_variants(case_id=case_id, content=vcf_lines)
