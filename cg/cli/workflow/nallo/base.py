"""CLI support to create config and/or start NALLO."""

import logging

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.nf_analysis import (
    config_case,
    metrics_deliver,
    report_deliver,
    run,
    start,
    store,
    store_housekeeper,
)
from cg.constants.constants import MetaApis
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.nallo import NalloAnalysisAPI

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
nallo.add_command(store)
nallo.add_command(store_housekeeper)
nallo.add_command(metrics_deliver)
