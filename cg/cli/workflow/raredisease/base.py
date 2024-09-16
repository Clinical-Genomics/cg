"""CLI support to create config and/or start RAREDISEASE."""

import logging

import click

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
from cg.constants.constants import MetaApis
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig

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
