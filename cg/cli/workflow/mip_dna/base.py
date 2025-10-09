"""Commands to start MIP rare disease DNA workflow."""

import logging
from typing import cast

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import (
    ensure_illumina_runs_on_disk,
    link,
    resolve_compression,
    store,
    store_available,
)
from cg.cli.workflow.mip.options import (
    ARGUMENT_CASE_ID,
    OPTION_BWA_MEM,
    OPTION_PANEL_BED,
    START_AFTER_PROGRAM,
    START_WITH_PROGRAM,
)
from cg.constants import Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter

LOG = logging.getLogger(__name__)


@click.group(
    "mip-dna",
    invoke_without_command=True,
    context_settings=CLICK_CONTEXT_SETTINGS,
)
@click.pass_context
def mip_dna(
    context: click.Context,
):
    """Rare disease DNA workflow"""
    AnalysisAPI.get_help(context)

    context.obj.meta_apis["analysis_api"] = MipDNAAnalysisAPI(config=context.obj)


for sub_cmd in [
    ensure_illumina_runs_on_disk,
    link,
    resolve_compression,
    store,
    store_available,
]:
    mip_dna.add_command(sub_cmd)


@mip_dna.command("run")
@START_AFTER_PROGRAM
@START_WITH_PROGRAM
@OPTION_BWA_MEM
@ARGUMENT_CASE_ID
@click.pass_obj
def run(
    cg_config: CGConfig,
    case_id: str,
    use_bwa_mem: bool,
    start_after: str | None,
    start_with: str | None,
):
    """
    Run a preconfigured MIP-DNA case.

    \b
    Assumes that the following files exist in the case run directory:
        - pedigree.yaml
        - gene_panels.bed
        - managed_variants.vcf
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.MIP_DNA)
    analysis_starter.run(
        case_id=case_id, start_after=start_after, start_with=start_with, use_bwa_mem=use_bwa_mem
    )


@mip_dna.command("start")
@START_AFTER_PROGRAM
@START_WITH_PROGRAM
@OPTION_BWA_MEM
@OPTION_PANEL_BED
@ARGUMENT_CASE_ID
@click.pass_obj
def start(
    cg_config: CGConfig,
    case_id: str,
    use_bwa_mem: bool,
    panel_bed: str | None,
    start_after: str | None,
    start_with: str | None,
):
    """
    Start a MIP-DNA case.

    \b
    Configures the case and writes the following files:
        - pedigree.yaml
        - gene_panels.bed
        - managed_variants.vcf
    """
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.MIP_DNA)
    analysis_starter.start(
        case_id=case_id,
        start_after=start_after,
        start_with=start_with,
        panel_bed=panel_bed,
        use_bwa_mem=use_bwa_mem,
    )


@mip_dna.command("start-available")
@click.pass_obj
def start_available(cg_config: CGConfig):
    """
    Starts all available MIP-DNA cases.

    \b
    Configures the individual case and writes the following files for each case:
        - pedigree.yaml
        - gene_panels.bed
        - managed_variants.vcf
    """
    LOG.info("Starting MIP-DNA workflow for all available cases.")
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.MIP_DNA)
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort


@mip_dna.command("config-case")
@OPTION_PANEL_BED
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(
    cg_config: CGConfig,
    case_id: str,
    panel_bed: str | None,
):
    """
    Configure a MIP-DNA case so that it is ready to be run.

    \b
    This creates the following files:
        - pedigree.yaml
        - gene_panels.bed
        - managed_variants.vcf
    """
    factory = ConfiguratorFactory(cg_config)
    configurator = cast(MIPDNAConfigurator, factory.get_configurator(Workflow.MIP_DNA))
    configurator.configure(case_id=case_id, panel_bed=panel_bed)
