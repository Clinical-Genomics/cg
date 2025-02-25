"""CLI support to create config and/or start TAXPROFILER."""

import logging

import rich_click as click

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
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def taxprofiler(context: click.Context) -> None:
    """nf-core/taxprofiler analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = TaxprofilerAnalysisAPI(config=context.obj)


taxprofiler.add_command(resolve_compression)
taxprofiler.add_command(config_case)
taxprofiler.add_command(run)
taxprofiler.add_command(start)
taxprofiler.add_command(start_available)
taxprofiler.add_command(metrics_deliver)
taxprofiler.add_command(report_deliver)
taxprofiler.add_command(store_housekeeper)
taxprofiler.add_command(store)
taxprofiler.add_command(store_available)
