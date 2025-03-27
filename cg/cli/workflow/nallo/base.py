"""CLI support to create config and/or start NALLO."""

import logging

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS, echo_lines
from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.constants.cli_options import DRY_RUN
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

from cg.constants.constants import MetaApis
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.models.cg_config import CGConfig

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
