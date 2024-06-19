"""CLI support to create config and/or start RNAFUSION."""

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
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def rnafusion(context: click.Context) -> None:
    """nf-core/rnafusion analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = RnafusionAnalysisAPI(config=context.obj)


rnafusion.add_command(resolve_compression)
rnafusion.add_command(config_case)
rnafusion.add_command(run)
rnafusion.add_command(start)
rnafusion.add_command(start_available)
rnafusion.add_command(metrics_deliver)
rnafusion.add_command(report_deliver)
rnafusion.add_command(store_housekeeper)
rnafusion.add_command(store)
rnafusion.add_command(store_available)
