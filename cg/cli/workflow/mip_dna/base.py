"""Commands to start MIP rare disease DNA workflow."""

import logging

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import (
    ensure_illumina_runs_on_disk,
    link,
    resolve_compression,
    store,
    store_available,
)
from cg.cli.workflow.mip.base import (
    config_case,
    managed_variants,
    panel,
    run,
    start,
    start_available,
)
from cg.cli.workflow.mip.options import (
    OPTION_BWA_MEM,
    OPTION_PANEL_BED,
    START_AFTER_PROGRAM,
    START_WITH_PROGRAM,
)
from cg.constants import Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
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
    config_case,
    ensure_illumina_runs_on_disk,
    link,
    managed_variants,
    panel,
    resolve_compression,
    run,
    start,
    start_available,
    store,
    store_available,
]:
    mip_dna.add_command(sub_cmd)


@mip_dna.command("dev-run")
@START_AFTER_PROGRAM
@START_WITH_PROGRAM
@OPTION_BWA_MEM
@click.argument("case_id", type=str)
@click.pass_obj
def dev_run(
    cg_config: CGConfig,
    case_id: str,
    use_bwa_mem: bool,
    start_after: str | None,
    start_with: str | None,
):
    """."""
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.MIP_DNA)
    analysis_starter.run(
        case_id=case_id, start_after=start_after, start_with=start_with, use_bwa_mem=use_bwa_mem
    )


@mip_dna.command("dev-start")
@START_AFTER_PROGRAM
@START_WITH_PROGRAM
@OPTION_BWA_MEM
@OPTION_PANEL_BED
@click.argument("case_id", type=str)
@click.pass_obj
def dev_start(
    cg_config: CGConfig,
    case_id: str,
    use_bwa_mem: bool,
    panel_bed: str | None,
    start_after: str | None,
    start_with: str | None,
):
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.MIP_DNA)
    analysis_starter.start(
        case_id=case_id,
        start_after=start_after,
        start_with=start_with,
        panel_bed=panel_bed,
        use_bwa_mem=use_bwa_mem,
    )


@mip_dna.command("dev-start-available")
@click.pass_obj
def dev_start_available(cg_config: CGConfig):
    factory = AnalysisStarterFactory(cg_config)
    analysis_starter: AnalysisStarter = factory.get_analysis_starter_for_workflow(Workflow.MIP_DNA)
    succeeded: bool = analysis_starter.start_available()
    if not succeeded:
        raise click.Abort
