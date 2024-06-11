"""CLI support to create config and/or start Tomte."""

import logging

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import resolve_compression
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
from cg.meta.workflow.tomte import TomteAnalysisAPI

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
